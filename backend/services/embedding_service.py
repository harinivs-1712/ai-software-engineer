import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from google import genai

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Fallback sequence of embedding models supported by Google GenAI
DEFAULT_EMBEDDING_MODELS = [
    "gemini-embedding-001",
    "gemini-embedding-2",
    "models/gemini-embedding-001",
]


class EmbeddingService:
    """Service to generate vector embeddings for text or code input using Gemini embedding models.

    Encapsulates provider details and exposes a clean, provider-agnostic interface.
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

    def generate_embedding(
        self,
        text_or_code: str,
        model_name: Optional[str] = None,
    ) -> List[float]:
        """Accept text (documentation, project descriptions, README, user queries) or code as input,

        send it to the embedding model, and return the vector list.

        Reusability Guarantee:
        Single entry point regardless of whether input comes from:
            File -> Code -> Documentation -> User Query

        Args:
            text_or_code: Input text or code snippet to embed.
            model_name: Optional specific model name.

        Returns:
            List[float]: The generated embedding vector representation.

        Raises:
            ValueError: If input is empty or invalid.
            RuntimeError: If embedding generation fails across candidate models.
        """
        if not isinstance(text_or_code, str):
            raise ValueError("Input text_or_code must be a string.")

        content = text_or_code.strip()
        if not content:
            raise ValueError("Input text_or_code cannot be empty.")

        client = self._get_client()

        models_to_try = [model_name] if model_name else DEFAULT_EMBEDDING_MODELS

        last_error = None
        for model in models_to_try:
            if not model:
                continue
            try:
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
                        return [float(val) for val in embedding_obj.values]

                raise RuntimeError(
                    f"Embedding model '{model}' returned empty embedding values."
                )

            except Exception as exc:
                logger.warning(
                    f"Embedding model '{model}' failed: {exc}"
                )
                last_error = exc

        raise RuntimeError(f"Failed to generate embedding: {str(last_error)}")

    def generate_text_embedding(
        self,
        text: str,
        model_name: Optional[str] = None,
    ) -> List[float]:
        """Alias method specifically for ordinary text inputs (documentation, comments, queries, READMEs)."""
        return self.generate_embedding(text, model_name=model_name)

    def get_embedding(
        self,
        text_or_code: str,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Safe wrapper returning structured dictionary exposing all verification properties:

        - input: processed input string snippet
        - success: bool indicating successful processing
        - model: embedding model used
        - dimension: integer N (e.g. 3072)
        - vector: float vector array
        - error: None or error string
        """
        chosen_model = model_name or DEFAULT_EMBEDDING_MODELS[0]
        try:
            vector = self.generate_embedding(
                text_or_code, model_name=model_name
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
                "model": chosen_model,
                "dimension": len(vector),
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
    ) -> Dict[str, Any]:
        """Convert a project file or code file into an embedding vector based on actual code content.

        Flow:
            file_path -> Read file / Extract content -> Embedding Model -> Vector
        """
        chosen_model = model_name or DEFAULT_EMBEDDING_MODELS[0]
        if not isinstance(file_path, str) or not file_path.strip():
            return {
                "input": file_path,
                "path": file_path,
                "content": "",
                "success": False,
                "model": chosen_model,
                "dimension": 0,
                "vector": [],
                "error": "File path must be a non-empty string.",
            }

        extracted_code = content

        # Option A: Read from Database project storage if db context provided
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
                    "dimension": 0,
                    "vector": [],
                    "error": f"Error reading project file: {str(read_err)}",
                }

        # Option B: Read from local disk path if file exists
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
                "dimension": 0,
                "vector": [],
                "error": f"File content for '{file_path}' is empty or could not be loaded. (Filename alone is not embedded)",
            }

        # Generate vector representation of the file's code/content
        try:
            vector = self.generate_embedding(extracted_code, model_name=model_name)
            return {
                "input": file_path,
                "path": file_path,
                "content": extracted_code,
                "success": True,
                "model": chosen_model,
                "dimension": len(vector),
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
                "dimension": 0,
                "vector": [],
                "error": str(exc),
            }


