from typing import List, Dict, Any
import re
import requests
from dotenv import load_dotenv
import json
import os
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
import logging

# Load environment variables
load_dotenv()

class YouTubeScraper:
    def __init__(self):
        """Initialize the YouTube scraper."""
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.captions_file = self.data_dir / "youtube_captions.json"

    def search_podcasts(self, person_name: str, max_results: int = 10) -> Dict[str, Any]:
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
            search_query = f"{person_name} podcast"
            
            # Make request to YouTube Data API
            url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': self.youtube_api_key,
                'q': search_query,
                'type': 'video',
                'part': 'snippet',
                'maxResults': max_results,
                'videoDuration': 'long',  # Filter for longer videos (likely podcasts)
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
        