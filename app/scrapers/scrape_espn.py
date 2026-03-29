from datetime import datetime, timedelta, timezone
import logging
import sys
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
import feedparser
import requests


if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.constants.links import ESPN_RSS_URL
from app.constants.data_models import ESPNArticle

logger = logging.getLogger(__name__)


class ESPNScraper:
    def __init__(self):
        self.rss_url = ESPN_RSS_URL

    def _get_user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def _get_html(self, url: str) -> str:
        headers = {"User-Agent": self._get_user_agent()}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        return soup

    def _get_article_text(self, soup: BeautifulSoup) -> str:
        content_div = soup.find("div", class_="article-body")
        if content_div:
            return content_div.get_text(" ", strip=True)
        return ""

    def _get_article_content(self, text) -> str:
        if "Content:" in text:
            return text.split("Content:", 1)[1].strip()
        return text.strip()

    def _get_reference_time(self, reference_time: Optional[datetime]) -> datetime:
        if reference_time is None:
            return datetime.now(tz=timezone.utc)
        if reference_time.tzinfo is None:
            return reference_time.replace(tzinfo=timezone.utc)
        return reference_time.astimezone(timezone.utc)

    def get_articles(
        self,
        hours: int = 24,
        reference_time: Optional[datetime] = None,
    ) -> List[ESPNArticle]:
        time_cutoff = self._get_reference_time(reference_time) - timedelta(hours=hours)
        articles = []
        feed = feedparser.parse(self.rss_url)
        entries = feed["entries"]

        if not entries:
            logger.warning("No ESPN RSS entries were found at %s.", self.rss_url)
            return []

        for entry in entries:
            guid = entry["id"]
            title = entry["title"]
            description = entry["summary"]
            url = entry["link"]
            published_date = entry["published_parsed"]
            published_datetime = datetime(*published_date[:6], tzinfo=timezone.utc)

            if published_datetime <= time_cutoff:
                continue
            html = self._get_html(url)
            soup = self._parse_html(html)
            text = self._get_article_text(soup)
            content = self._get_article_content(text)

            article = ESPNArticle(
                id=guid,
                title=title,
                description=description,
                url=url,
                published_date=published_datetime,
                content=content,
            )
            articles.append(article)

        logger.debug(
            "Collected %s ESPN articles from the last %s hours.",
            len(articles),
            hours,
        )
        return articles
