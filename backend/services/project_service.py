from io import BytesIO
from pathlib import Path
from zipfile import ZipFile


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".html",
    ".css",
    ".json",
    ".md",
}


def is_supported_project_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def get_project_files(file_content: bytes):
    project_files = []

    with ZipFile(BytesIO(file_content)) as archive:

        for entry in archive.infolist():

            if entry.is_dir():
                continue

            filename = entry.filename

            if not is_supported_project_file(filename):
                continue

            project_files.append(filename)

    return project_files


def read_project_files(file_content: bytes):

    files = []

    with ZipFile(BytesIO(file_content)) as archive:

        for entry in archive.infolist():

            if entry.is_dir():
                continue

            filename = entry.filename

            if not is_supported_project_file(filename):
                continue

            try:
                content = archive.read(entry).decode("utf-8")
            except UnicodeDecodeError:
                continue

            files.append(
                {
                    "path": filename,
                    "content": content,
                }
            )

    return files


extract_project = get_project_files