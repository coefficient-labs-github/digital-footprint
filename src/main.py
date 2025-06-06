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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def youtube_process(youtube_scraper):
    logging.info(f"Searching YouTube for podcasts featuring {person_name}")
    youtube_links = youtube_scraper.search_podcasts(person_name)["videos"]
    logging.info(f"Found {len(youtube_links)} initial YouTube videos")
    
    # Filter for links that contain the person's name in either title or description
    youtube_links = [
        link for link in youtube_links
        if person_name.lower() in link["title"].lower() or person_name.lower() in link["description"].lower()
    ]
    logging.info(f"Filtered down to {len(youtube_links)} relevant YouTube videos")
    
    if youtube_links:
        logging.info(f"Video titles: {[link['title'] for link in youtube_links[:3]]}")
    else:
        logging.warning(f"No relevant YouTube videos found for {person_name}")

    # Dictionary to store all transcripts
    transcripts_data = {}
    
    # Get transcripts for each link
    for link in youtube_links:
        vid = link["video_id"]
        logging.info(f"Attempting to get transcript for video {vid}")
        
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
        logging.info(f"Successfully processed {len(transcripts_data)} transcripts")
    else:
        logging.warning("No transcripts were successfully processed")

def linkedin_process():
    li_handle = os.getenv("PERSON_LI_HANDLE")
    if not li_handle:
        print("PERSON_LI_HANDLE environment variable not set.")
    else:
        scraper = LinkedInScraper()
        scraper.scrape_linkedin(li_handle) 
    scraper.format_linkedin_data(max_posts=50)

def x_process():
    # Initialize scraper
    scraper = XScraper()

    # Scrape all tweets from PERSON_X_HANDLE (env variable) --> data/x_posts/{{PERSON_X_HANDLE}}.json
    scraper.scrape_x(os.getenv("PERSON_X_HANDLE"))

    # Format data/x_posts/{{PERSON_X_HANDLE}}.json into a cleaned csv, data/x_posts/cleaned{{PERSON_X_HANDLE}}.csv
    scraper.format_x_data()

def main(person_name: str):    
    logging.info(f"Collecting content for {person_name}...")
    
    # Scrape YouTube transcripts
    logging.info("Starting YouTube process...")
    youtube_scraper = YouTubeScraper()
    youtube_process(youtube_scraper)

    # Synthesize youtube transcripts into questions
    logging.info("Synthesizing transcripts into questions...")
    process_transcripts()
    logging.info("Successfully generated questions from transcripts")
    logging.info("YouTube process complete")

    # Scrape and synthesize Linkedin
    logging.info("Starting LinkedIn process...")
    linkedin_process()
    logging.info("LinkedIn process complete.")

    # Scrape and synthesize X
    logging.info("Starting X process..")
    x_process()
    logging.info("X process complete..")

    # Snythesize document


"""
    # LinkedIn
    linkedin_links = linkedin_scraper.search_posts(person_name)
    storage.save_links("linkedin", linkedin_links)
    
    # Twitter
    twitter_links = twitter_scraper.search_posts(person_name)
    storage.save_links("twitter", twitter_links)
    
    # Step 2: Process YouTube transcripts
    print("Processing YouTube transcripts...")
    transcript_processor = TranscriptProcessor()
    youtube_links = storage.load_links("youtube") d
    
    for video_id in youtube_links:
        if not storage.load_transcript(video_id):
            transcript = transcript_processor.get_transcript(video_id)
            storage.save_transcript(video_id, transcript)
    
    print("Processing complete!")
"""
if __name__ == "__main__":
    load_dotenv()
    person_name = os.getenv("PERSON_NAME")
    person_li_url = os.getenv("PERSON_LI_URL")
    if not person_name:
        raise ValueError("PERSON_NAME environment variable is required")
    main(person_name, person_li_url) 