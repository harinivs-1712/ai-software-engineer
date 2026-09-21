import logging
from typing import Any, Dict, List, Optional

from services.chunking_service import chunk_file, chunk_project_files
from services.embedding_service import (
    clear_temporary_embeddings,
    get_embedding_service,
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
    """Embed the user search query into a vector representation using CODE_RETRIEVAL_QUERY task type.

    Flow:
        query -> embedding model (task_type=CODE_RETRIEVAL_QUERY) -> query vector
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("User query must be a non-empty string.")

    query_str = query.strip()
    service = get_embedding_service()
    vector, model_used, dim = service.generate_embedding_with_meta(
        query_str, model_name=model_name, task_type="CODE_RETRIEVAL_QUERY"
    )

    return {
        "query": query_str,
        "vector": vector,
        "model_used": model_used,
        "dimension": dim,
        "success": True,
    }


def index_project_files_to_temporary_store(
    db: Any,
    user_id: int,
    project_id: int,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Chunk files stored in ProjectFile DB model and store vector embeddings per chunk.

    Flow:
        ProjectFile -> Chunking -> Code Chunks + Metadata -> Batch Embedding -> Tenant Vector Store
    """
    from services.file_system_service import get_user_project_files

    # Clear old entries for this tenant project to prevent stale or cross-project data leaks
    clear_temporary_embeddings(user_id=user_id, project_id=project_id)

    db_files = get_user_project_files(
        db=db, user_id=user_id, project_id=project_id
    )
    indexed_chunk_count = 0
    file_list = []

    file_records = []
    for f in db_files:
        f_path = f.path.replace("\\", "/")
        f_content = f.content or ""
        if f_content.strip():
            file_records.append({"path": f_path, "content": f_content})
            file_list.append(f_path)

    # chunk_project_files prints the per-file, per-chunk metadata trace.
    all_chunks = chunk_project_files(file_records)

    if all_chunks:
        stored = store_temporary_chunks(
            all_chunks,
            model_name=model_name,
            user_id=user_id,
            project_id=project_id,
            task_type="RETRIEVAL_DOCUMENT",
        )
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
    max_content_chars: int = 400,
) -> Dict[str, Any]:
    """Perform Chunk-Level Semantic Search for a user query (Requirement 11).

    Searches individual code chunks (functions, classes, imports) using exact model vector space matching.
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error": "Query string cannot be empty.",
            "results": [],
            "count": 0,
        }

    top_k = max(1, top_k)

    # 1. Embed User Query with CODE_RETRIEVAL_QUERY task type
    try:
        query_info = embed_user_query(query, model_name=model_name)
        query_vector = query_info["vector"]
        query_model = query_info["model_used"]
        print(
            "\n[EMBEDDING TRACE] Query embedded: "
            f"query={query!r}, model={query_model!r}, dimension={len(query_vector)}, "
            f"vector_preview={[round(value, 5) for value in query_vector[:5]]}",
            flush=True,
        )
    except Exception as exc:
        logger.error(f"Failed to generate query embedding for '{query}': {exc}")
        return {
            "success": False,
            "error": f"Failed to embed user query: {str(exc)}",
            "results": [],
            "count": 0,
        }

    # 2. Gather Candidates for tenant scope
    target_candidates = candidates

    if target_candidates is None:
        if db is not None and user_id is not None and project_id is not None:
            try:
                # Check if already indexed for tenant scope
                existing = list_temporary_embeddings(user_id=user_id, project_id=project_id)
                if not existing:
                    index_project_files_to_temporary_store(
                        db=db,
                        user_id=user_id,
                        project_id=project_id,
                        model_name=model_name,
                    )
                    existing = list_temporary_embeddings(user_id=user_id, project_id=project_id)
                target_candidates = existing
            except Exception as db_err:
                logger.warning(
                    f"Error fetching DB project files for semantic search: {db_err}"
                )

        if not target_candidates:
            target_candidates = list_temporary_embeddings(user_id=user_id, project_id=project_id)

    if not target_candidates:
        return {
            "success": True,
            "query": query,
            "results": [],
            "count": 0,
            "message": "No stored chunk embeddings found to compare against.",
        }

    # 3. Calculate Similarity Scores & Rank Chunks by Cosine Similarity with Model Matching
    ranked = find_most_similar(
        query_vector=query_vector,
        candidates=target_candidates,
        top_k=top_k,
        metric="cosine",
        query_model=query_model,
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
        cand_model = item.get("model_used") or query_model

        raw_vec = item.get("embedding", [])
        vec_dim = len(raw_vec)
        vec_prev = [round(float(v), 4) for v in raw_vec[:5]] if raw_vec else []

        res_entry = {
            "chunk_id": cid,
            "symbol": sym,
            "file": fpath,
            "type": utype,
            "start_line": sl,
            "end_line": el,
            "score": score_val,
            "similarity_score": score_val,
            "model_used": cand_model,
            "vector_dimension": vec_dim,
            "vector_preview": vec_prev,
            "metadata": item_meta or {
                "file": fpath,
                "symbol": sym,
                "type": utype,
                "start_line": sl,
                "end_line": el,
                "model_used": cand_model,
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

    print(
        f"[EMBEDDING TRACE] Top-{len(results)} retrieval result(s) for query {query!r}:",
        flush=True,
    )
    for rank, result in enumerate(results, start=1):
        print(
            "[EMBEDDING TRACE] "
            f"#{rank} score={result['similarity_score']}, chunk_id={result['chunk_id']!r}, "
            f"file={result['file']!r}, symbol={result['symbol']!r}, "
            f"lines={result['start_line']}-{result['end_line']}, "
            f"model={result['model_used']!r}, dimension={result['vector_dimension']}, "
            f"metadata={result['metadata']}",
            flush=True,
        )
    print("[EMBEDDING TRACE] Retrieval complete.\n", flush=True)

    return {
        "success": True,
        "query": query,
        "query_model": query_model,
        "count": len(results),
        "results": results[:top_k],
    }
