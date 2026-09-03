import ast
from pathlib import Path


def analyze_python_file(
    path: str,
    content: str,
):

    try:
        tree = ast.parse(content)
    except SyntaxError:

        return {
            "path": path,
            "language": "python",
            "imports": [],
            "functions": [],
            "classes": [],
        }

    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for name in node.names:
                imports.append(name.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.append(node.module)

        elif isinstance(node, ast.FunctionDef):

            functions.append(node.name)

        elif isinstance(node, ast.AsyncFunctionDef):

            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):

            classes.append(node.name)

    return {
        "path": path,
        "language": "python",
        "imports": imports,
        "functions": functions,
        "classes": classes,
    }


def detect_language(path: str):

    extension = Path(path).suffix.lower()

    languages = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
    }

    return languages.get(
        extension,
        "unknown",
    )


def analyze_file(path: str, content: str):

    language = detect_language(path)

    if language == "python":

        return analyze_python_file(
            path,
            content,
        )

    return {
        "path": path,
        "language": language,
        "imports": [],
        "functions": [],
        "classes": [],
    }