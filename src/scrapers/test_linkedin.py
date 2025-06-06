from linkedin import LinkedInScraper
from dotenv import load_dotenv
import os
import re

load_dotenv()

if __name__ == "__main__":
    li_handle = os.getenv("PERSON_LI_HANDLE")
    if not li_handle:
        print("PERSON_LI_HANDLE environment variable not set.")
    else:
        scraper = LinkedInScraper()
        scraper.scrape_linkedin(li_handle) 