import os
from typing import List
from dotenv import load_dotenv
from data.storage import DataStorage
from scrapers.youtube import YouTubeScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.twitter import TwitterScraper
from processors.transcript import TranscriptProcessor

def main(person_name: str):
    # Initialize storage
    storage = DataStorage()
    
    # Initialize scrapers
    youtube_scraper = YouTubeScraper()
    linkedin_scraper = LinkedInScraper()
    twitter_scraper = TwitterScraper()
    
    # Step 1: Collect links from different platforms
    print(f"Collecting content for {person_name}...")
    
    # YouTube
    youtube_links = youtube_scraper.search_podcasts(person_name)
    storage.save_links("youtube", youtube_links)
    
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

if __name__ == "__main__":
    load_dotenv()
    person_name = os.getenv("PERSON_NAME")
    if not person_name:
        raise ValueError("PERSON_NAME environment variable is required")
    main(person_name) 