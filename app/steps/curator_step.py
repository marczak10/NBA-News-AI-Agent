from app.agents.curator_agent import CuratorAgent
from app.database.connection import get_session
from app.database.table_models import Summary
from app.steps.base import State
from datetime import datetime, timedelta, timezone
import uuid

def _get_cutoff_reference_time(state: State) -> datetime:
     start_time = state.get("start_time")
     if start_time is None:
          return datetime.utcnow()
     if start_time.tzinfo is None:
          return start_time
     return start_time.astimezone(timezone.utc).replace(tzinfo=None)

def curate(state: State) -> State:
    print("Starting curation step...")
    cutoff = _get_cutoff_reference_time(state) - timedelta(hours=24)
    curator_agent = CuratorAgent()
    
    with get_session() as session:
          recent_summaries = (
               session.query(Summary)
               .filter(Summary.article_created_at>= cutoff)
               .all()
          )
          
          ranked_summaries = curator_agent.rank_summaries(recent_summaries)
          print(f"Ranked summaries: {ranked_summaries}")
     
          return {
               "ranked_summaries": ranked_summaries
          }
               