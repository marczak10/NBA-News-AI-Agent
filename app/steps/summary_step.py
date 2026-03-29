import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from langchain_openai import OpenAIEmbeddings

from app.database.connection import get_session
from app.database.table_models import ESPNArticle, NBAArticle, Summary, YoutubeVideo
from app.agents.summary_agent import SummaryAgent
from app.services.env_config import load_project_env
from app.steps.base import State

load_project_env()

logger = logging.getLogger(__name__)

def _get_cutoff_reference_time(state: State) -> datetime:
    start_time = state.get("start_time")
    if start_time is None:
        return datetime.utcnow()
    if start_time.tzinfo is None:
        return start_time
    return start_time.astimezone(timezone.utc).replace(tzinfo=None)


def _get_existing_summary_keys(
    session,
    source_ids_by_type: dict[str, list[str]],
) -> set[tuple[str, str]]:
    existing_summary_keys: set[tuple[str, str]] = set()

    for source_type, source_ids in source_ids_by_type.items():
        if not source_ids:
            continue

        rows = (
            session.query(Summary.source_type, Summary.source_id)
            .filter(
                Summary.source_type == source_type,
                Summary.source_id.in_(source_ids),
            )
            .distinct()
            .all()
        )
        existing_summary_keys.update(
            (row_source_type, row_source_id) for row_source_type, row_source_id in rows
        )

    return existing_summary_keys


def _filter_unsummarized_items(
    items: list[Any],
    source_type: str,
    existing_summary_keys: set[tuple[str, str]],
) -> list[Any]:
    return [
        item for item in items if (source_type, item.id) not in existing_summary_keys
    ]

def _create_embedding(title: str, summary_text: str) -> str | None:
    embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_KEY"),
)
    if not summary_text:
        return None
    combined_text = f"Title: {title}\nSummary: {summary_text}"
    embedding = embedding_model.embed_documents([combined_text])[0]
    return json.dumps(embedding)


def summarize(state: State, hours: int = 24) -> dict[str, dict[str, int]]:
    logger.info("Starting summary step for the last %s hours.", hours)
    summarize_start_time = time.time()
    cutoff = _get_cutoff_reference_time(state) - timedelta(hours=hours)
    summary_agent = SummaryAgent()

    with get_session() as session:
        recent_nba_articles = (
            session.query(NBAArticle).filter(NBAArticle.published_date >= cutoff).all()
        )
        recent_espn_articles = (
            session.query(ESPNArticle)
            .filter(ESPNArticle.published_date >= cutoff)
            .all()
        )
        recent_youtube_videos = (
            session.query(YoutubeVideo)
            .filter(
                YoutubeVideo.published_date >= cutoff, YoutubeVideo.transcript != None
            )
            .all()
        )
        logger.info(
            "Found %s NBA articles, %s ESPN articles, and %s YouTube videos to check.",
            len(recent_nba_articles),
            len(recent_espn_articles),
            len(recent_youtube_videos),
        )

        existing_summary_keys = _get_existing_summary_keys(
            session,
            {
                "nba_article": [article.id for article in recent_nba_articles],
                "espn_article": [article.id for article in recent_espn_articles],
                "youtube_video": [video.id for video in recent_youtube_videos],
            },
        )

        nba_articles_to_summarize = _filter_unsummarized_items(
            recent_nba_articles,
            "nba_article",
            existing_summary_keys,
        )
        espn_articles_to_summarize = _filter_unsummarized_items(
            recent_espn_articles,
            "espn_article",
            existing_summary_keys,
        )
        youtube_videos_to_summarize = _filter_unsummarized_items(
            recent_youtube_videos,
            "youtube_video",
            existing_summary_keys,
        )

        for article in nba_articles_to_summarize:
            summary = summary_agent.summarize_article(
                "article", article.title, article.content
            )
            embedding = _create_embedding(summary.title, summary.summary)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=article.id,
                    source_type="nba_article",
                    summary_text=summary.summary,
                    article_created_at=article.published_date,
                    summary_vector=embedding,
                    created_at=datetime.utcnow(),
                )
            )

        for article in espn_articles_to_summarize:
            summary = summary_agent.summarize_article(
                "article", article.title, article.content
            )
            embedding = _create_embedding(summary.title, summary.summary)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=article.id,
                    source_type="espn_article",
                    summary_text=summary.summary,
                    summary_vector=embedding,
                    article_created_at=article.published_date,
                    created_at=datetime.utcnow(),
                )
            )

        for video in youtube_videos_to_summarize:
            summary = summary_agent.summarize_article(
                "video", video.title, video.description
            )
            embedding = _create_embedding(summary.title, summary.summary)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=video.id,
                    source_type="youtube_video",
                    summary_text=summary.summary,
                    summary_vector=embedding,
                    article_created_at=video.published_date,
                    created_at=datetime.utcnow(),
                )
            )

        summary = {
            "nba_articles_summarized": len(nba_articles_to_summarize),
            "espn_articles_summarized": len(espn_articles_to_summarize),
            "youtube_videos_summarized": len(youtube_videos_to_summarize),
        }

        session.commit()

    summarize_end_time = time.time()
    logger.info(
        "Finished summary step in %.2f seconds. Summary: %s",
        summarize_end_time - summarize_start_time,
        summary,
    )

    return {"summarization_summary": summary}