class TemporaryEmbeddingPipeline:
    """In-memory temporary embedding storage pipeline.

    Stores generated vectors per chunk in memory in the format:
    {
        "chunk_id": "backend/auth.py:function:authenticate_user",
        "file": "backend/auth.py",
        "symbol": "authenticate_user",
        "type": "function",
        "start_line": 25,
        "end_line": 48,
        "embedding": [0.13, -0.82, 0.41, ...],
        "content": "..."
    }

    Does NOT use a persistent vector database yet.
    """

    def __init__(self, service: Optional[EmbeddingService] = None):
        self.service = service or get_embedding_service()
        self._store: Dict[str, Dict[str, Any]] = {}

    def store_embedding(
        self,
        identifier: str,
        text_or_code: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate embedding for text/code and store temporarily in memory."""
        vector = self.service.generate_embedding(text_or_code)
        entry = {
            "chunk_id": identifier,
            "file": (metadata or {}).get("file", identifier),
            "symbol": (metadata or {}).get("symbol", identifier),
            "type": (metadata or {}).get("type", "text"),
            "embedding": vector,
            "content": text_or_code,
            "dimension": len(vector),
            "metadata": metadata or {},
        }
        self._store[identifier] = entry
        return entry

    def store_chunk(
        self,
        chunk: Dict[str, Any],
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate vector embedding for a single code chunk and store in memory (Requirement 10).

        Flow:
            File -> Chunking -> Code Chunk + Metadata -> Embedding -> Vector per Chunk
        """
        chunk_id = chunk.get("chunk_id") or "unknown_chunk"
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})

        vector = self.service.generate_embedding(content, model_name=model_name)

        entry = {
            "chunk_id": chunk_id,
            "file": metadata.get("file") or chunk.get("file", "unknown"),
            "symbol": metadata.get("symbol", ""),
            "type": metadata.get("type", "chunk"),
            "start_line": metadata.get("start_line", 1),
            "end_line": metadata.get("end_line", 1),
            "language": metadata.get("language", "python"),
            "embedding": vector,
            "dimension": len(vector),
            "content": content,
            "metadata": metadata,
        }
        self._store[chunk_id] = entry
        return entry

    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        model_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Batch store vector embeddings for a list of code chunks."""
        results = []
        for c in chunks:
            res = self.store_chunk(c, model_name=model_name)
            results.append(res)
        return results

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
                stored = self.store_chunks(chunks)
                return stored[0]

        # Fallback to whole file embedding if chunking returns nothing
        res = self.service.generate_file_embedding(
            file_path=file_path, content=content, db=db, user_id=user_id, project_id=project_id
        )
        if not res.get("success"):
            raise RuntimeError(res.get("error", f"Failed to generate embedding for '{file_path}'."))

        entry = {
            "chunk_id": f"{file_path}:file:full",
            "file": file_path,
            "symbol": Path(file_path).stem,
            "type": "file",
            "embedding": res["vector"],
            "content": res.get("content", ""),
            "dimension": res["dimension"],
            "metadata": {"file": file_path, "type": "file", "symbol": Path(file_path).stem},
        }
        self._store[file_path] = entry
        return entry

    def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored temporary chunk embedding record."""
        return self._store.get(identifier)

    def list_all(self) -> List[Dict[str, Any]]:
        """Return all temporary in-memory chunk vectors."""
        return [dict(item) for item in self._store.values()]

    def clear(self) -> None:
        """Clear temporary in-memory store."""
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
) -> List[float]:
    """Reusable, provider-agnostic interface to generate an embedding vector."""
    service = get_embedding_service()
    return service.generate_embedding(text_or_code, model_name=model_name)


def generate_text_embedding(
    text: str,
    model_name: Optional[str] = None,
) -> List[float]:
    """Generate vector embedding for general text (documentation, comments, user queries, READMEs)."""
    service = get_embedding_service()
    return service.generate_text_embedding(text, model_name=model_name)


def get_embedding(
    text_or_code: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Module-level function returning structured embedding result dict for property verification."""
    service = get_embedding_service()
    return service.get_embedding(text_or_code, model_name=model_name)


def generate_file_embedding(
    file_path: str,
    content: Optional[str] = None,
    db: Any = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    model_name: Optional[str] = None,
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
    )


def store_temporary_chunk(
    chunk: Dict[str, Any],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Store vector embedding for a single code chunk in temporary memory."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_chunk(chunk, model_name=model_name)


def store_temporary_chunks(
    chunks: List[Dict[str, Any]],
    model_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Store vector embeddings for a list of code chunks in temporary memory."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_chunks(chunks, model_name=model_name)


def store_temporary_embedding(
    identifier: str,
    text_or_code: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Store generated vector temporarily in memory with content metadata."""
    pipeline = get_temporary_pipeline()
    return pipeline.store_embedding(identifier, text_or_code, metadata=metadata)


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


def list_temporary_embeddings() -> List[Dict[str, Any]]:
    """List all vectors currently stored in temporary memory with file and content metadata."""
    pipeline = get_temporary_pipeline()
    return pipeline.list_all()


def clear_temporary_embeddings() -> None:
    """Clear in-memory temporary vector store."""
    pipeline = get_temporary_pipeline()
    pipeline.clear()
