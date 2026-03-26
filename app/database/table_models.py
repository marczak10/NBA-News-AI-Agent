from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class NBAArticle(Base):
    __tablename__ = 'nba_articles'
    
    id = Column(String(255), primary_key=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(2048), nullable=False)
    published_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ESPNArticle(Base):
    __tablename__ = 'espn_articles'
    
    id = Column(String(255), primary_key=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(2048), nullable=False)
    published_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
class YoutubeVideo(Base):
    __tablename__ = 'youtube_videos'
    
    id = Column(String(255), primary_key=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(2048), nullable=False)
    published_date = Column(DateTime, nullable=False)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
