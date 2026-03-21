from datetime import datetime, timedelta, timezone
from typing import List
import feedparser
from pydantic import BaseModel


class ESPNArticle(BaseModel):
    guid: str
    title: str
    description: str
    url: str
    published_date: datetime


class ESPNScraper:
    def __init__(self):
        self.rss_url = "https://www.espn.com/espn/rss/nba/news"

    def get_articles(self, hours: int = 24) -> List[ESPNArticle]:
        time_now = datetime.now(tz=timezone.utc)
        time_cutoff = time_now - timedelta(hours=hours)
        articles = []
        feed = feedparser.parse(self.rss_url)
        entries = feed["entries"]

        if not entries:
            return []

        for entry in entries:
            guid = entry["id"]
            title = entry["title"]
            description = entry["summary"]
            url = entry["link"]
            published_date = entry["published_parsed"]
            published_datetime = datetime(*published_date[:6], tzinfo=timezone.utc)

            if published_datetime >= time_cutoff:
                article = ESPNArticle(
                    guid=guid,
                    title=title,
                    description=description,
                    url=url,
                    published_date=published_datetime,
                )
                articles.append(article)

        return articles
