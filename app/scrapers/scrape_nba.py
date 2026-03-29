from datetime import datetime, timedelta, timezone
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.constants.links import NBA_TOP_STORIES_URL
from app.constants.data_models import NBAArticle

logger = logging.getLogger(__name__)


class NBAScraper:
    BASE_URL = "https://www.nba.com"
    DEFAULT_TIMEOUT = 20
    DEFAULT_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nba.com/",
        "Connection": "keep-alive",
    }
    ISO_DATETIME_RE = re.compile(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
    )
    TEXT_DATETIME_PATTERNS = (
        re.compile(
            r"(?:Updated|Published)\s+on\s+"
            r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:Updated|Published)\s*:?\s*"
            r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)",
            re.IGNORECASE,
        ),
    )
    TEXT_DATETIME_FORMATS = (
        "%B %d, %Y %I:%M %p",
        "%b %d, %Y %I:%M %p",
        "%B %d, %Y",
        "%b %d, %Y",
    )

    def __init__(self):
        self.news_link = NBA_TOP_STORIES_URL
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.session.headers.update({"User-Agent": self._get_user_agent()})

    def _get_user_agent(self) -> str:
        return (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )

    def _get_html(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            logger.warning("Could not fetch NBA content from %s: %s", url, exc)
            return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        html = self._get_html(url)
        if html is None:
            return None
        return self._parse_html(html)

    def _get_article_urls(self, category_url: str) -> List[str]:
        urls: List[str] = []

        candidate_pages = [
            category_url,
            f"{category_url.rstrip('/')}/page/2",
            f"{category_url}?page=2",
        ]

        for page_url in candidate_pages:
            page_urls = self._get_article_urls_from_page(page_url)

            new_urls = 0
            for url in page_urls:
                urls.append(url)
                new_urls += 1

            if page_url != candidate_pages[0] and new_urls == 0:
                break

        return urls

    def _get_article_urls_from_page(self, page_url: str) -> List[str]:
        soup = self._get_soup(page_url)
        if soup is None:
            return []

        urls = self._extract_article_urls_from_ld_json(soup)
        if urls:
            return urls

        return self._extract_article_urls_from_anchors(soup)

    def _get_article(self, article_url: str) -> Optional[NBAArticle]:
        soup = self._get_soup(article_url)
        if soup is None:
            return None

        article_data = self._extract_article_data_from_ld_json(soup) or {}
        title = self._get_article_title(soup, article_data)
        description = self._get_article_description(soup, article_data)
        published_date = self._get_article_datetime(soup, article_data)
        content = self._get_article_content(soup, article_data)

        if not title or published_date is None:
            return None

        normalized_url = self._normalize_url(article_url)
        if normalized_url is None:
            return None

        return NBAArticle(
            id=self._article_id_from_url(normalized_url),
            title=title,
            description=description,
            url=normalized_url,
            published_date=published_date,
            content=content,
        )

    def _get_article_title(
        self, soup: BeautifulSoup, article_data: dict[str, Any]
    ) -> str:
        return self._first_non_empty_text(
            (
                article_data.get("headline"),
                self._meta_content(soup, property_name="og:title"),
                self._meta_content(soup, name="twitter:title"),
                self._first_text(soup, ["h1"]),
            )
        )

    def _get_article_description(
        self, soup: BeautifulSoup, article_data: dict[str, Any]
    ) -> str:
        return self._first_non_empty_text(
            (
                article_data.get("description"),
                self._meta_content(soup, property_name="og:description"),
                self._meta_content(soup, name="description"),
                self._meta_content(soup, name="twitter:description"),
            )
        )

    def _get_article_datetime(
        self,
        soup: BeautifulSoup,
        article_data: dict[str, Any],
    ) -> Optional[datetime]:
        datetime_candidates = [
            article_data.get("dateModified"),
            article_data.get("datePublished"),
            self._meta_content(soup, property_name="article:modified_time"),
            self._meta_content(soup, property_name="article:published_time"),
            self._meta_content(soup, name="date"),
            self._meta_content(soup, itemprop="dateModified"),
            self._meta_content(soup, itemprop="datePublished"),
        ]

        datetime_candidates.extend(
            tag["datetime"] for tag in soup.find_all("time") if tag.has_attr("datetime")
        )

        visible_text = soup.get_text(" ", strip=True)
        for pattern in self.TEXT_DATETIME_PATTERNS:
            match = pattern.search(visible_text)
            if match:
                datetime_candidates.append(match.group(1))

        parsed_datetime = self._first_parsed_datetime(datetime_candidates)
        if parsed_datetime is not None:
            return parsed_datetime

        iso_match = self.ISO_DATETIME_RE.search(str(article_data))
        if iso_match:
            return self._parse_datetime(iso_match.group(0))

        return None

    def _get_article_content(
        self, soup: BeautifulSoup, article_data: dict[str, Any]
    ) -> str:
        structured_body = article_data.get("articleBody")
        if isinstance(structured_body, str):
            cleaned = self._clean_text(structured_body)
            if cleaned:
                return cleaned

        candidate_roots = (
            "div[class*='ArticleContent_article']",
            "article",
            "main",
        )
        for selector in candidate_roots:
            container = soup.select_one(selector)
            content = self._extract_content_from_container(container)
            if content:
                return content

        return ""

    def _extract_article_urls_from_ld_json(self, soup: BeautifulSoup) -> List[str]:
        candidates = (
            candidate
            for data in self._iter_ld_json_objects(soup)
            for candidate in self._find_urls_in_structured_data(data)
        )
        return self._filter_article_urls(candidates)

    def _extract_article_urls_from_anchors(self, soup: BeautifulSoup) -> List[str]:
        candidates = (anchor.get("href") for anchor in soup.select("a[href]"))
        return self._filter_article_urls(candidates)

    def _extract_article_data_from_ld_json(
        self, soup: BeautifulSoup
    ) -> Optional[dict[str, Any]]:
        article_types = {"NewsArticle", "Article", "ReportageNewsArticle"}

        for data in self._iter_ld_json_objects(soup):
            for obj in self._walk_json(data):
                if not isinstance(obj, dict):
                    continue

                obj_type = obj.get("@type")
                if isinstance(obj_type, list):
                    matches = any(item in article_types for item in obj_type)
                else:
                    matches = obj_type in article_types

                if matches:
                    return obj

        return None

    def _extract_content_from_container(self, container: Optional[Tag]) -> str:
        if container is None:
            return ""

        blocks: List[str] = []
        for element in container.select("p, li"):
            if element.find_parent(["aside", "nav", "footer"]):
                continue

            classes = element.get("class") or []
            if any("caption" in class_name.lower() for class_name in classes):
                continue

            text = self._clean_text(element.get_text(" ", strip=True))
            if not text:
                continue

            blocks.append(text)

        if blocks:
            return "\n\n".join(blocks)

        return self._clean_text(container.get_text(" ", strip=True))

    def _iter_ld_json_objects(self, soup: BeautifulSoup) -> Iterable[Any]:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw_text = script.string or script.get_text(strip=True)
            if not raw_text:
                continue

            cleaned = raw_text.strip()
            try:
                yield json.loads(cleaned)
                continue
            except json.JSONDecodeError:
                pass

            for match in re.finditer(r"\{.*?\}", cleaned, re.DOTALL):
                snippet = match.group(0)
                try:
                    yield json.loads(snippet)
                except json.JSONDecodeError:
                    continue

    def _find_urls_in_structured_data(self, data: Any) -> Iterable[str]:
        for obj in self._walk_json(data):
            if not isinstance(obj, dict):
                continue

            for key in ("url", "@id"):
                value = obj.get(key)
                if isinstance(value, str):
                    yield value

            if isinstance(obj.get("item"), dict):
                item_url = obj["item"].get("url")
                if isinstance(item_url, str):
                    yield item_url

    def _filter_article_urls(self, candidates: Iterable[Optional[str]]) -> List[str]:
        urls: List[str] = []

        for candidate in candidates:
            normalized = self._normalize_url(candidate)
            if not normalized:
                continue
            if not self._looks_like_article_url(normalized):
                continue

            urls.append(normalized)

        return urls

    def _walk_json(self, data: Any) -> Iterable[Any]:
        if isinstance(data, dict):
            yield data
            for value in data.values():
                yield from self._walk_json(value)
        elif isinstance(data, list):
            for item in data:
                yield from self._walk_json(item)

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return self._ensure_utc(value)

        text = self._clean_text(str(value))
        if not text:
            return None

        text = text.replace("Z", "+00:00")
        iso_match = self.ISO_DATETIME_RE.search(text)
        if iso_match:
            iso_text = iso_match.group(0).replace("Z", "+00:00")
            try:
                return self._ensure_utc(datetime.fromisoformat(iso_text))
            except ValueError:
                pass

        for fmt in self.TEXT_DATETIME_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return None

    def _ensure_utc(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _meta_content(
        self,
        soup: BeautifulSoup,
        *,
        name: Optional[str] = None,
        property_name: Optional[str] = None,
        itemprop: Optional[str] = None,
    ) -> Optional[str]:
        attrs = {
            key: value
            for key, value in (
                ("name", name),
                ("property", property_name),
                ("itemprop", itemprop),
            )
            if value is not None
        }
        if not attrs:
            return None

        tag = soup.find("meta", attrs=attrs)
        if tag and tag.has_attr("content"):
            return str(tag["content"])
        return None

    def _first_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                text = self._clean_text(tag.get_text(" ", strip=True))
                if text:
                    return text
        return None

    def _first_non_empty_text(self, candidates: Iterable[Optional[str]]) -> str:
        for candidate in candidates:
            cleaned = self._clean_text(candidate)
            if cleaned:
                return cleaned
        return ""

    def _first_parsed_datetime(self, candidates: Iterable[Any]) -> Optional[datetime]:
        for candidate in candidates:
            parsed = self._parse_datetime(candidate)
            if parsed is not None:
                return parsed
        return None

    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None

        absolute_url = urljoin(self.BASE_URL, url.strip())
        parsed = urlparse(absolute_url)

        if not parsed.scheme.startswith("http"):
            return None
        if "nba.com" not in parsed.netloc:
            return None

        normalized_path = parsed.path.rstrip("/")
        if not normalized_path:
            return None

        return f"{parsed.scheme}://{parsed.netloc}{normalized_path}"

    def _looks_like_article_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        if not path.startswith("/news/"):
            return False
        if path.startswith("/news/category"):
            return False

        slug = path.split("/")[-1]
        if not slug or slug in {"news", "home"}:
            return False

        excluded_prefixes = (
            "/news/author/",
            "/news/tag/",
            "/news/archive",
            "/news/writer-archive",
            "/news/newsletters",
        )
        if any(path.startswith(prefix) for prefix in excluded_prefixes):
            return False

        return True

    def _article_id_from_url(self, url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        return path.split("/")[-1]

    def _clean_text(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", " ", value).strip()

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
    ) -> List[NBAArticle]:
        time_cutoff = self._get_reference_time(reference_time) - timedelta(hours=hours)
        articles: List[NBAArticle] = []

        article_urls = self._get_article_urls(self.news_link)
        for article_url in article_urls:
            article = self._get_article(article_url)
            if article is None:
                continue

            if self._ensure_utc(article.published_date) < time_cutoff:
                continue

            articles.append(article)

        logger.debug(
            "Collected %s NBA articles from the last %s hours.",
            len(articles),
            hours,
        )
        return articles
