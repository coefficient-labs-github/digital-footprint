import os
import logging
from dotenv import load_dotenv
from scrapers.x_scraper import XScraper
from scrapers.linkedin_scraper import LinkedInScraper
from synthesizers.main_synthesizer import main as notion_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    load_dotenv()
    person_name = os.getenv("PERSON_NAME")
    logging.info(f"Loaded PERSON_NAME: {person_name}")
    if not person_name:
        raise ValueError("PERSON_NAME environment variable is required")

    # Scrape X
    logging.info("Scraping X...")
    x_scraper = XScraper()
    x_scraper.scrape()
    logging.info("X scraping complete.")

    # Scrape LinkedIn
    logging.info("Scraping LinkedIn...")
    linkedin_scraper = LinkedInScraper()
    linkedin_scraper.scrape()
    logging.info("LinkedIn scraping complete.")

    # Synthesize Notion Page
    logging.info("Synthesizing Notion page...")
    notion_main()
    logging.info("Notion page synthesis complete.")

if __name__ == "__main__":
    main()