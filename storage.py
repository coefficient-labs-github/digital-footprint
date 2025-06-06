import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

class DataStorage:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def save_links(self, platform: str, links: List[str]) -> None:
        """Save platform-specific links to a JSON file."""
        file_path = self.base_dir / f"{platform}_links.json"
        data = {
            "timestamp": datetime.now().isoformat(),
            "links": links
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
            
    def load_links(self, platform: str) -> List[str]:
        """Load platform-specific links from a JSON file."""
        file_path = self.base_dir / f"{platform}_links.json"
        if not file_path.exists():
            return []
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("links", [])
    
    def save_transcript(self, video_id: str, transcript: Dict[str, Any]) -> None:
        """Save a video transcript to a JSON file.
        
        Args:
            video_id: The YouTube video ID
            transcript: The transcript response from YouTube API
        """
        file_path = self.base_dir / "transcripts" / f"{video_id}.json"
        file_path.parent.mkdir(exist_ok=True)
        
        # Convert transcript response to a dictionary format
        transcript_data = {
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "content": transcript.text if hasattr(transcript, 'text') else str(transcript),
            "status_code": transcript.status_code if hasattr(transcript, 'status_code') else None
        }
        
        with open(file_path, "w") as f:
            json.dump(transcript_data, f, indent=2)
            
    def load_transcript(self, video_id: str) -> Dict[str, Any]:
        """Load a video transcript from a JSON file."""
        file_path = self.base_dir / "transcripts" / f"{video_id}.json"
        if not file_path.exists():
            return {}
        with open(file_path, "r") as f:
            return json.load(f) 