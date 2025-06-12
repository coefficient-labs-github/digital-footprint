import os
import logging
from dotenv import load_dotenv
from scrapers.x import XScraper
from scrapers.linkedin import LinkedInScraper
from synthesizers.main_synthesizer import main as notion_main
from scrapers.youtube import YouTubeScraper
from synthesizers.questions_synthesizer import extract_and_bucket_questions_from_segments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    load_dotenv()
    person_name = os.getenv("PERSON_NAME")
    company_name = os.getenv("COMPANY_NAME")
    APIFY_API_KEY = os.getenv("APIFY_API_KEY")
    logging.info(f"Loaded PERSON_NAME: {person_name}")
    if not person_name:
        raise ValueError("PERSON_NAME environment variable is required")

    # 1. Scrape YouTube podcasts and transcripts
    logging.info("Scraping YouTube podcasts and transcripts...")
    youtube_scraper = YouTubeScraper()
    searched_videos = youtube_scraper.search_podcasts(person_name, company_name)["videos"]
    title_to_url = {video['title']: video['url'] for video in searched_videos}
    youtube_scraper.get_transcripts(APIFY_API_KEY, searched_videos, title_to_url)
    logging.info("YouTube scraping complete.")

    # 2. Extract and bucket questions from transcripts
    logging.info("Extracting and bucketing questions from transcripts...")
    extract_and_bucket_questions_from_segments()
    logging.info("Question extraction and bucketing complete.")

    # 3. Scrape X
    logging.info("Scraping X...")
    x_scraper = XScraper()
    x_scraper.scrape()
    logging.info("X scraping complete.")

    # 4. Scrape LinkedIn
    logging.info("Scraping LinkedIn...")
    linkedin_scraper = LinkedInScraper()
    linkedin_scraper.scrape()
    logging.info("LinkedIn scraping complete.")

    # 5. Synthesize Notion Page
    logging.info("Synthesizing Notion page...")
    notion_main()
    logging.info("Notion page synthesis complete.")

if __name__ == "__main__":
    main()