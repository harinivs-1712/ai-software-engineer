from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".java",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".cpp",
    ".c",
    ".html",
    ".css",
    ".json",
    ".md",
}


MAX_FILE_SIZE = 2 * 1024 * 1024


def get_file_extension(
    filename: str
) -> str:

    return Path(
        filename
    ).suffix.lower()


def is_supported_file(
    filename: str
) -> bool:

    extension = get_file_extension(
        filename
    )

    return extension in ALLOWED_EXTENSIONS


def validate_file_size(
    file_content: bytes
) -> None:

    if len(file_content) > MAX_FILE_SIZE:

        raise ValueError(
            "File size exceeds the 2 MB limit."
        )


def read_text_file(
    file_content: bytes
) -> str:

    return file_content.decode(
        "utf-8"
    )