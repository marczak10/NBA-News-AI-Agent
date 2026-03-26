from pathlib import Path
import sys

from langgraph.graph import END, START, StateGraph

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.steps.base import State
from app.steps.ingest_step import ingest
from app.steps.scraper_step import scrape
from app.steps.summary_step import summarize
from app.database.connection import engine
from app.database.create_tables import create_tables

def build_workflow():
    workflow = StateGraph(State)
    workflow.add_node("scrape", scrape)
    workflow.add_node("ingest", ingest)
    workflow.add_node("summarize", summarize)
    workflow.add_edge(START, "scrape")
    workflow.add_edge("scrape", "ingest")
    workflow.add_edge("ingest", "summarize")
    workflow.add_edge("summarize", END)
    return workflow.compile()