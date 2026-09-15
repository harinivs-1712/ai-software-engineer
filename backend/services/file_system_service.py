from pathlib import PurePosixPath
from sqlalchemy.orm import Session

from models.project import ProjectFile
from services.ownership_service import get_user_project


MAX_FILE_READ_SIZE = 100_000


def normalize_path(path: str) -> str:
    """
    Normalize a project-relative path.
    """

    if not isinstance(path, str):
        raise ValueError(
            "Path must be a string."
        )

    path = path.strip()

    if not path:
        raise ValueError(
            "Path cannot be empty."
        )

    # Always treat project paths as POSIX-style paths.
    path = path.replace("\\", "/")

    # Reject drive letters (e.g. C:, D:)
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        raise ValueError(
            "Absolute Windows paths are not allowed."
        )

    normalized = PurePosixPath(path)

    # Reject absolute paths.
    if normalized.is_absolute():
        raise ValueError(
            "Absolute paths are not allowed."
        )

    # Reject path traversal.
    if ".." in normalized.parts:
        raise ValueError(
            "Path traversal is not allowed."
        )

    clean_parts = [p for p in normalized.parts if p not in (".", "")]
    if not clean_parts:
        return ""

    return str(PurePosixPath(*clean_parts))


def get_user_project_files(
    db: Session,
    user_id: int,
    project_id: int,
):
    """
    Verify ownership and return all ProjectFile records for a project.
    """
    project = get_user_project(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    return (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project.id)
        .all()
    )


def list_project_files(
    db: Session,
    user_id: int,
    project_id: int,
) -> dict:
    """
    List files available inside the currently selected project.
    """
    db_files = get_user_project_files(
        db=db,
        user_id=user_id,
        project_id=project_id,
    )

    files = [
        {
            "path": str(PurePosixPath(f.path.replace("\\", "/")))
        }
        for f in db_files
    ]

    return {
        "success": True,
        "files": files,
    }


def read_project_file(
    db: Session,
    user_id: int,
    project_id: int,
    path: str,
    start_line: int = None,
    end_line: int = None,
) -> dict:
    """
    Read content of a project file with path validation and size limits.
    """
    norm_path = normalize_path(path)

    db_files = get_user_project_files(
        db=db,
        user_id=user_id,
        project_id=project_id,
    )

    target_file = None
    for f in db_files:
        clean_fpath = str(PurePosixPath(f.path.replace("\\", "/")))
        if clean_fpath == norm_path:
            target_file = f
            break

    if target_file is None:
        return {
            "success": False,
            "error": f"File not found: '{norm_path}'",
        }

    content = target_file.content or ""
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)

    if start_line is not None or end_line is not None:
        s_line = start_line if (start_line is not None and start_line >= 1) else 1
        e_line = end_line if (end_line is not None and end_line <= total_lines) else total_lines
        selected_lines = lines[s_line - 1 : e_line]
        content_to_return = "".join(selected_lines)
    else:
        content_to_return = content

    if len(content_to_return.encode("utf-8")) > MAX_FILE_READ_SIZE:
        return {
            "success": False,
            "error": f"File content exceeds maximum size of {MAX_FILE_READ_SIZE} bytes. Specify start_line and end_line parameters.",
        }

    return {
        "success": True,
        "path": norm_path,
        "content": content_to_return,
    }


def search_project_files(
    db: Session,
    user_id: int,
    project_id: int,
    query: str,
) -> dict:
    """
    Search project files for a case-insensitive query substring.
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error": "Search query cannot be empty.",
        }

    query_str = query.strip()
    query_lower = query_str.lower()

    db_files = get_user_project_files(
        db=db,
        user_id=user_id,
        project_id=project_id,
    )

    results = []
    seen_paths = set()

    for file_record in db_files:
        content = file_record.content or ""
        if query_lower in content.lower():
            clean_path = str(PurePosixPath(file_record.path.replace("\\", "/")))
            if clean_path not in seen_paths:
                seen_paths.add(clean_path)
                results.append({"path": clean_path})

    return {
        "success": True,
        "query": query_str,
        "results": results,
        "count": len(results),
    }


def get_project_file_info(
    db: Session,
    user_id: int,
    project_id: int,
    path: str,
) -> dict:
    """
    Retrieve basic metadata for a project file.
    """
    norm_path = normalize_path(path)

    db_files = get_user_project_files(
        db=db,
        user_id=user_id,
        project_id=project_id,
    )

    for f in db_files:
        clean_fpath = str(PurePosixPath(f.path.replace("\\", "/")))
        if clean_fpath == norm_path:
            content = f.content or ""
            p = PurePosixPath(norm_path)
            return {
                "success": True,
                "path": norm_path,
                "size": len(content.encode("utf-8")),
                "extension": p.suffix,
                "line_count": len(content.splitlines()),
            }

    return {
        "success": False,
        "error": f"File not found: '{norm_path}'",
    }
