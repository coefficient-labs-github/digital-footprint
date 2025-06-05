import os
import json
from pathlib import Path
from transcripts_to_questions import extract_questions_from_transcript

def test_question_extraction():
    # Read the input JSON
    input_path = Path("src/data/transcripts/youtube_captions.json")
    
    with open(input_path, 'r') as f:
        captions_data = json.load(f)
    
    # Get the first video for testing
    video_id = next(iter(captions_data))
    video_info = captions_data[video_id]
    
    print(f"\nTesting with video: {video_info['title']}")
    print(f"Channel: {video_info['channel']}")
    print(f"Date: {video_info['date']}")
    
    # Extract questions
    questions = extract_questions_from_transcript(video_info['transcript'])
    
    # Print results
    print("\nExtracted Questions:")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
    
    # Basic validation
    assert len(questions) > 0, "No questions were extracted"
    print(f"\nSuccessfully extracted {len(questions)} questions")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        exit(1)
        
    test_question_extraction() 