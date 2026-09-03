from pathlib import Path


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
):
    if not files:
        return ""

    all_file_paths = [f["path"] for f in files]
    file_list_summary = "\n".join(f"- {path}" for path in all_file_paths[:50])

    sections = [
        f"PROJECT OVERVIEW - ALL FILES IN PROJECT ({len(files)} total):\n{file_list_summary}\n"
    ]

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