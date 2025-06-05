import os
import json
import time
from typing import List
from dotenv import load_dotenv
from data.storage import DataStorage
from scrapers.youtube import YouTubeScraper
from youtube_transcript_api import YouTubeTranscriptApi
#from scrapers.linkedin import LinkedInScraper
#from scrapers.twitter import TwitterScraper
#from processors.transcript import TranscriptProcessor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main(person_name: str, person_li_url: str):
    # Initialize storage
    storage = DataStorage()
    
    # Initialize scrapers
    youtube_scraper = YouTubeScraper()
    ytt_api = YouTubeTranscriptApi()
    #linkedin_scraper = LinkedInScraper()
    #twitter_scraper = TwitterScraper()
    
    logging.info(f"Collecting content for {person_name}...")
    
    ### YouTube
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
    youtube_links = storage.load_links("youtube")
    
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