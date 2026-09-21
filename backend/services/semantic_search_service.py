import logging
from typing import Any, Dict, List, Optional

from services.chunking_service import chunk_file, chunk_project_files
from services.embedding_service import (
    clear_temporary_embeddings,
    generate_embedding,
    get_temporary_pipeline,
    list_temporary_embeddings,
    store_temporary_chunks,
)
from services.similarity_service import cosine_similarity, find_most_similar

logger = logging.getLogger(__name__)


def embed_user_query(
    query: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Embed the user search query into a vector representation using the exact same

    embedding model used for code chunks.

    Flow:
        query -> embedding model -> query vector
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("User query must be a non-empty string.")

    query_str = query.strip()
    vector = generate_embedding(query_str, model_name=model_name)

    return {
        "query": query_str,
        "vector": vector,
        "dimension": len(vector),
        "success": True,
    }


def index_project_files_to_temporary_store(
    db: Any,
    user_id: int,
    project_id: int,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Chunk files stored in ProjectFile DB model and store vector embeddings per chunk (Requirement 10).

    Flow:
        ProjectFile
            ↓
        Chunking Service
            ↓
        Code Chunks + Metadata
            ↓
        Embedding Service (Vector per chunk)
            ↓
        Temporary embedding store
    """
    from services.file_system_service import get_user_project_files

    db_files = get_user_project_files(
        db=db, user_id=user_id, project_id=project_id
    )
    indexed_chunk_count = 0
    file_list = []

    all_chunks = []
    for f in db_files:
        f_path = f.path.replace("\\", "/")
        f_content = f.content or ""
        if f_content.strip():
            file_chunks = chunk_file(f_path, f_content)
            all_chunks.extend(file_chunks)
            file_list.append(f_path)

    if all_chunks:
        stored = store_temporary_chunks(all_chunks, model_name=model_name)
        indexed_chunk_count = len(stored)

    return {
        "success": True,
        "user_id": user_id,
        "project_id": project_id,
        "indexed_chunk_count": indexed_chunk_count,
        "files": file_list,
    }


def semantic_search(
    query: str,
    top_k: int = 5,
    candidates: Optional[List[Dict[str, Any]]] = None,
    db: Any = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    model_name: Optional[str] = None,
    include_content: bool = True,
    max_content_chars: int = 300,
) -> Dict[str, Any]:
    """Perform Chunk-Level Semantic Search for a user query (Requirement 11).

    Searches individual code chunks (functions, classes, imports) rather than whole files.

    Pipeline:
        User Query
            ↓
        Generate Query Embedding
            ↓
        Compare with Stored Chunk Embeddings
            ↓
        Calculate Cosine Similarity Scores
            ↓
        Rank Chunks by Similarity
            ↓
        Select Top-K Chunks
            ↓
        Return Chunk Metadata Results (e.g. authenticate_user() 0.94, verify_token() 0.88)
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error": "Query string cannot be empty.",
            "results": [],
            "count": 0,
        }

    top_k = max(1, top_k)

    # 1. Embed User Query
    try:
        query_info = embed_user_query(query, model_name=model_name)
        query_vector = query_info["vector"]
    except Exception as exc:
        logger.error(f"Failed to generate query embedding for '{query}': {exc}")
        return {
            "success": False,
            "error": f"Failed to embed user query: {str(exc)}",
            "results": [],
            "count": 0,
        }

    # 2. Gather Candidates
    target_candidates = candidates

    if target_candidates is None:
        # Check DB project files if db, user_id, project_id are provided
        if db is not None and user_id is not None and project_id is not None:
            try:
                index_project_files_to_temporary_store(
                    db=db,
                    user_id=user_id,
                    project_id=project_id,
                    model_name=model_name,
                )
                target_candidates = list_temporary_embeddings()
            except Exception as db_err:
                logger.warning(
                    f"Error fetching DB project files for semantic search: {db_err}"
                )

        # Fallback to in-memory temporary embeddings if candidates list is still empty
        if not target_candidates:
            target_candidates = list_temporary_embeddings()

    if not target_candidates:
        return {
            "success": True,
            "query": query,
            "results": [],
            "count": 0,
            "message": "No stored chunk embeddings found to compare against.",
        }

    # 3. Calculate Similarity Scores & Rank Chunks by Cosine Similarity
    ranked = find_most_similar(
        query_vector=query_vector,
        candidates=target_candidates,
        top_k=top_k,
        metric="cosine",
    )

    # 4. Format Useful Chunk Metadata Results
    results = []
    for item in ranked[:top_k]:
        score_val = round(float(item["score"]), 4)
        item_meta = item.get("metadata", {})

        cid = item.get("chunk_id") or f"{item.get('file')}:{item.get('symbol')}"
        sym = item.get("symbol") or item_meta.get("symbol") or item.get("file")
        fpath = item.get("file") or item_meta.get("file", "")
        utype = item.get("type") or item_meta.get("type", "chunk")
        sl = item.get("start_line") or item_meta.get("start_line")
        el = item.get("end_line") or item_meta.get("end_line")

        res_entry = {
            "chunk_id": cid,
            "symbol": sym,
            "file": fpath,
            "type": utype,
            "start_line": sl,
            "end_line": el,
            "score": score_val,
            "similarity_score": score_val,
            "metadata": item_meta or {
                "file": fpath,
                "symbol": sym,
                "type": utype,
                "start_line": sl,
                "end_line": el,
            },
        }

        if include_content:
            raw_content = item.get("content", "")
            if len(raw_content) > max_content_chars:
                limited_content = (
                    raw_content[:max_content_chars]
                    + "\n... [truncated to preserve context window]"
                )
            else:
                limited_content = raw_content
            res_entry["content"] = limited_content

        results.append(res_entry)

    return {
        "success": True,
        "query": query,
        "count": len(results),
        "results": results[:top_k],
    }
