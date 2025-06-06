from linkedin import LinkedInScraper
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == "__main__":
    scraper = LinkedInScraper()
    scraper.format_linkedin_data(max_posts=50)