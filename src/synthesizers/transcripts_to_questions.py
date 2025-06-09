import json
import os
from pathlib import Path
from openai import OpenAI
from typing import Dict, List
import logging

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def split_transcript_into_parts(transcript: str, num_parts: int = 3) -> List[str]:
    """Split transcript into num_parts roughly equal parts by character count."""
    length = len(transcript)
    part_size = length // num_parts
    parts = []
    for i in range(num_parts):
        start = i * part_size
        # Last part takes the remainder
        end = (i + 1) * part_size if i < num_parts - 1 else length
        parts.append(transcript[start:end])
    return parts

def extract_questions_from_transcript(transcript: str) -> List[str]:
    """Extract questions from a transcript using ChatGPT 4.0, splitting into 3 parts."""
    parts = split_transcript_into_parts(transcript, 3)
    all_questions = []
    
    for part in parts:
        prompt = f"""Given the following podcast transcript segment, extract all questions that were asked to the guest. 
Return only the questions in a list format, one per line. Do not include any other text or explanation.

Transcript segment:
{part}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts questions from podcast transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        chunk_questions = [q.strip() for q in response.choices[0].message.content.split('\n') if q.strip()]
        all_questions.extend(chunk_questions)
    # Remove duplicates while preserving order
    seen = set()
    unique_questions = [q for q in all_questions if not (q in seen or seen.add(q))]
    return unique_questions

def process_transcripts():
    # Read the input JSON
    input_path = Path("src/data/transcripts/youtube_captions.json")
    output_path = Path("src/data/transcripts/youtube_questions.json")
    logging.info(f"Reading transcripts from {input_path}")
    with open(input_path, 'r') as f:
        captions_data = json.load(f)
    
    # Process each video
    questions_data = {}
    for video_id, video_info in captions_data.items():
        print(f"Processing video: {video_info['title']}")
        
        # Extract questions from transcript
        questions = extract_questions_from_transcript(video_info['transcript'])
        
        # Store in same format as input
        questions_data[video_id] = {
            "title": video_info['title'],
            "channel": video_info['channel'],
            "date": video_info['date'],
            "questions": questions
        }
    
    # Save the results
    with open(output_path, 'w') as f:
        json.dump(questions_data, f, indent=2)

if __name__ == "__main__":
    process_transcripts()
