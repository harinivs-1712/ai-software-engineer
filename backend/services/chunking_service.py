import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def create_chunk(
    file_path: str,
    unit_type: str,
    symbol: Optional[str],
    start_line: int,
    end_line: int,
    content: str,
    language: str = "python",
    imports: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Construct a standardized code chunk dictionary with line numbers, metadata, and import context.

    Standard Structure:
    {
      "chunk_id": "backend/auth.py:function:authenticate_user",  (or "config.py:file")
      "content": "def authenticate_user(...): ...",
      "metadata": {
        "file": "backend/auth.py",
        "language": "python",
        "symbol": "authenticate_user",  (or null for files without symbols)
        "type": "function",
        "start_line": 25,
        "end_line": 48,
        "imports": [...]
      }
    }
    """
    clean_path = file_path.replace("\\", "/")
    if symbol is not None and str(symbol).strip():
        chunk_id = f"{clean_path}:{unit_type}:{symbol}"
    else:
        chunk_id = f"{clean_path}:{unit_type}"

    metadata = {
        "file": clean_path,
        "language": language,
        "symbol": symbol,
        "type": unit_type,
        "start_line": start_line,
        "end_line": end_line,
    }

    if imports is not None:
        metadata["imports"] = imports

    return {
        "chunk_id": chunk_id,
        "content": content,
        "metadata": metadata,
    }


def extract_import_strings(import_nodes: List[ast.AST]) -> List[str]:
    """Extract human-readable import strings from AST import nodes.

    Example:
        from database import get_user -> "database.get_user"
        import jwt                    -> "jwt"
    """
    imports_list = []
    for node in import_nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports_list.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod_prefix = node.module + "." if node.module else ""
            for alias in node.names:
                imports_list.append(f"{mod_prefix}{alias.name}")
    return imports_list


def chunk_python_code(path: str, content: str) -> List[Dict[str, Any]]:
    """Parse Python source code using AST and extract logical code units (Functions, Classes, Imports).

    Handling Files Without Functions/Classes (Requirement 12):
        If a file (e.g. config.py, constants.py) has no functions or classes,
        it produces a file-level chunk with chunk_id="config.py:file", type="file", symbol=None.

    AST-Aware Prioritization (Requirement 13):
        Prioritizes Functions, Classes, Imports, and File-Level Content without doing premature fixed-token splits.
    """
    if not isinstance(content, str) or not content.strip():
        return []

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)

    try:
        tree = ast.parse(content)
    except SyntaxError as syntax_err:
        logger.warning(
            f"SyntaxError parsing AST for '{path}': {syntax_err}. Falling back to file-level chunk."
        )
        return [
            create_chunk(
                file_path=path,
                unit_type="file",
                symbol=None,
                start_line=1,
                end_line=total_lines,
                content=content.strip(),
                language="python",
                imports=[],
            )
        ]

    chunks = []
    import_nodes = []
    func_or_class_units = []
    statement_nodes = []

    # Iterate over top-level AST nodes
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_or_class_units.append(("function", node.name, node))
        elif isinstance(node, ast.ClassDef):
            func_or_class_units.append(("class", node.name, node))
        else:
            statement_nodes.append(node)

    # Extract File-Level Import Strings for context attachment
    file_imports = extract_import_strings(import_nodes)

    # REQUIREMENT 12: If file has NO functions and NO classes (e.g. config.py, constants.py)
    if not func_or_class_units:
        return [
            create_chunk(
                file_path=path,
                unit_type="file",
                symbol=None,
                start_line=1,
                end_line=total_lines,
                content=content.strip(),
                language="python",
                imports=file_imports,
            )
        ]

    # 1. Process Imports Chunk if present
    if import_nodes:
        min_line = min(node.lineno for node in import_nodes)
        max_line = max(
            getattr(node, "end_lineno", node.lineno) for node in import_nodes
        )
        import_lines = lines[min_line - 1 : max_line]
        import_content = "".join(import_lines).strip()

        if import_content:
            chunks.append(
                create_chunk(
                    file_path=path,
                    unit_type="imports",
                    symbol=None,
                    start_line=min_line,
                    end_line=max_line,
                    content=import_content,
                    language="python",
                    imports=file_imports,
                )
            )

    # 2. Process Function and Class Chunks
    for unit_type, symbol_name, node in func_or_class_units:
        start_l = node.lineno
        end_l = getattr(node, "end_lineno", start_l)
        unit_lines = lines[start_l - 1 : end_l]
        unit_content = "".join(unit_lines).strip()

        if not unit_content:
            continue

        chunks.append(
            create_chunk(
                file_path=path,
                unit_type=unit_type,
                symbol=symbol_name,
                start_line=start_l,
                end_line=end_l,
                content=unit_content,
                language="python",
                imports=file_imports,
            )
        )

    # Fallback if no chunks extracted
    if not chunks and content.strip():
        chunks.append(
            create_chunk(
                file_path=path,
                unit_type="file",
                symbol=None,
                start_line=1,
                end_line=total_lines,
                content=content.strip(),
                language="python",
                imports=file_imports,
            )
        )

    return chunks


def chunk_file(path: str, content: str) -> List[Dict[str, Any]]:
    """Chunk a file based on file extension and language awareness.

    Supports AST-based chunking for Python (.py) files and logical chunking for text/markdown/code.
    """
    if not isinstance(content, str) or not content.strip():
        return []

    clean_path = path.replace("\\", "/")
    ext = Path(path).suffix.lower()

    if ext == ".py":
        return chunk_python_code(clean_path, content)

    # Non-Python / General Text / Markdown (e.g. README.md, config.json) -> file-level chunk
    lines = content.splitlines()
    total_lines = len(lines)
    lang_map = {
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".css": "css",
        ".html": "html",
        ".json": "json",
        ".md": "markdown",
    }
    language = lang_map.get(ext, "text")

    return [
        create_chunk(
            file_path=clean_path,
            unit_type="file",
            symbol=None,
            start_line=1,
            end_line=total_lines,
            content=content.strip(),
            language=language,
            imports=[],
        )
    ]


def chunk_project_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pipeline component: Project Files -> Chunking Service -> Standardized Chunks.

    Args:
        files: List of file dictionaries containing 'path' (or 'file') and 'content'.

    Returns:
        List[Dict[str, Any]]: List of standardized chunk dictionaries.
    """
    all_chunks = []
    for item in files:
        f_path = item.get("path") or item.get("file") or "unknown"
        f_content = item.get("content", "")
        if f_content and f_content.strip():
            file_chunks = chunk_file(f_path, f_content)
            all_chunks.extend(file_chunks)
    return all_chunks
