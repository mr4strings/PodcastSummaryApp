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
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

        prompt = f"""
        You are an expert podcast analyst. Your task is to analyze the following podcast transcript for the episode titled "{episode_title}" and provide a structured summary.

        Transcript (first 10,000 characters):
        ---
        {transcript_text[:10000]} 
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
    Uses the Gemini API to format a raw transcript into a script-like format
    with speaker labels (a process called diarization).

    Args:
        transcript_text (str): The raw transcript text.

    Returns:
        str: The formatted transcript with speaker labels, or None if an error occurs.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not found for diarization.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

        # This prompt is specifically engineered for the formatting task.
        prompt = f"""
        You are an expert transcript editor. Your task is to take the following raw text from a podcast transcript and reformat it into a script, identifying and labeling the speakers.

        Use labels like "Host:", "Guest 1:", "Guest 2:", etc. If you can identify a speaker's name from the context, use it (e.g., "Nilay:"). Ensure each speaker's dialogue is on a new line.

        Do not summarize or change the content. Only add speaker labels and line breaks.

        Here is an example of the desired output format:
        ---
        Host: Welcome back to the show. Today, we're joined by a special guest.
        Guest 1: Thanks for having me. I'm excited to be here.
        ---

        Now, please reformat the following transcript:
        ---
        {transcript_text}
        ---
        """
        
        response = model.generate_content(prompt)
        logging.info("Gemini diarization processing complete.")
        return response.text

    except Exception as e:
        logging.error(f"An unexpected error occurred during diarization with Gemini: {e}", exc_info=True)
        return None

