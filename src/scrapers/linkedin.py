from apify_client import ApifyClient
import logging
from dotenv import load_dotenv
import os
import json
from pathlib import Path
import pandas as pd
import re

# Load environment variables
load_dotenv()

class LinkedInScraper:
    def __init__(self):
        """Initialize LinkedIn Scraper"""
        self.apify_api_key = os.getenv("APIFY_API_KEY")
        self.output_dir = Path("src/data/linkedin_posts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO)

    def scrape_linkedin(self, linkedin_handle: str):
        # Initialize the ApifyClient with your API token
        client = ApifyClient(self.apify_api_key)
        logging.info(f"Starting scrape for LinkedIn handle: {linkedin_handle}")

        # Prepare the Actor input
        run_input = {
            "username": linkedin_handle,
            "page_number": 1,
            "limit": 100,
        }

        # Run the Actor and wait for it to finish
        run = client.actor("LQQIXN9Othf8f7R5n").call(run_input=run_input)
        logging.info(f"Actor run complete. Fetching results for {linkedin_handle}")

        # Fetch Actor results from the run's dataset (if there are any)
        posts = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            posts.append(item)
        logging.info(f"Fetched {len(posts)} posts for {linkedin_handle}")

        # Save to JSON file
        filename = self.get_linkedin_filename(linkedin_handle)
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, "w") as f:
            json.dump(posts, f, indent=2)
        logging.info(f"Saved posts to {output_path}")

        return None

    def format_linkedin_data(self, max_posts=50):
        li_handle = os.getenv("PERSON_LI_HANDLE")
        print(li_handle)
        if not li_handle:
            logging.error("PERSON_LI_HANDLE environment variable not set.")
            return

        username = li_handle.rstrip('/').split('/')[-1]
        json_path = self.output_dir / f"{username}.json"
        if not json_path.exists():
            logging.error(f"File {json_path} does not exist.")
            return

        with open(json_path, "r") as f:
            posts = json.load(f)

        # Extract relevant fields
        rows = []
        for post in posts:
            rows.append({
                "url": post.get("url"),
                "text": post.get("text"),
                "posted_at": post.get("posted_at", {}).get("date"),
                "total_reactions": post.get("stats", {}).get("total_reactions", 0)
            })

        # Sort and select top posts
        df = pd.DataFrame(rows)
        df = df.sort_values(by="total_reactions", ascending=False).head(max_posts)

        # Save to CSV
        cleaned_path = self.output_dir / f"cleaned_{username}.csv"
        df.to_csv(cleaned_path, index=False)
        logging.info(f"Saved cleaned data to {cleaned_path}")

    @staticmethod
    def get_linkedin_filename(linkedin_handle):
        # Extract the last part after the last slash, ignoring trailing slashes
        username = linkedin_handle.rstrip('/').split('/')[-1]
        # Allow only alphanumeric, dash, and underscore
        safe_username = re.sub(r'[^a-zA-Z0-9_-]', '', username)
        return safe_username