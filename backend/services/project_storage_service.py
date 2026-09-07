from sqlalchemy.orm import Session

from models.project import Project, ProjectFile


def create_project(
    db: Session,
    user_id: int,
    project_name: str,
    files: list,
):

    project = Project(
        name=project_name,
        user_id=user_id,
    )

    db.add(project)
    db.flush()

    for file in files:

        project_file = ProjectFile(
            path=file["path"],
            content=file["content"],
            project_id=project.id,
        )

        db.add(project_file)

    db.commit()
    db.refresh(project)

    return project