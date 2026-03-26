from typing import Any

from app.scrapers.scrape_espn import ESPNScraper
from app.scrapers.scrape_nba import NBAScraper
from app.scrapers.scrape_youtube import YoutubeScraper
from app.steps.base import State


def scrape(state: State, hours: int = 24) -> dict[str, list[Any]]:
    print("Starting scraping step...")

    espn_scraper = ESPNScraper()
    nba_scraper = NBAScraper()
    youtube_scraper = YoutubeScraper()

    espn_articles = espn_scraper.get_articles(hours=hours)
    nba_articles = nba_scraper.get_articles(hours=hours)
    youtube_videos = youtube_scraper.get_videos(hours=hours)
    
    print(f"Scraped {len(espn_articles)} articles from ESPN, {len(nba_articles)} articles from NBA, and {len(youtube_videos)} videos from YouTube.")

    return {
        "espn_articles": espn_articles,
        "nba_articles": nba_articles,
        "youtube_videos": youtube_videos,
    }
