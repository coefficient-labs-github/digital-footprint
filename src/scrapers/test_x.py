from x import XScraper
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize scraper
scraper = XScraper()

# Scrape someone
scraper.scrape_x(os.getenv("PERSON_X_HANDLE"))