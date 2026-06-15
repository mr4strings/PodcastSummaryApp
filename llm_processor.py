import logging
import time
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

def process_transcript_with_llm(transcript_text, episode_title):
    """
    Processes the transcript text using the Google Gemini API to generate a structured
    summary, major points, important quotes, and sources.

    Args:
        transcript_text (str): The full transcript of the podcast episode.
        episode_title (str): The title of the podcast episode.

    Returns:
        dict: A dictionary containing the summary, major points, quotes, and sources,
              or None if an error occurs.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not found.")
        return None

    response_text = None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        You are an expert podcast analyst. Your task is to analyze the following podcast transcript for the episode titled "{episode_title}" and provide a structured summary.

        Transcript:
        ---
        {transcript_text} 
        ---

        Your response MUST be a single, valid JSON object and nothing else. Do not include any explanatory text or markdown formatting.

        Here is an example of the exact format required:
        ```json
        {{
          "summary": "This is a concise, one-paragraph summary of the entire podcast episode.",
          "major_points": [
            "This is the first major point or takeaway from the episode.",
            "This is the second major point, which should be a separate idea.",
            "This is a third and final key takeaway."
          ],
          "quotes": [
            "This is the first important quote. It should be a complete sentence or a memorable phrase.",
            "This is a second important quote from a different part of the conversation."
          ],
          "sources": [
            "First source mentioned, like a book or a person.",
            "Second source mentioned. If none, return an empty list [] here."
          ]
        }}
        ```
        """

        # Make the API call to the Gemini model with the prepared prompt.
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Clean up potential markdown formatting (like ```json) from the response.
        if response_text.strip().startswith("```json"):
            response_text = response_text.strip()[7:-3].strip()
            
        # Parse the cleaned text string into a Python dictionary.
        content_data = json.loads(response_text)

        logging.info("Gemini summary processing complete.")
        return content_data

    except json.JSONDecodeError as e:
        # This error handles cases where the LLM returns text that isn't valid JSON.
        logging.error(f"Failed to decode JSON from Gemini response: {e}")
        if response_text:
            logging.error(f"--- START OF INVALID SUMMARY RESPONSE ---\n{response_text}\n--- END OF INVALID SUMMARY RESPONSE ---")
        return None
    except Exception as e:
        # This is a general catch-all for any other unexpected errors.
        logging.error(f"An unexpected error occurred during summary processing with Gemini: {e}", exc_info=True)
        return None

def diarize_transcript_with_llm(transcript_text):
    """
    Since transcription is now performed natively by Gemini, the transcript is
    already properly formatted and diarized. This function acts as a pass-through.
    """
    logging.info("Transcript was already diarized natively. Skipping secondary formatting.")
    return transcript_text

