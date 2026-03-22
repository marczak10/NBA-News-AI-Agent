from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pathlib import Path
import sys
import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.constants.user_profile import CHANNEL_LINKS


class YoutubeVideo(BaseModel):
    id: str
    title: str
    description: str
    url: str
    published_date: datetime
    transcript: str | None = None


class YoutubeScraper:
    def __init__(self):
        self.channel_links = CHANNEL_LINKS
        self.transcript_api = YouTubeTranscriptApi()

    def _get_transcript(self, video_id: str) -> Optional[str]:
        try:
            fetched_transcript = self.transcript_api.fetch(video_id=video_id)
            transcript = "".join(
                [snippet.text for snippet in fetched_transcript.snippets]
            )
            return transcript
        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception:
            return None

    def _get_rss_url(self, channel_url: str) -> str:
        channel_id = channel_url.split("/")[-1]
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        return rss_url

    def get_videos(self, hours: int = 24) -> List[YoutubeVideo]:
        time_now = datetime.now(tz=timezone.utc)
        time_cutoff = time_now - timedelta(hours=hours)
        videos = []
        for channel_url in self.channel_links:
            rss_url = self._get_rss_url(channel_url)
            feed = feedparser.parse(rss_url)
            entries = feed["entries"]

            if not entries:
                continue
            for entry in entries:
                video_id = entry["yt_videoid"]
                title = entry["title"]
                description = entry["summary"]
                url = entry["link"]
                published_date = entry["published_parsed"]
                published_datetime = datetime(*published_date[:6], tzinfo=timezone.utc)

                if published_datetime <= time_cutoff and "/shorts/" in url:
                    continue

                transcript = self._get_transcript(video_id)
                videos.append(
                    YoutubeVideo(
                        id=video_id,
                        title=title,
                        description=description,
                        url=url,
                        published_date=published_datetime,
                        transcript=transcript,
                    )
                )

        return videos


if __name__ == "__main__":
    scraper = YoutubeScraper()
    videos = scraper.get_videos()
    print(videos)
