from typing import Dict, Any, Tuple, Optional
import requests
import time
import json
from dotenv import load_dotenv
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
        self.data_dir = Path("src/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir = self.data_dir / "transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.captions_file = self.transcripts_dir / "youtube_captions.json"

    def get_transcript_with_retry(self, video_id: str, max_retries: int = 10, initial_delay: int = 1) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempt to get transcript with retry logic and exponential backoff.
        
        Args:
            video_id: YouTube video ID
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
        
        Returns:
            tuple: (transcript_data, language_code) if successful, (None, None) if failed
        """
        ytt_api = YouTubeTranscriptApi()
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                # Get transcript list
                trans_list = ytt_api.list_transcripts(video_id=video_id)
                
                # Try to get transcript in preferred language (English)
                transcript = trans_list.find_transcript(['en'])
                transcript_data = transcript.fetch()
                
                # Convert transcript data to string
                if isinstance(transcript_data, list):
                    full_transcript = ' '.join([part['text'] for part in transcript_data])
                else:
                    full_transcript = ' '.join([snippet.text for snippet in transcript_data])
                
                return full_transcript, transcript.language_code
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Attempt {attempt + 1}/{max_retries} failed for video {video_id}: {str(e)}")
                    time.sleep(delay)
                    delay = min(delay * 2, 10)  # Exponential backoff, capped at 10 seconds
                else:
                    logging.error(f"All {max_retries} attempts failed for video {video_id}: {str(e)}")
                    return None, None
        
        return None, None

    def save_transcripts_to_json(self, transcripts_data: Dict[str, Any]) -> None:
        """
        Save transcripts data to a JSON file.
        
        Args:
            transcripts_data: Dictionary containing transcript data
        """
        try:
            self.transcripts_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Saving transcripts to {self.captions_file}")
            with open(self.captions_file, 'w', encoding='utf-8') as f:
                json.dump(transcripts_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Successfully saved transcripts to {self.captions_file}")
        except Exception as e:
            logging.error(f"Error saving transcripts to {self.captions_file}: {str(e)}")

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
        