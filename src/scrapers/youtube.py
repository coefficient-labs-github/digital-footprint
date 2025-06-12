from typing import Dict, Any, Tuple, Optional
import requests
import time
import json
from dotenv import load_dotenv
import os
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
import logging
from apify_client import ApifyClient

# Load environment variables
load_dotenv()

class YouTubeScraper:
    def __init__(self):
        """Initialize the YouTube scraper."""
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.data_dir = Path("src/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir = self.data_dir / "transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.captions_file = self.transcripts_dir / "youtube_captions.json"

    def search_podcasts(self, person_name: str, company_name: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for podcasts featuring the given person using YouTube Data API.
        
        Args:
            person_name: Name of the person to search for
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing video information including URLs
        """
        try:
            # Construct the search query
            search_query = f"{person_name} {company_name} podcast"
            
            # Make request to YouTube Data API
            url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': self.youtube_api_key,
                'q': search_query,
                'type': 'video',
                'part': 'snippet',
                'maxResults': max_results,
                'relevanceLanguage': 'en'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status() 
            
            data = response.json()
            
            # Transform the response into our desired format
            videos = []
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                video_info = {
                    'title': snippet['title'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'channel': snippet['channelTitle'],
                    'date': snippet['publishedAt'].split('T')[0],  # Convert to YYYY-MM-DD
                    'description': snippet['description'],
                    'video_id': video_id
                }
                videos.append(video_info)
            
            return {'videos': videos}
            
        except Exception as e:
            print(f"Error in search_podcasts: {str(e)}")
            return {"videos": []}

    def get_transcripts(self, APIFY_API_KEY: str, searched_videos: list, title_to_url: dict) -> Dict[str, Any]:
        """Gets transcript for each podcast"""
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_KEY)
        urls = [video['url'] for video in searched_videos]
        print(f"Scraping videos: {urls}")
        
        # Prepare the Actor input - FORMAT URLS CORRECTLY HERE
        run_input = {
            "maxResults": 10,
            "maxResultsShorts": 0,
            "maxResultStreams": 0,
            "startUrls": [{"url": video['url']} for video in searched_videos], 
            "subtitlesLanguage": "any",
            "subtitlesFormat": "srt",
            "downloadSubtitles": True,
            "saveSubsToKVS": False
        }

        # Run the Actor and wait for it to finish
        run = client.actor("h7sDV53CddomktSi5").call(run_input=run_input)

        # Fetch all items from the dataset
        results = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            subtitles = item.get('subtitles', [])
            if isinstance(subtitles, list):
                for sub in subtitles:
                    if 'srt' in sub and isinstance(sub['srt'], str):
                        # Parse SRT into segments
                        sub['segments'] = self.parse_srt(sub['srt'])
                        # Concatenate all segment texts into a single uninterrupted string
                        sub['full_transcript'] = ' '.join(seg['text'] for seg in sub['segments'] if seg['text'])
            results.append(item)
            print(f"Found transcript for: {item.get('title', 'Unknown')}")
        
        # Save results to JSON file
        output_path = self.data_dir / "transcripts" / "youtube_transcripts.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(results)} transcripts to {output_path}")
        
        return results

    def parse_srt(self, srt_str):
        """
        Parses an SRT string into a list of segments with start_time, end_time, and text.
        """
        import re
        segments = []
        srt_blocks = re.split(r'\n\s*\n', srt_str.strip())
        for block in srt_blocks:
            lines = block.strip().splitlines()
            if len(lines) >= 3:
                # SRT index (lines[0])
                # Timestamp line (lines[1])
                match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if match:
                    start_time, end_time = match.groups()
                    text = ' '.join(lines[2:]).strip()
                    segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
        return segments

def main():
    person_name = os.getenv("PERSON_NAME")
    company_name = os.getenv("COMPANY_NAME")
    APIFY_API_KEY = os.getenv("APIFY_API_KEY")
    youtube_scraper = YouTubeScraper()
    searched_videos = youtube_scraper.search_podcasts(person_name, company_name)["videos"]
    title_to_url = {video['title']: video['url'] for video in searched_videos}
    trans = youtube_scraper.get_transcripts(os.getenv("APIFY_API_KEY"), searched_videos, title_to_url)

main()