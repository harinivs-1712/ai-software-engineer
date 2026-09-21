import ast
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum character limit per chunk to ensure strict adherence to gemini-embedding-001 2,048 token ceiling (~6,000 chars)
MAX_CHUNK_SIZE_CHARS = 5500


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
    """Construct a standardized code chunk dictionary with line numbers, metadata, and import context."""
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


def partition_large_chunk(chunk: Dict[str, Any], max_chars: int = MAX_CHUNK_SIZE_CHARS) -> List[Dict[str, Any]]:
    """Safety partition policy for oversized functions, classes, or whole-file fallbacks.

    If a chunk exceeds max_chars, split it into smaller sliding-window sub-chunks to prevent model token overflow.
    """
    content = chunk.get("content", "")
    if len(content) <= max_chars:
        return [chunk]

    logger.warning(
        f"Chunk '{chunk.get('chunk_id')}' exceeds size limit ({len(content)} > {max_chars} chars). Partitioning into sub-chunks."
    )

    lines = content.splitlines(keepends=True)
    meta = chunk.get("metadata", {})
    start_l = meta.get("start_line", 1)
    base_id = chunk.get("chunk_id", "chunk")
    unit_type = meta.get("type", "chunk")
    symbol = meta.get("symbol")
    f_path = meta.get("file", "file")
    language = meta.get("language", "python")
    file_imports = meta.get("imports")

    sub_chunks = []
    current_lines = []
    current_length = 0
    current_start = start_l
    part_idx = 1

    for line in lines:
        if current_length + len(line) > max_chars and current_lines:
            sub_content = "".join(current_lines).strip()
            sub_end = current_start + len(current_lines) - 1
            part_symbol = f"{symbol}:part{part_idx}" if symbol else f"part{part_idx}"
            
            sub_chunks.append(
                create_chunk(
                    file_path=f_path,
                    unit_type=unit_type,
                    symbol=part_symbol,
                    start_line=current_start,
                    end_line=sub_end,
                    content=sub_content,
                    language=language,
                    imports=file_imports,
                )
            )
            part_idx += 1
            current_start = sub_end + 1
            current_lines = []
            current_length = 0

        current_lines.append(line)
        current_length += len(line)

    if current_lines:
        sub_content = "".join(current_lines).strip()
        sub_end = current_start + len(current_lines) - 1
        part_symbol = f"{symbol}:part{part_idx}" if symbol else f"part{part_idx}"
        sub_chunks.append(
            create_chunk(
                file_path=f_path,
                unit_type=unit_type,
                symbol=part_symbol,
                start_line=current_start,
                end_line=sub_end,
                content=sub_content,
                language=language,
                imports=file_imports,
            )
        )

    return sub_chunks


def extract_import_strings(import_nodes: List[ast.AST]) -> List[str]:
    """Extract human-readable import strings from AST import nodes."""
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
    """Parse Python source code using AST and extract logical code units (Functions, Classes, Imports)."""
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
        fallback = create_chunk(
            file_path=path,
            unit_type="file",
            symbol=None,
            start_line=1,
            end_line=total_lines,
            content=content.strip(),
            language="python",
            imports=[],
        )
        return partition_large_chunk(fallback)

    raw_chunks = []
    import_nodes = []
    func_or_class_units = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_or_class_units.append(("function", node.name, node))
        elif isinstance(node, ast.ClassDef):
            func_or_class_units.append(("class", node.name, node))

    file_imports = extract_import_strings(import_nodes)

    if not func_or_class_units:
        fallback = create_chunk(
            file_path=path,
            unit_type="file",
            symbol=None,
            start_line=1,
            end_line=total_lines,
            content=content.strip(),
            language="python",
            imports=file_imports,
        )
        return partition_large_chunk(fallback)

    if import_nodes:
        min_line = min(node.lineno for node in import_nodes)
        max_line = max(
            getattr(node, "end_lineno", node.lineno) for node in import_nodes
        )
        import_lines = lines[min_line - 1 : max_line]
        import_content = "".join(import_lines).strip()

        if import_content:
            raw_chunks.append(
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

    for unit_type, symbol_name, node in func_or_class_units:
        start_l = node.lineno
        end_l = getattr(node, "end_lineno", start_l)
        unit_lines = lines[start_l - 1 : end_l]
        unit_content = "".join(unit_lines).strip()

        if not unit_content:
            continue

        raw_chunks.append(
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

    if not raw_chunks and content.strip():
        fallback = create_chunk(
            file_path=path,
            unit_type="file",
            symbol=None,
            start_line=1,
            end_line=total_lines,
            content=content.strip(),
            language="python",
            imports=file_imports,
        )
        return partition_large_chunk(fallback)

    # Apply partition policy to any oversized AST chunks
    final_chunks = []
    for c in raw_chunks:
        final_chunks.extend(partition_large_chunk(c))

    return final_chunks


def chunk_file(path: str, content: str) -> List[Dict[str, Any]]:
    """Chunk a file based on file extension, language awareness, and input size policy."""
    if not isinstance(content, str) or not content.strip():
        return []

    clean_path = path.replace("\\", "/")
    ext = Path(path).suffix.lower()

    if ext == ".py":
        return chunk_python_code(clean_path, content)

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

    raw_chunk = create_chunk(
        file_path=clean_path,
        unit_type="file",
        symbol=None,
        start_line=1,
        end_line=total_lines,
        content=content.strip(),
        language=language,
        imports=[],
    )

    return partition_large_chunk(raw_chunk)


def chunk_project_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pipeline component: Project Files -> Chunking Service -> Standardized Chunks."""
    all_chunks = []
    print(f"\n[EMBEDDING TRACE] Chunking {len(files)} uploaded project file(s).", flush=True)
    for item in files:
        f_path = item.get("path") or item.get("file") or "unknown"
        f_content = item.get("content", "")
        if f_content and f_content.strip():
            file_chunks = chunk_file(f_path, f_content)
            all_chunks.extend(file_chunks)
            print(
                f"[EMBEDDING TRACE] File '{f_path}' produced {len(file_chunks)} chunk(s).",
                flush=True,
            )
            for chunk in file_chunks:
                print(
                    "[EMBEDDING TRACE] Chunk created: "
                    + json.dumps(
                        {
                            "chunk_id": chunk.get("chunk_id"),
                            "metadata": chunk.get("metadata", {}),
                            "content_chars": len(chunk.get("content", "")),
                        },
                        default=str,
                    ),
                    flush=True,
                )
    print(f"[EMBEDDING TRACE] Chunking complete: {len(all_chunks)} total chunk(s).\n", flush=True)
    return all_chunks
