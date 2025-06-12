import json
import os
import re
from pathlib import Path
from openai import OpenAI
import logging
import difflib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File path
YOUTUBE_TRANSCRIPTS_PATH = Path("src/data/transcripts/youtube_transcripts.json")
OUTPUT_PATH = Path("src/data/transcripts/bucketed_questions.json")

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Buckets
BUCKETS = [
    ("Early Life / Professional Journey", "questions about early life, background, upbringing, or professional journey"),
    ("Questions/Advice to help founders", "questions or advice that would help startup founders"),
    ("Questions/Advice to help VCs", "questions or advice that would help venture capitalists (VCs)"),
    ("Questions/Advice that pertains to Culturally Relevant Topics (ex: AI, Blockchain)", "questions or advice about culturally relevant topics such as AI, Blockchain, or other major trends"),
    ("Questions/Advice that pertains to methodologies/frameworks they utilize in their work", "questions or advice about methodologies or frameworks used in their work"),
    ("Questions/Advice that cannot easily be put into any of the buckets above, but you think is interesting and should be included", "questions or advice that don't fit the above buckets but are interesting or should be included"),
]

def extract_questions_from_subtitles(video_data):
    """Extract questions from video subtitles with timestamps."""
    video_title = video_data.get('title', 'Unknown Video')
    video_url = video_data.get('url', '')
    
    # Get subtitles
    subtitles = []
    for subtitle_data in video_data.get('subtitles', []):
        srt_content = subtitle_data.get('srt', '')
        if srt_content:
            subtitles.append(srt_content)
    
    if not subtitles:
        logging.warning(f"No subtitles found for video: {video_title}")
        return []
    
    # Join all subtitles
    full_transcript = "\n".join(subtitles)
    
    # Use OpenAI to extract questions with timestamps
    prompt = f"""
    Extract all questions asked to the guest in this podcast transcript. 
    For each question, provide:
    1. The exact question text
    2. The approximate timestamp (in format MM:SS) when the question was asked
    
    Format your response as a JSON array of objects with 'question' and 'timestamp' fields.
    Only include actual questions asked to the guest, not rhetorical questions or statements.
    
    Transcript:
    {full_transcript[:15000]}  # Limit to avoid token limits
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts questions with timestamps from podcast transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        questions_with_timestamps = result.get('questions', [])
        
        # Add video metadata to each question
        for q in questions_with_timestamps:
            q['video_title'] = video_title
            q['video_url'] = video_url
        
        logging.info(f"Extracted {len(questions_with_timestamps)} questions from video: {video_title}")
        return questions_with_timestamps
    
    except Exception as e:
        logging.error(f"Error extracting questions from video {video_title}: {str(e)}")
        return []

def load_all_questions_with_metadata():
    """Load transcripts and extract questions with metadata."""
    logging.info(f"Loading transcripts from {YOUTUBE_TRANSCRIPTS_PATH}")
    with open(YOUTUBE_TRANSCRIPTS_PATH, "r") as f:
        videos_data = json.load(f)
    
    all_questions = []
    for video_data in videos_data:
        video_questions = extract_questions_from_subtitles(video_data)
        all_questions.extend(video_questions)
    
    logging.info(f"Extracted a total of {len(all_questions)} questions with timestamps from all videos.")
    return all_questions

def clean_questions(questions_with_metadata):
    """Clean and deduplicate questions while preserving metadata."""
    logging.info("Cleaning and deduplicating questions using OpenAI...")
    
    # Extract just the question text for cleaning
    question_texts = [q['question'] for q in questions_with_metadata]
    
    prompt = (
        "You are a helpful assistant. Clean up the following list of podcast questions: "
        "- Remove any duplicate or near-duplicate questions. "
        "- Correct grammar and formatting. "
        "- Return only the cleaned questions as a plain numbered list.\n\n"
        "Questions:\n" + "\n".join(question_texts)
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that cleans and deduplicates podcast questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    cleaned_texts = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
    logging.info(f"Cleaned and deduplicated down to {len(cleaned_texts)} questions.")
    
    # Map cleaned questions back to their metadata
    cleaned_with_metadata = []
    for clean_q in cleaned_texts:
        # Find the first matching original question
        for orig_q in questions_with_metadata:
            if clean_q.lower() in orig_q['question'].lower() or orig_q['question'].lower() in clean_q.lower():
                # Create a new object with cleaned question text but original metadata
                cleaned_with_metadata.append({
                    'question': clean_q,
                    'timestamp': orig_q['timestamp'],
                    'video_title': orig_q['video_title'],
                    'video_url': orig_q['video_url']
                })
                break
    
    return cleaned_with_metadata

def bucket_questions(cleaned_questions_with_metadata):
    """Bucket questions while preserving metadata."""
    bucketed = {}
    
    # Extract just the question text for bucketing
    question_texts = [q['question'] for q in cleaned_questions_with_metadata]
    
    for bucket_name, bucket_desc in BUCKETS:
        logging.info(f"Bucketing questions for: {bucket_name}")
        
        prompt = (
            f"From the following list of podcast questions, select the 10 best that fall under the bucket: '{bucket_name}'. "
            f"This bucket is defined as: {bucket_desc}.\n"
            "If there are none, return nothing.\n"
            "Return only the selected questions as a plain numbered list.\n\n"
            "Questions:\n" + "\n".join(question_texts)
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that categorizes podcast questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        selected_texts = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
        
        if selected_texts:
            logging.info(f"Added {len(selected_texts)} questions to bucket: {bucket_name}")
            
            # Map selected questions back to their metadata
            selected_with_metadata = []
            for sel_text in selected_texts:
                for q in cleaned_questions_with_metadata:
                    if sel_text.lower() in q['question'].lower() or q['question'].lower() in sel_text.lower():
                        selected_with_metadata.append(q)
                        break
            
            bucketed[bucket_name] = selected_with_metadata
        else:
            logging.info(f"No questions found for bucket: {bucket_name}")
    
    return bucketed

def save_bucketed(bucketed):
    """Save bucketed questions with metadata to JSON."""
    with open(OUTPUT_PATH, "w") as f:
        json.dump(bucketed, f, indent=2)
    logging.info(f"Saved bucketed questions with metadata to {OUTPUT_PATH}")

def synthesize_buckets_if_needed():
    """Run the bucketing process if needed."""
    if not OUTPUT_PATH.exists():
        logging.info(f"{OUTPUT_PATH} does not exist. Running bucketing process.")
        questions_with_metadata = load_all_questions_with_metadata()
        cleaned = clean_questions(questions_with_metadata)
        bucketed = bucket_questions(cleaned)
        save_bucketed(bucketed)
    else:
        logging.info(f"{OUTPUT_PATH} already exists. Skipping bucketing.")

def extract_and_bucket_questions_from_segments():
    """
    Extracts all questions from each video's full transcript, maps them to timestamps using segments,
    buckets them, and saves to bucketed_questions.json.
    """
    logging.info(f"Loading transcripts from {YOUTUBE_TRANSCRIPTS_PATH}")
    with open(YOUTUBE_TRANSCRIPTS_PATH, "r") as f:
        videos_data = json.load(f)

    all_questions_with_metadata = []
    for video_data in videos_data:
        video_title = video_data.get('title', 'Unknown Video')
        video_url = video_data.get('url', '')
        for subtitle_data in video_data.get('subtitles', []):
            full_transcript = subtitle_data.get('full_transcript', '')
            segments = subtitle_data.get('segments', [])
            if not full_transcript or not segments:
                continue
            # If transcript is too long, split into chunks (OpenAI context limit ~15k tokens)
            max_length = 15000
            transcript_chunks = [full_transcript[i:i+max_length] for i in range(0, len(full_transcript), max_length)]
            questions = []
            for chunk in transcript_chunks:
                prompt = f"""
                Extract all questions asked to the guest in this podcast transcript. 
                For each question, provide:
                1. The exact question text
                2. The exact or closest matching snippet from the transcript (for timestamp lookup)
                
                Format your response as a JSON array of objects with 'question' and 'snippet' fields.
                Only include actual questions asked to the guest, not rhetorical questions or statements.
                
                Transcript:
                {chunk}
                """
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that extracts questions from podcast transcripts."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
                    questions += result.get('questions', [])
                except Exception as e:
                    logging.error(f"Error extracting questions from video {video_title}: {str(e)}")
                    continue
            # For each question, find closest matching segment for timestamp
            for q in questions:
                question_text = q.get('question', '')
                snippet = q.get('snippet', '')
                # Fuzzy match snippet to segment text
                best_match = None
                best_score = 0
                for seg in segments:
                    score = difflib.SequenceMatcher(None, snippet, seg['text']).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = seg
                timestamp = best_match['start_time'] if best_match else None
                all_questions_with_metadata.append({
                    'question': question_text,
                    'timestamp': timestamp,
                    'video_title': video_title,
                    'video_url': video_url
                })
    logging.info(f"Extracted a total of {len(all_questions_with_metadata)} questions with timestamps from all videos.")
    # Clean and deduplicate
    cleaned_questions = clean_questions(all_questions_with_metadata)
    # Bucket
    bucketed = bucket_questions(cleaned_questions)
    # Save
    save_bucketed(bucketed)
    logging.info("Question extraction and bucketing complete.")

if __name__ == "__main__":
    extract_and_bucket_questions_from_segments()
