import os
import json
import time
from typing import List
from dotenv import load_dotenv
from scrapers.youtube import YouTubeScraper
from youtube_transcript_api import YouTubeTranscriptApi
from synthesizers.transcripts_to_questions import process_transcripts
from scrapers.linkedin import LinkedInScraper
from scrapers.x import XScraper
import logging
from synthesizers.main_synthesizer import main as notion_main
from synthesizers.questions_synthesizer import synthesize_buckets_if_needed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def youtube_process(youtube_scraper, person_name):
    logging.info(f"[YouTube] Searching for podcasts featuring: {person_name}")
    youtube_links = youtube_scraper.search_podcasts(person_name)["videos"]
    logging.info(f"Found {len(youtube_links)} initial YouTube videos for {person_name}")
    
    # Use only the first two words of person_name for matching
    person_name_words = person_name.split()
    person_name_short = ' '.join(person_name_words[:2]).lower() if len(person_name_words) >= 2 else person_name.lower()
    logging.info(f"Filtering YouTube videos using short name: '{person_name_short}'")
    
    # Filter for links that contain the first two words of the person's name in either title or description
    youtube_links = [
        link for link in youtube_links
        if person_name_short in link["title"].lower() or person_name_short in link["description"].lower()
    ]
    logging.info(f"Filtered down to {len(youtube_links)} relevant YouTube videos for {person_name}")
    
    if youtube_links:
        logging.info(f"Video titles: {[link['title'] for link in youtube_links[:3]]}")
    else:
        logging.warning(f"No relevant YouTube videos found for {person_name}")

    # Dictionary to store all transcripts
    transcripts_data = {}
    
    # Get transcripts for each link
    for link in youtube_links:
        vid = link["video_id"]
        logging.info(f"Attempting to get transcript for video {vid} ({link['title']})")
        
        # Try to get transcript with retry logic
        transcript, language = youtube_scraper.get_transcript_with_retry(vid)
        
        if transcript:
            # Store transcript with metadata
            transcripts_data[vid] = {
                "title": link["title"],
                "channel": link["channel"],
                "date": link["date"],
                "transcript": transcript,
                "language": language
            }
            logging.info(f"Successfully retrieved transcript for video {vid}")
        else:
            logging.warning(f"Failed to get transcript for video {vid} after all retry attempts")
    
    # Save all transcripts to JSON file
    if transcripts_data:
        youtube_scraper.save_transcripts_to_json(transcripts_data)
        logging.info(f"Successfully processed {len(transcripts_data)} transcripts for {person_name}")
    else:
        logging.warning(f"No transcripts were successfully processed for {person_name}")

def linkedin_process(person_name):
    li_handle = os.getenv("PERSON_LI_HANDLE")
    logging.info(f"[LinkedIn] Using PERSON_LI_HANDLE: {li_handle} for {person_name}")
    if not li_handle:
        print("PERSON_LI_HANDLE environment variable not set.")
    else:
        scraper = LinkedInScraper()
        scraper.scrape_linkedin(li_handle) 
    scraper.format_linkedin_data(max_posts=50)

def x_process(person_name):
    x_handle = os.getenv("PERSON_X_HANDLE")
    logging.info(f"[X] Using PERSON_X_HANDLE: {x_handle} for {person_name}")
    # Initialize scraper
    scraper = XScraper()
    # Scrape all tweets from PERSON_X_HANDLE (env variable) --> data/x_posts/{{PERSON_X_HANDLE}}.json
    scraper.scrape_x(x_handle)
    # Format data/x_posts/{{PERSON_X_HANDLE}}.json into a cleaned csv, data/x_posts/cleaned{{PERSON_X_HANDLE}}.csv
    scraper.format_x_data()

def main(person_name: str):
    logging.info(f"Collecting content for {person_name}...")
    
    # Scrape YouTube transcripts
    logging.info("Starting YouTube process...")
    youtube_scraper = YouTubeScraper()
    youtube_process(youtube_scraper, person_name)

    # Synthesize youtube transcripts into questions
    logging.info("Synthesizing transcripts into questions...")
    process_transcripts()
    logging.info("Successfully generated questions from transcripts")
    logging.info("YouTube process complete")

    # Synthesize and bucket questions if needed
    logging.info("Synthesizing and bucketing questions if needed...")
    synthesize_buckets_if_needed()
    logging.info("Question bucketing complete.")

    # Scrape and synthesize Linkedin
    logging.info("Starting LinkedIn process...")
    linkedin_process(person_name)
    logging.info("LinkedIn process complete.")

    # Scrape and synthesize X
    logging.info("Starting X process..")
    x_process(person_name)
    logging.info("X process complete..")

    # Synthesize Notion Page
    logging.info("Synthesizing Notion page...")
    notion_main()
    logging.info("Notion page synthesis complete.")
    
if __name__ == "__main__":
    load_dotenv()
    person_name = os.getenv("PERSON_NAME")
    logging.info(f"Loaded PERSON_NAME: {person_name}")
    if not person_name:
        raise ValueError("PERSON_NAME environment variable is required")
    main(person_name) 