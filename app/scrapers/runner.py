from scrape_espn import ESPNScraper
from scrape_nba import NBAScraper
from scrape_youtube import YoutubeScraper


def scrape(hours: int = 24):
    espn_scraper = ESPNScraper()
    nba_scraper = NBAScraper()
    youtube_scraper = YoutubeScraper()

    espn_articles = espn_scraper.get_articles(hours=hours)
    nba_articles = nba_scraper.get_articles(hours=hours)
    youtube_videos = youtube_scraper.get_videos(hours=hours)

    return {
        "espn": espn_articles,
        "nba": nba_articles,
        "youtube": youtube_videos,
    }
    
if __name__ == "__main__":
    scraped_data = scrape()
    print(f"Scraped {len(scraped_data['espn'])} ESPN articles")
    print(f"Scraped {len(scraped_data['nba'])} NBA articles")
    print(f"Scraped {len(scraped_data['youtube'])} YouTube videos")