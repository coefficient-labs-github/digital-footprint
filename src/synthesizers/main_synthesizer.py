import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List
from notion_client import Client
from dotenv import load_dotenv
import re
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Load Youtube Questions and Timestamps (todo)

def load_x_posts() -> pd.DataFrame:
    """Load and sort X posts from CSV file."""
    x_handle = os.getenv("PERSON_X_HANDLE")
    if not x_handle:
        return pd.DataFrame()
    csv_path = Path(__file__).parent.parent / "data" / "x_posts" / f"cleaned_{x_handle}.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df = df.sort_values('viewCount', ascending=True)
    return df.head(50)  # Only top 50

def get_linkedin_filename(linkedin_handle: str) -> str:
    username = linkedin_handle.rstrip('/').split('/')[-1]
    safe_username = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    return safe_username

def load_linkedin_posts() -> pd.DataFrame:
    li_handle = os.getenv("PERSON_LI_HANDLE")
    logging.info(f"PERSON_LI_HANDLE: {li_handle}")
    if not li_handle:
        logging.warning("No PERSON_LI_HANDLE set.")
        return pd.DataFrame()
    filename = get_linkedin_filename(li_handle)
    logging.info(f"Sanitized LinkedIn filename: {filename}")
    csv_path = Path(__file__).parent.parent / "data" / "linkedin_posts" / f"cleaned_{filename}.csv"
    logging.info(f"Looking for LinkedIn CSV at: {csv_path}")
    if not csv_path.exists():
        logging.warning(f"File does not exist: {csv_path}")
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    logging.info(f"Loaded {len(df)} rows from {csv_path}")
    df = df.sort_values('total_reactions', ascending=True)
    return df.head(50)

def extract_page_id(url: str) -> str:
    """Extract the page ID from a Notion URL."""
    # Remove any query parameters
    base_url = url.split("?")[0]
    # Get the last part of the URL which is the page ID
    page_id = base_url.split("/")[-1]
    return page_id

def create_x_posts_database(notion: Client, parent_id: str) -> str:
    """Create a database for X posts and return its ID."""
    database = notion.databases.create(
        parent={"page_id": parent_id},
        title=[{"type": "text", "text": {"content": "Top X Posts"}}],
        properties={
            "Post": {"title": {}},  # This will be the main column
            "Views": {"number": {}},
            "Date": {"date": {}},
            "URL": {"url": {}}
        }
    )
    return database["id"]

def create_linkedin_posts_database(notion: Client, parent_id: str) -> str:
    database = notion.databases.create(
        parent={"page_id": parent_id},
        title=[{"type": "text", "text": {"content": "Top LinkedIn Posts"}}],
        properties={
            "Post": {"title": {}},
            "Reactions": {"number": {}},
            "Date": {"date": {}},
            "URL": {"url": {}}
        }
    )
    return database["id"]

def srt_timestamp_to_yt(t):
    """Convert SRT timestamp (e.g., 00:33:20,240) to YouTube &t=33m20s format."""
    try:
        parts = t.split(",")[0].split(":")
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        total_seconds = h * 3600 + m * 60 + s
        m, s = divmod(total_seconds, 60)
        if h > 0:
            return f"{h}h{m}m{s}s"
        elif m > 0:
            return f"{m}m{s}s"
        else:
            return f"{s}s"
    except Exception:
        return "0s"

def update_notion_page():
    """Update the existing Notion page with X and LinkedIn posts."""
    # Initialize Notion client
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    
    # Get the person's name from environment variable
    person_name = os.getenv("PERSON_NAME")
    
    # Get the page ID from the URL
    page_id = extract_page_id(os.getenv("NOTION_PAGE"))
    
    # 1. Set the Notion page title
    notion.pages.update(
        page_id=page_id,
        properties={
            "title": [
                {
                    "type": "text",
                    "text": {"content": f"VC Brief: {person_name}"}
                }
            ]
        }
    )
    
    # 2. Add heading and database for Top X Posts
    notion.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "Top X Posts Database"}
                }]
            }
        }]
    )
    # Create database
    database_id = create_x_posts_database(notion, page_id)
    # Add posts to database
    df = load_x_posts()
    if not df.empty:
        for _, row in df.iterrows():
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Post": {
                        "title": [
                            {
                                "text": {
                                    "content": str(row["text"])[:2000]
                                }
                            }
                        ]
                    },
                    "Views": {"number": int(row["viewCount"])},
                    "Date": {"date": {"start": pd.to_datetime(row["createdAt"]).strftime("%Y-%m-%d")}},
                    "URL": {"url": row["url"]}
                }
            )
    
    # 3. Add heading and database for Top LinkedIn Posts
    notion.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "Top LinkedIn Posts Database"}
                }]
            }
        }]
    )
    li_database_id = create_linkedin_posts_database(notion, page_id)
    li_df = load_linkedin_posts()
    if not li_df.empty:
        for _, row in li_df.iterrows():
            notion.pages.create(
                parent={"database_id": li_database_id},
                properties={
                    "Post": {
                        "title": [
                            {
                                "text": {
                                    "content": str(row["text"])[:2000]
                                }
                            }
                        ]
                    },
                    "Reactions": {"number": int(row["total_reactions"])},
                    "Date": {"date": {"start": pd.to_datetime(row["posted_at"]).strftime("%Y-%m-%d")}},
                    "URL": {"url": row["url"]}
                }
            )
    
    # 4. Add bucketed questions as inline databases (tables)
    notion.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "Questions Asked On Previous Podcasts"}
                }]
            }
        }]
    )
    bucketed_path = Path(__file__).parent.parent / "data" / "transcripts" / "bucketed_questions.json"
    if bucketed_path.exists():
        with open(bucketed_path, "r") as f:
            bucketed = json.load(f)
        for bucket, questions in bucketed.items():
            if not questions:
                continue
            # Add a heading for the bucket
            heading_block = {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": bucket}
                    }]
                }
            }
            notion.blocks.children.append(block_id=page_id, children=[heading_block])
            # Create the inline database (table)
            db = notion.databases.create(
                parent={"page_id": page_id},
                title=[{"type": "text", "text": {"content": f"{bucket}"}}],
                properties={
                    "Question": {"title": {}},
                    "Link": {"url": {}},
                    "Timestamp": {"rich_text": {}},
                    "Video": {"rich_text": {}}
                }
            )
            db_id = db["id"]
            # Add each question as a row
            for q in questions:
                # Add timestamp to the video URL
                ts = q["timestamp"]
                yt_url = q["video_url"]
                if ts and yt_url:
                    t_param = srt_timestamp_to_yt(ts)
                    if "&" in yt_url:
                        yt_url = yt_url + f"&t={t_param}"
                    else:
                        yt_url = yt_url + f"?t={t_param}"
                notion.pages.create(
                    parent={"database_id": db_id},
                    properties={
                        "Question": {
                            "title": [{"text": {"content": q["question"]}}]
                        },
                        "Link": {"url": yt_url},
                        "Timestamp": {"rich_text": [{"text": {"content": q["timestamp"]}}]},
                        "Video": {"rich_text": [{"text": {"content": q["video_title"]}}]}
                    }
                )
    
    return f"https://www.notion.so/{page_id}"

def main():
    """Main function to update the Notion page."""
    try:
        page_url = update_notion_page()
        print(f"Notion page has been updated: {page_url}")
    except Exception as e:
        print(f"Error updating Notion page: {str(e)}")

if __name__ == "__main__":
    main()
