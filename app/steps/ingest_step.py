from typing import Any

from sqlalchemy.orm import Session

from app.constants.data_models import (
    ESPNArticle as ESPNArticleData,
    NBAArticle as NBAArticleData,
    YoutubeVideo as YoutubeVideoData,
)
from app.database.connection import get_session
from app.database.table_models import (
    ESPNArticle as ESPNArticleRecord,
    NBAArticle as NBAArticleRecord,
    YoutubeVideo as YoutubeVideoRecord,
)
from app.steps.base import State


def _upsert_records(
    session: Session,
    items: list[Any],
    model: type[Any],
    fields: tuple[str, ...],
) -> dict[str, int]:
    incoming_ids = list(dict.fromkeys(item.id for item in items))
    existing_rows = session.query(model).filter(model.id.in_(incoming_ids)).all()
    existing_by_id = {row.id: row for row in existing_rows}

    inserted = 0
    updated = 0

    for item in items:
        row = existing_by_id.get(item.id)

        if row is None:
            row = model(id=item.id)
            session.add(row)
            existing_by_id[item.id] = row
            inserted += 1
        else:
            updated += 1

        for field in fields:
            setattr(row, field, getattr(item, field))

    session.commit()
    return {"inserted": inserted, "updated": updated}


def ingest(state: State) -> dict[str, dict[str, dict[str, int]]]:
    print("Starting ingestion step...")
    nba_articles = state.get("nba_articles", [])
    espn_articles = state.get("espn_articles", [])
    youtube_videos = state.get("youtube_videos", [])

    with get_session() as session:
        summary = {
            "nba_articles": _upsert_records(session, nba_articles, NBAArticleRecord, ("title", "description", "url", "published_date", "content")),
            "espn_articles": _upsert_records(session, espn_articles, ESPNArticleRecord, ("title", "description", "url", "published_date", "content")),
            "youtube_videos": _upsert_records(session, youtube_videos, YoutubeVideoRecord, ("title", "description", "url", "published_date", "transcript")),
        }
        print(f"Ingestion summary: {summary}")
    return {"ingest_summary": summary}
