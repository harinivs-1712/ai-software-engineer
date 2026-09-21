from pathlib import Path
from typing import Any, Optional


def score_file(
    path: str,
    query: str,
):
    score = 0

    filename = Path(path).stem.lower()
    query_words = query.lower().split()

    for word in query_words:

        if word in filename:
            score += 5

        if word in path.lower():
            score += 2

    return score


def select_relevant_files(
    files,
    query: str,
    max_files: int = 5,
):
    scored_files = []

    for file in files:

        score = score_file(
            file["path"],
            query,
        )

        scored_files.append(
            (
                score,
                file,
            )
        )

    scored_files.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected = []

    for score, file in scored_files:

        if len(selected) >= max_files:
            break

        selected.append(file)

    return selected


def build_project_context(
    files,
    query: str,
    max_files: int = 5,
    db: Any = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
):
    if not files:
        return ""

    all_file_paths = [f.get("path", "") for f in files if isinstance(f, dict) and f.get("path")]
    file_list_summary = "\n".join(f"- {path}" for path in all_file_paths[:50])

    sections = [
        f"PROJECT OVERVIEW - ALL FILES IN PROJECT ({len(files)} total):\n{file_list_summary}\n"
    ]

    # Perform Chunk-Level Vector Embedding Semantic Search
    try:
        from services.semantic_search_service import semantic_search
        from services.chunking_service import chunk_project_files

        # Prepare chunks for files
        all_chunks = chunk_project_files(files)
        if all_chunks:
            from services.embedding_service import store_temporary_chunks
            candidates = store_temporary_chunks(all_chunks)
            search_res = semantic_search(query=query, top_k=max_files, candidates=candidates, include_content=True, max_content_chars=800)
            results = search_res.get("results", [])

            if results:
                sections.append("### SEMANTIC SEARCH (VECTOR EMBEDDINGS & AST CHUNKS):")
                sections.append(f"Retrieved Top-{len(results)} vector-matched code chunks using Cosine Similarity on gemini-embedding-001 vectors:\n")

                for res in results:
                    cid = res.get("chunk_id", "")
                    score = res.get("score", 0.0)
                    stype = res.get("type", "chunk")
                    sym = res.get("symbol") or "N/A"
                    fpath = res.get("file", "")
                    content = res.get("content", "")
                    sl = res.get("start_line", 1)
                    el = res.get("end_line", 1)

                    sections.append(
                        f"Chunk ID: `{cid}`\n"
                        f"File: `{fpath}` (Lines {sl}-{el})\n"
                        f"Type: {stype} | Symbol: {sym} | Cosine Similarity Score: {score}\n"
                        f"```python\n{content}\n```\n"
                    )

                return "\n\n".join(sections)
    except Exception as err:
        pass

    # Fallback to keyword search if vector embedding fails
    relevant_files = select_relevant_files(
        files,
        query,
        max_files,
    )

    for file in relevant_files:
        sections.append(
            f"FILE: {file['path']}\n\n```text\n{file['content']}\n```\n"
        )

    return "\n\n".join(sections)


def get_project_files_for_context(
    project,
):

    return [
        {
            "path": file.path,
            "content": file.content,
        }
        for file in project.files
    ]