from apify_client import ApifyClient
import logging
from dotenv import load_dotenv
import os
import json
from pathlib import Path
import pandas as pd

# Load environment variables
load_dotenv()

class XScraper:
    def __init__(self):
        """Initialize LinkedIn Scraper"""
        self.apify_api_key = os.getenv("APIFY_API_KEY")
        self.output_dir = Path("src/data/x_posts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO)

    def scrape_x(self, x_handle: str):
        # Initialize the ApifyClient with your API token
        client = ApifyClient(self.apify_api_key)
        logging.info(f"Starting scrape for X handle: {x_handle}")

        # Prepare the Actor input
        run_input = {
            "twitterHandles": [x_handle],
            "sort": "Latest",
            "maxItems": 1000,
        }

        # Run the Actor and wait for it to finish
        run = client.actor("nfp1fpt5gUlBwPcor").call(run_input=run_input)
        logging.info(f"Actor run complete. Fetching results for {x_handle}")

        # Fetch Actor results from the run's dataset (if there are any)
        posts = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            posts.append(item)
        logging.info(f"Fetched {len(posts)} posts for {x_handle}")

        # Save to JSON file
        output_path = self.output_dir / f"{x_handle}.json"
        with open(output_path, "w") as f:
            json.dump(posts, f, indent=2)
        logging.info(f"Saved posts to {output_path}")

        return None

    def format_x_data(self, max_posts=50):
        x_handle = os.getenv("PERSON_X_HANDLE")
        if not x_handle:
            logging.error("PERSON_X_HANDLE environment variable not set.")
            return

        json_path = self.output_dir / f"{x_handle}.json"
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
                "createdAt": post.get("createdAt"),
                "viewCount": post.get("viewCount", 0)
            })

        # Sort and select top posts
        df = pd.DataFrame(rows)
        df = df.sort_values(by="viewCount", ascending=False).head(max_posts)

        # Save to CSV
        cleaned_path = self.output_dir / f"cleaned_{x_handle}.csv"
        df.to_csv(cleaned_path, index=False)
        logging.info(f"Saved cleaned data to {cleaned_path}")