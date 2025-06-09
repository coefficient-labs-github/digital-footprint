import json
import os
from pathlib import Path
from openai import OpenAI
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File path
YOUTUBE_QUESTIONS_PATH = Path("src/data/transcripts/youtube_questions.json")
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

# 1. Load and flatten all questions
def load_all_questions():
    logging.info(f"Loading questions from {YOUTUBE_QUESTIONS_PATH}")
    with open(YOUTUBE_QUESTIONS_PATH, "r") as f:
        data = json.load(f)
    questions = []
    for video in data.values():
        questions.extend(video.get("questions", []))
    logging.info(f"Loaded {len(questions)} questions from all videos.")
    return questions

# 2. Clean questions using OpenAI
def clean_questions(questions):
    logging.info("Cleaning and deduplicating questions using OpenAI...")
    prompt = (
        "You are a helpful assistant. Clean up the following list of podcast questions: "
        "- Remove any duplicate or near-duplicate questions. "
        "- Correct grammar and formatting. "
        "- Return only the cleaned questions as a plain numbered list.\n\n"
        "Questions:\n" + "\n".join(questions)
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that cleans and deduplicates podcast questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    cleaned = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
    logging.info(f"Cleaned and deduplicated down to {len(cleaned)} questions.")
    return cleaned

# 3. Bucket questions using OpenAI
def bucket_questions(cleaned_questions):
    bucketed = {}
    for bucket_name, bucket_desc in BUCKETS:
        logging.info(f"Bucketing questions for: {bucket_name}")
        prompt = (
            f"From the following list of podcast questions, select the 10 best that fall under the bucket: '{bucket_name}'. "
            f"This bucket is defined as: {bucket_desc}.\n"
            "If there are none, return nothing.\n"
            "Return only the selected questions as a plain numbered list.\n\n"
            "Questions:\n" + "\n".join(cleaned_questions)
        )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that categorizes podcast questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        selected = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
        if selected:
            logging.info(f"Added {len(selected)} questions to bucket: {bucket_name}")
            bucketed[bucket_name] = selected
        else:
            logging.info(f"No questions found for bucket: {bucket_name}")
    return bucketed

# 4. Save output
def save_bucketed(bucketed):
    with open(OUTPUT_PATH, "w") as f:
        json.dump(bucketed, f, indent=2)
    logging.info(f"Saved bucketed questions to {OUTPUT_PATH}")

def synthesize_buckets_if_needed():
    if not OUTPUT_PATH.exists():
        logging.info(f"{OUTPUT_PATH} does not exist. Running bucketing process.")
        questions = load_all_questions()
        cleaned = clean_questions(questions)
        bucketed = bucket_questions(cleaned)
        save_bucketed(bucketed)
    else:
        logging.info(f"{OUTPUT_PATH} already exists. Skipping bucketing.")

if __name__ == "__main__":
    questions = load_all_questions()
    cleaned = clean_questions(questions)
    bucketed = bucket_questions(cleaned)
    save_bucketed(bucketed)
