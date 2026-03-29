import logging
from datetime import datetime, timezone
import time
from typing import Any

from app.scrapers.scrape_espn import ESPNScraper
from app.scrapers.scrape_nba import NBAScraper
from app.scrapers.scrape_youtube import YoutubeScraper
from app.steps.base import State

logger = logging.getLogger(__name__)


def _get_start_time(state: State) -> datetime:
    start_time = state.get("start_time")
    if start_time is None:
        return datetime.now(timezone.utc)
    if start_time.tzinfo is None:
        return start_time.replace(tzinfo=timezone.utc)
    return start_time.astimezone(timezone.utc)


def scrape(state: State, hours: int = 24) -> dict[str, Any]:
    logger.info("Starting scraper step for the last %s hours.", hours)
    scrape_start_time = time.time()
    start_time = _get_start_time(state)

    espn_scraper = ESPNScraper()
    nba_scraper = NBAScraper()
    youtube_scraper = YoutubeScraper()

    espn_articles = espn_scraper.get_articles(hours=hours, reference_time=start_time)
    nba_articles = nba_scraper.get_articles(hours=hours, reference_time=start_time)
    youtube_videos = youtube_scraper.get_videos(hours=hours, reference_time=start_time)
    scrape_end_time = time.time()
    logger.info(
        "Finished scraper step in %.2f seconds. ESPN: %s, NBA: %s, YouTube: %s.",
        scrape_end_time - scrape_start_time,
        len(espn_articles),
        len(nba_articles),
        len(youtube_videos),
    )

    return {
        "start_time": start_time,
        "espn_articles": espn_articles,
        "nba_articles": nba_articles,
        "youtube_videos": youtube_videos,
    }
