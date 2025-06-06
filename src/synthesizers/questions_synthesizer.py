import json
import os
from pathlib import Path
from openai import OpenAI

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
    with open(YOUTUBE_QUESTIONS_PATH, "r") as f:
        data = json.load(f)
    questions = []
    for video in data.values():
        questions.extend(video.get("questions", []))
    return questions

# 2. Clean questions using OpenAI
def clean_questions(questions):
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
    # Parse the response into a list
    cleaned = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
    return cleaned

# 3. Bucket questions using OpenAI
def bucket_questions(cleaned_questions):
    bucketed = {}
    for bucket_name, bucket_desc in BUCKETS:
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
        # Parse the response into a list
        selected = [q.strip().lstrip("0123456789. ") for q in response.choices[0].message.content.split("\n") if q.strip()]
        if selected:
            bucketed[bucket_name] = selected
    return bucketed

# 4. Save output
def save_bucketed(bucketed):
    with open(OUTPUT_PATH, "w") as f:
        json.dump(bucketed, f, indent=2)
    print(f"Saved bucketed questions to {OUTPUT_PATH}")

if __name__ == "__main__":
    questions = load_all_questions()
    cleaned = clean_questions(questions)
    bucketed = bucket_questions(cleaned)
    save_bucketed(bucketed)
