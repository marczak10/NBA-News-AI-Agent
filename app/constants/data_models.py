from datetime import datetime
from pydantic import BaseModel


class ESPNArticle(BaseModel):
    id: str
    title: str
    description: str
    url: str
    published_date: datetime
    content: str
    
    
class YoutubeVideo(BaseModel):
    id: str
    title: str
    description: str
    url: str
    published_date: datetime
    transcript: str | None = None
    

class NBAArticle(BaseModel):
    id: str
    title: str
    description: str
    url: str
    published_date: datetime
    content: str
    

class Summary(BaseModel):
    id: str
    title: str
    source_id: str
    source_type: str
    summary_text: str
    created_at: datetime