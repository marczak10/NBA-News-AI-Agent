import uuid
from datetime import datetime, timedelta

from app.database.connection import get_session
from app.database.table_models import (
    ESPNArticle,
    NBAArticle,
    Summary,
    YoutubeVideo
)
from app.agents.summary_agent import SummaryAgent
from app.steps.base import State


def summarize(state: State, hours: int = 24) -> dict[str, dict[str, int]]:
    print(f"Starting summarization step for items from the last {hours} hours...")
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    summary_agent = SummaryAgent()

    with get_session() as session:
        recent_nba_articles = (
            session.query(NBAArticle)
            .filter(NBAArticle.published_date >= cutoff)
            .all()
        )
        recent_espn_articles = (
            session.query(ESPNArticle)
            .filter(ESPNArticle.published_date >= cutoff)
            .all()
        )
        recent_youtube_videos = (
            session.query(YoutubeVideo)
            .filter(YoutubeVideo.published_date >= cutoff, YoutubeVideo.transcript != None)
            .all()
        )

        for article in recent_nba_articles:
            summary = summary_agent.summarize_article("article", article.title, article.content)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=article.id,
                    source_type="nba_article",
                    summary_text=summary.summary,
                    article_created_at=article.published_date,
                    created_at=datetime.utcnow(),
                )
            )

        for article in recent_espn_articles:
            summary = summary_agent.summarize_article("article", article.title, article.content)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=article.id,
                    source_type="espn_article",
                    summary_text=summary.summary,
                    article_created_at=article.published_date,
                    created_at=datetime.utcnow(),
                )
            )

        for video in recent_youtube_videos:
            summary = summary_agent.summarize_article("video", video.title, video.description)
            session.add(
                Summary(
                    id=str(uuid.uuid4()),
                    title=summary.title,
                    source_id=video.id,
                    source_type="youtube_video",
                    summary_text=summary.summary,
                    article_created_at=video.published_date,
                    created_at=datetime.utcnow(),
                )
            )

        summary = {
            "nba_articles_summarized": len(recent_nba_articles),
            "espn_articles_summarized": len(recent_espn_articles),
            "youtube_videos_summarized": len(recent_youtube_videos),
        }

        session.commit()
        
    print (f"Summarization step completed. Summary: {summary}")

    return {"summarization_summary": summary}
