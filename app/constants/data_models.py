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
