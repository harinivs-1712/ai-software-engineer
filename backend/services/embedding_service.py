import concurrent.futures
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from google import genai
from google.genai import types

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Fallback sequence of embedding models supported by Google GenAI
DEFAULT_EMBEDDING_MODELS = [
    "gemini-embedding-001",
    "gemini-embedding-2",
    "models/gemini-embedding-001",
]

# Safe character ceiling to ensure inputs stay under gemini-embedding-001 2,048 token limit (~8,000 chars)
MAX_EMBEDDING_CHARS = 6000


class EmbeddingService:
    """Service to generate vector embeddings for text or code input using Gemini embedding models.

    Encapsulates provider details, task types (RETRIEVAL_DOCUMENT vs CODE_RETRIEVAL_QUERY),
    input truncation protection, and exact model identity reporting.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or GEMINI_API_KEY
        if key:
            self.client = genai.Client(api_key=key)
        else:
            self.client = None

    def _get_client(self) -> genai.Client:
        """Ensure client is initialized with a valid API key."""
        if self.client:
            return self.client

        from config import GEMINI_API_KEY as latest_key

        if latest_key:
            self.client = genai.Client(api_key=latest_key)
            return self.client

        raise RuntimeError("GEMINI_API_KEY is not configured.")

    def generate_embedding_with_meta(
        self,
        text_or_code: str,
        model_name: Optional[str] = None,
        task_type: Optional[str] = None,
        max_chars: int = MAX_EMBEDDING_CHARS,
    ) -> Tuple[List[float], str, int]:
        """Accept text or code as input, apply truncation protection & task type configuration,

        send it to Gemini embedding models, and return (vector, model_used, dimension).

        Args:
            text_or_code: Input text or code snippet to embed.
            model_name: Optional specific model name.
            task_type: Gemini embedding task type ('RETRIEVAL_DOCUMENT', 'CODE_RETRIEVAL_QUERY', 'RETRIEVAL_QUERY').
            max_chars: Maximum character limit per input string.

        Returns:
            Tuple[List[float], str, int]: (embedding_vector, actual_model_used, dimension)

        Raises:
            ValueError: If input is empty or invalid.
            RuntimeError: If embedding generation fails across candidate models.
        """
        if not isinstance(text_or_code, str):
            raise ValueError("Input text_or_code must be a string.")

        content = text_or_code.strip()
        if not content:
            raise ValueError("Input text_or_code cannot be empty.")

        # Truncation policy: protect against token ceiling (>2,048 tokens limit)
        if len(content) > max_chars:
            logger.warning(
                f"Input text/code length ({len(content)} chars) exceeds maximum safety limit ({max_chars} chars). Truncating."
            )
            content = content[:max_chars]

        client = self._get_client()
        models_to_try = [model_name] if model_name else DEFAULT_EMBEDDING_MODELS

        last_error = None
        for model in models_to_try:
            if not model:
                continue
            try:
                if task_type:
                    config = types.EmbedContentConfig(task_type=task_type)
                    response = client.models.embed_content(
                        model=model,
                        contents=content,
                        config=config,
                    )
                else:
                    response = client.models.embed_content(
                        model=model,
                        contents=content,
                    )

                if (
                    response
                    and hasattr(response, "embeddings")
                    and response.embeddings
                ):
                    embedding_obj = response.embeddings[0]
                    if (
                        hasattr(embedding_obj, "values")
                        and embedding_obj.values is not None
                    ):
                        vector = [float(val) for val in embedding_obj.values]
                        return vector, model, len(vector)

                raise RuntimeError(
                    f"Embedding model '{model}' returned empty embedding values."
                )

            except Exception as exc:
                logger.warning(
                    f"Embedding model '{model}' failed: {exc}"
                )
                last_error = exc

        raise RuntimeError(f"Failed to generate embedding: {str(last_error)}")

    def generate_embedding(
        self,
        text_or_code: str,
        model_name: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[float]:
        """Generate vector embedding array for code or text input."""
        vector, _, _ = self.generate_embedding_with_meta(
            text_or_code=text_or_code,
            model_name=model_name,
            task_type=task_type,
        )
        return vector

    def generate_text_embedding(
        self,
        text: str,
        model_name: Optional[str] = None,
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
    ) -> List[float]:
        """Alias method specifically for ordinary text inputs (documentation, comments, queries, READMEs)."""
        return self.generate_embedding(text, model_name=model_name, task_type=task_type)

    def get_embedding(
        self,
        text_or_code: str,
        model_name: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Safe wrapper returning structured dictionary exposing exact model that succeeded."""
        chosen_model = model_name or DEFAULT_EMBEDDING_MODELS[0]
        try:
            vector, actual_model, dim = self.generate_embedding_with_meta(
                text_or_code, model_name=model_name, task_type=task_type
            )
            input_summary = (
                text_or_code
                if len(text_or_code) <= 100
                else text_or_code[:97] + "..."
            )
            return {
                "input": input_summary,
                "content": text_or_code,
                "success": True,
                "model": actual_model,
                "model_used": actual_model,
                "dimension": dim,
                "vector": vector,
                "error": None,
            }
        except Exception as exc:
            input_str = str(text_or_code)
            input_summary = (
                input_str
                if len(input_str) <= 100
                else input_str[:97] + "..."
            )
            return {
                "input": input_summary,
                "content": input_str,
                "success": False,
                "model": chosen_model,
                "model_used": None,
                "dimension": 0,
                "vector": [],
                "error": str(exc),
            }

    def generate_file_embedding(
        self,
        file_path: str,
        content: Optional[str] = None,
        db: Any = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        model_name: Optional[str] = None,
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
    ) -> Dict[str, Any]:
        """Convert a project file or code file into an embedding vector with exact model metadata."""
        chosen_model = model_name or DEFAULT_EMBEDDING_MODELS[0]
        if not isinstance(file_path, str) or not file_path.strip():
            return {
                "input": file_path,
                "path": file_path,
                "content": "",
                "success": False,
                "model": chosen_model,
                "model_used": None,
                "dimension": 0,
                "vector": [],
                "error": "File path must be a non-empty string.",
            }

        extracted_code = content

        if extracted_code is None and db is not None and user_id is not None and project_id is not None:
            try:
                from services.file_system_service import read_project_file
                read_res = read_project_file(
                    db=db,
                    user_id=user_id,
                    project_id=project_id,
                    path=file_path,
                )
                if read_res.get("success"):
                    extracted_code = read_res.get("content", "")
                else:
                    return {
                        "input": file_path,
                        "path": file_path,
                        "content": "",
                        "success": False,
                        "model": chosen_model,
                        "model_used": None,
                        "dimension": 0,
                        "vector": [],
                        "error": read_res.get("error", "Failed to read project file from database."),
                    }
            except Exception as read_err:
                return {
                    "input": file_path,
                    "path": file_path,
                    "content": "",
                    "success": False,
                    "model": chosen_model,
                    "model_used": None,
                    "dimension": 0,
                    "vector": [],
                    "error": f"Error reading project file: {str(read_err)}",
                }

        if extracted_code is None:
            p = Path(file_path)
            if p.is_file():
                try:
                    extracted_code = p.read_text(encoding="utf-8")
                except Exception as file_read_err:
                    return {
                        "input": file_path,
                        "path": file_path,
                        "content": "",
                        "success": False,
                        "model": chosen_model,
                        "model_used": None,
                        "dimension": 0,
                        "vector": [],
                        "error": f"Failed to read disk file '{file_path}': {str(file_read_err)}",
                    }

        if extracted_code is None or not extracted_code.strip():
            return {
                "input": file_path,
                "path": file_path,
                "content": "",
                "success": False,
                "model": chosen_model,
                "model_used": None,
                "dimension": 0,
                "vector": [],
                "error": f"File content for '{file_path}' is empty or could not be loaded.",
            }

        try:
            vector, actual_model, dim = self.generate_embedding_with_meta(
                extracted_code, model_name=model_name, task_type=task_type
            )
            return {
                "input": file_path,
                "path": file_path,
                "content": extracted_code,
                "success": True,
                "model": actual_model,
                "model_used": actual_model,
                "dimension": dim,
                "vector": vector,
                "error": None,
            }
        except Exception as exc:
            return {
                "input": file_path,
                "path": file_path,
                "content": extracted_code,
                "success": False,
                "model": chosen_model,
                "model_used": None,
                "dimension": 0,
                "vector": [],
                "error": str(exc),
            }


