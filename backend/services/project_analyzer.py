from services.code_analyzer import analyze_file
from services.project_service import read_project_files


def analyze_project(file_content: bytes):

    files = read_project_files(
        file_content
    )

    analysis = []

    for file in files:

        result = analyze_file(
            file["path"],
            file["content"],
        )

        analysis.append(result)

    return analysis