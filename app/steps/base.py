from datetime import datetime
from typing import TypedDict

from app.constants.data_models import ESPNArticle, NBAArticle, YoutubeVideo


class UpsertCounts(TypedDict):
    inserted: int
    updated: int


class IngestSummary(TypedDict):
    nba_articles: UpsertCounts
    espn_articles: UpsertCounts
    youtube_videos: UpsertCounts


class State(TypedDict, total=False):
    start_time: datetime
    nba_articles: list[NBAArticle]
    espn_articles: list[ESPNArticle]
    youtube_videos: list[YoutubeVideo]
    ingest_summary: IngestSummary
    summarization_summary: dict[str, int]
    ranked_summaries: list[dict[str, str]]
