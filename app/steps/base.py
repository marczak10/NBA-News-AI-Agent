from datetime import datetime
from typing import TypedDict
from enum import Enum

from app.constants.data_models import ESPNArticle, NBAArticle, YoutubeVideo


class UpsertCounts(TypedDict):
    inserted: int
    updated: int


class IngestSummary(TypedDict):
    nba_articles: UpsertCounts
    espn_articles: UpsertCounts
    youtube_videos: UpsertCounts


class RankedSummary(TypedDict):
    id: str
    title: str
    summary: str
    url: str
    source_id: str
    source_type: str
    article_created_at: datetime
    rank: int
    relevance_score: float
    reasoning: str


class EmailIntroduction(TypedDict):
    greeting: str
    introduction: str


class PipelineStatus(Enum):
    NOT_STARTED = "not_started"
    SCRAPING = "scraping"
    INGESTING = "ingesting"
    SUMMARIZING = "summarizing"
    CURATING = "curating"
    EMAILING = "emailing"
    COMPLETED = "completed"


class State(TypedDict, total=False):
    start_time: datetime = datetime.now()
    pipeline_status: PipelineStatus = PipelineStatus.NOT_STARTED
    nba_articles: list[NBAArticle]
    espn_articles: list[ESPNArticle]
    youtube_videos: list[YoutubeVideo]
    ingest_summary: IngestSummary
    summarization_summary: dict[str, int]
    top_summaries: list[RankedSummary]
