from typing import List, Dict, Any
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
from dotenv import load_dotenv
import json
from openai import OpenAI
import os

# Load environment variables
load_dotenv()

class YouTubeScraper:
    def __init__(self):
        """Initialize the YouTube scraper."""
        self.formatter = TextFormatter()
        self.client = OpenAI()
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

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
            
    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        Get the transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary containing transcript information
        """
        try:
            # Try to get transcript in English first
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            except Exception as e:
                # If English fails, try to get any available transcript
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                except Exception as e:
                    # Get list of available transcripts
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    available_languages = [t.language_code for t in transcript_list]
                    return {
                        'video_id': video_id,
                        'error': f'No transcript available. Available languages: {available_languages}',
                        'transcript': '',
                        'segments': []
                    }
            
            # Format transcript as plain text
            formatted_transcript = self.formatter.format_transcript(transcript_list)
            
            return {
                'video_id': video_id,
                'transcript': formatted_transcript,
                'segments': transcript_list  # Original transcript with timestamps
            }
            
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {str(e)}")
            return {
                'video_id': video_id,
                'error': str(e),
                'transcript': '',
                'segments': []
            }