class TemporaryEmbeddingPipeline:
    """In-memory temporary embedding storage pipeline.

    Multi-tenant Scoped Architecture:
        Self-contained dict scoped by (user_id, project_id) composite keys to prevent data leakage across projects.
    """

    def __init__(self, service: Optional[EmbeddingService] = None):
        self.service = service or get_embedding_service()
        # Storage dictionary: key = "user_id:project_id", value = {chunk_id: chunk_record}
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def _get_scope_key(self, user_id: Optional[int] = None, project_id: Optional[int] = None) -> str:
        u_str = str(user_id) if user_id is not None else "global"
        p_str = str(project_id) if project_id is not None else "global"
        return f"{u_str}:{p_str}"

    def store_embedding(
        self,
        identifier: str,
        text_or_code: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
    ) -> Dict[str, Any]:
        """Generate embedding for text/code and store temporarily in tenant-scoped memory."""
        vector, model_used, dim = self.service.generate_embedding_with_meta(
            text_or_code, task_type=task_type
        )
        scope = self._get_scope_key(user_id, project_id)

        meta = dict(metadata or {})
        meta["model_used"] = model_used

        entry = {
            "chunk_id": identifier,
            "file": meta.get("file", identifier),
            "symbol": meta.get("symbol", identifier),
            "type": meta.get("type", "text"),
            "model": model_used,
            "model_used": model_used,
            "embedding": vector,
            "content": text_or_code,
            "dimension": dim,
            "metadata": meta,
        }

        if scope not in self._store:
            self._store[scope] = {}
        self._store[scope][identifier] = entry
        return entry

    def store_chunk(
        self,
        chunk: Dict[str, Any],
        model_name: Optional[str] = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
    ) -> Dict[str, Any]:
        """Generate vector embedding for a single code chunk and store in tenant memory."""
        chunk_id = chunk.get("chunk_id") or "unknown_chunk"
        content = chunk.get("content", "")
        metadata = dict(chunk.get("metadata", {}))

        vector, model_used, dim = self.service.generate_embedding_with_meta(
            content, model_name=model_name, task_type=task_type
        )

        metadata["model_used"] = model_used

        entry = {
            "chunk_id": chunk_id,
            "file": metadata.get("file") or chunk.get("file", "unknown"),
            "symbol": metadata.get("symbol", ""),
            "type": metadata.get("type", "chunk"),
            "start_line": metadata.get("start_line", 1),
            "end_line": metadata.get("end_line", 1),
            "language": metadata.get("language", "python"),
            "model": model_used,
            "model_used": model_used,
            "embedding": vector,
            "dimension": dim,
            "content": content,
            "metadata": metadata,
        }

        scope = self._get_scope_key(user_id, project_id)
        if scope not in self._store:
            self._store[scope] = {}
        self._store[scope][chunk_id] = entry
        print(
            "[EMBEDDING TRACE] Vector stored: "
            f"chunk_id={chunk_id!r}, model={model_used!r}, dimension={dim}, "
            f"task_type={task_type!r}, scope={scope!r}, "
            f"vector_preview={[round(value, 5) for value in vector[:5]]}",
            flush=True,
        )
        return entry

    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        model_name: Optional[str] = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
        max_workers: int = 5,
    ) -> List[Dict[str, Any]]:
        """Batch store vector embeddings concurrently using parallel worker pool."""
        if not chunks:
            return []

        print(
            "[EMBEDDING TRACE] Embedding "
            f"{len(chunks)} chunk(s) with task_type={task_type!r}, "
            f"scope={self._get_scope_key(user_id, project_id)!r}.",
            flush=True,
        )

        # Process parallel worker pool to speed up chunk indexing
        results = [None] * len(chunks)

        def _process_item(index: int, item: Dict[str, Any]):
            try:
                res = self.store_chunk(
                    chunk=item,
                    model_name=model_name,
                    user_id=user_id,
                    project_id=project_id,
                    task_type=task_type,
                )
                results[index] = res
            except Exception as err:
                logger.error(f"Failed to embed chunk '{item.get('chunk_id')}': {err}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_process_item, i, c) for i, c in enumerate(chunks)]
            concurrent.futures.wait(futures)

        stored = [r for r in results if r is not None]
        print(
            f"[EMBEDDING TRACE] Embedding complete: {len(stored)}/{len(chunks)} vector(s) stored.\n",
            flush=True,
        )
        return stored

    def store_file(
        self,
        file_path: str,
        content: Optional[str] = None,
        db: Any = None,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Extract file content, chunk it, and store chunk vector embeddings."""
        extracted_content = content
        if extracted_content is None and db is not None and user_id is not None and project_id is not None:
            from services.file_system_service import read_project_file
            read_res = read_project_file(db=db, user_id=user_id, project_id=project_id, path=file_path)
            if read_res.get("success"):
                extracted_content = read_res.get("content", "")

        if extracted_content is None:
            p = Path(file_path)
            if p.is_file():
                extracted_content = p.read_text(encoding="utf-8")

        if extracted_content and extracted_content.strip():
            from services.chunking_service import chunk_file
            chunks = chunk_file(file_path, extracted_content)
            if chunks:
                stored = self.store_chunks(chunks, user_id=user_id, project_id=project_id)
                return stored[0]

        res = self.service.generate_file_embedding(
            file_path=file_path, content=content, db=db, user_id=user_id, project_id=project_id
        )
        if not res.get("success"):
            raise RuntimeError(res.get("error", f"Failed to generate embedding for '{file_path}'."))

        scope = self._get_scope_key(user_id, project_id)
        entry = {
            "chunk_id": f"{file_path}:file:full",
            "file": file_path,
            "symbol": Path(file_path).stem,
            "type": "file",
            "model": res.get("model_used", "gemini-embedding-001"),
            "model_used": res.get("model_used", "gemini-embedding-001"),
            "embedding": res["vector"],
            "content": res.get("content", ""),
            "dimension": res["dimension"],
            "metadata": {"file": file_path, "type": "file", "symbol": Path(file_path).stem, "model_used": res.get("model_used")},
        }

        if scope not in self._store:
            self._store[scope] = {}
        self._store[scope][file_path] = entry
        return entry

    def get(self, identifier: str, user_id: Optional[int] = None, project_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve stored temporary chunk embedding record for specified tenant."""
        scope = self._get_scope_key(user_id, project_id)
        if scope in self._store:
            return self._store[scope].get(identifier)
        # Fallback search across all scopes if global identifier requested
        for tenant_store in self._store.values():
            if identifier in tenant_store:
                return tenant_store[identifier]
        return None

    def list_all(self, user_id: Optional[int] = None, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return all temporary in-memory chunk vectors for tenant scope."""
        if user_id is not None or project_id is not None:
            scope = self._get_scope_key(user_id, project_id)
            tenant_store = self._store.get(scope, {})
            return [dict(item) for item in tenant_store.values()]

        # Return all stored vectors across all tenant scopes
        all_entries = []
        for tenant_store in self._store.values():
            all_entries.extend([dict(item) for item in tenant_store.values()])
        return all_entries

    def clear(self, user_id: Optional[int] = None, project_id: Optional[int] = None) -> None:
        """Clear temporary in-memory store for a specific user & project tenant or globally."""
        if user_id is not None or project_id is not None:
            scope = self._get_scope_key(user_id, project_id)
            if scope in self._store:
                self._store[scope].clear()
        else:
            self._store.clear()


# Singleton service instances and module-level helpers
_embedding_service_instance: Optional[EmbeddingService] = None
_temporary_pipeline_instance: Optional[TemporaryEmbeddingPipeline] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance


def get_temporary_pipeline() -> TemporaryEmbeddingPipeline:
    global _temporary_pipeline_instance
    if _temporary_pipeline_instance is None:
        _temporary_pipeline_instance = TemporaryEmbeddingPipeline(
            service=get_embedding_service()
        )
    return _temporary_pipeline_instance


def generate_embedding(
    text_or_code: str,
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
) -> List[float]:
    """Reusable, provider-agnostic interface to generate an embedding vector."""
    service = get_embedding_service()
    return service.generate_embedding(text_or_code, model_name=model_name, task_type=task_type)


def generate_text_embedding(
    text: str,
    model_name: Optional[str] = None,
    task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
) -> List[float]:
    """Generate vector embedding for general text."""
    service = get_embedding_service()
    return service.generate_text_embedding(text, model_name=model_name, task_type=task_type)


def get_embedding(
    text_or_code: str,
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Module-level function returning structured embedding result dict with exact model identity."""
    service = get_embedding_service()
    return service.get_embedding(text_or_code, model_name=model_name, task_type=task_type)


def generate_file_embedding(
    file_path: str,
    content: Optional[str] = None,
    db: Any = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    model_name: Optional[str] = None,
    task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
) -> Dict[str, Any]:
    """Module-level function to convert a project file into an embedding based on its code content."""
    service = get_embedding_service()
    return service.generate_file_embedding(
        file_path=file_path,
        content=content,
        db=db,
        user_id=user_id,
        project_id=project_id,
        model_name=model_name,
        task_type=task_type,
    )


def store_temporary_chunk(
    chunk: Dict[str, Any],
    model_name: Optional[str] = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
) -> Dict[str, Any]:
    """Store vector embedding for a single code chunk in temporary memory."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_chunk(chunk, model_name=model_name, user_id=user_id, project_id=project_id, task_type=task_type)


def store_temporary_chunks(
    chunks: List[Dict[str, Any]],
    model_name: Optional[str] = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
) -> List[Dict[str, Any]]:
    """Store vector embeddings for a list of code chunks in temporary memory."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_chunks(chunks, model_name=model_name, user_id=user_id, project_id=project_id, task_type=task_type)


def store_temporary_embedding(
    identifier: str,
    text_or_code: str,
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
) -> Dict[str, Any]:
    """Store generated vector temporarily in memory with content metadata."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_embedding(identifier, text_or_code, metadata=metadata, user_id=user_id, project_id=project_id, task_type=task_type)


def store_temporary_file(
    file_path: str,
    content: Optional[str] = None,
    db: Any = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Store file embedding temporarily in memory with file content."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_file(
        file_path=file_path,
        content=content,
        db=db,
        user_id=user_id,
        project_id=project_id,
    )


def list_temporary_embeddings(user_id: Optional[int] = None, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """List all vectors currently stored in temporary memory for tenant scope."""
    pipeline = get_temporary_pipeline()
    return pipeline.list_all(user_id=user_id, project_id=project_id)


def clear_temporary_embeddings(user_id: Optional[int] = None, project_id: Optional[int] = None) -> None:
    """Clear in-memory temporary vector store for tenant scope."""
    pipeline = get_temporary_pipeline()
    pipeline.clear(user_id=user_id, project_id=project_id)
