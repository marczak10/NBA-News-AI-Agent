import logging
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.steps.base import State
from app.database.connection import get_engine
from app.database.create_tables import create_tables
from app.services.logging_config import configure_logging
from app.services.workflow import build_workflow

logger = logging.getLogger(__name__)


def run(state: State) -> State:
    configure_logging()
    logger.info("Starting NBA news workflow.")

    try:
        create_tables(get_engine())
        graph = build_workflow()
        result = graph.invoke(state)
    except Exception:
        logger.exception("NBA news workflow failed.")
        raise

    logger.info("Finished NBA news workflow.")
    return result


if __name__ == "__main__":
    run(State())
