from scrapers.youtube import YouTubeScraper
import json
from pprint import pprint

def test_youtube_scraper():
    # Initialize the scraper
    scraper = YouTubeScraper()
    
    # Search for podcasts
    person_name = "Sean Goldfaden"
    print(f"\nSearching for podcasts featuring {person_name}...")
    search_results = scraper.search_podcasts(person_name, max_results=5)

    print("\nFound videos:")
    for video in search_results["videos"]:
        print(f"\nTitle: {video['title']}")
        print(f"URL: {video['url']}")
        
        transcript_result = scraper.get_transcript(video["video_id"])
        if transcript_result.get('error'):
            print(f"Error: {transcript_result['error']}")
        else:
            print("Successfully retrieved transcript")
            print(f"Transcript length: {len(transcript_result['transcript'])} characters")
            print("First 200 characters of transcript:")
            print(transcript_result['transcript'][:200] + "...")

if __name__ == "__main__":
    test_youtube_scraper()