from typing import TypedDict
from app.database.table_models import NBAArticle, ESPNArticle, YoutubeVideo

class UpsertCounts(TypedDict):
    inserted: int
    updated: int

class IngestSummary(TypedDict):
    nba_articles: UpsertCounts
    espn_articles: UpsertCounts
    youtube_videos: UpsertCounts

class State(TypedDict, total=False):
    nba_articles: list[NBAArticle]
    espn_articles: list[ESPNArticle]
    youtube_videos: list[YoutubeVideo]
    ingest_summary: IngestSummary
