from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.steps.base import State
from app.database.connection import engine
from app.database.create_tables import create_tables
from app.services.workflow import build_workflow


def main(initial_state: State | None = None):
    create_tables(engine)
    graph = build_workflow()
    return graph.invoke(initial_state or {})


if __name__ == "__main__":
    main(State())
