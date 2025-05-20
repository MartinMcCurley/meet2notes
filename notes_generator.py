#!/usr/bin/env python3
"""
notes_generator.py ─────────────────────────────────────────────────────────────
A script to convert a meeting transcript into formatted Markdown meeting notes
with a summary, key points, and a to-do list at the end.

Usage:
    python notes_generator.py [--transcript TRANSCRIPT_FILE] [--output OUTPUT_FILE]
    
Options:
    --transcript TRANSCRIPT_FILE   Path to the transcript file (default: meeting01_transcript_tiny.txt)
    --output OUTPUT_FILE          Path for the output Markdown file (default: meeting_notes.md)
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from openai import OpenAI

def read_transcript(file_path):
    """Read the transcript file and return its content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        sys.exit(1)

def chunk_text(text, max_len=12000):
    """Split text into chunks below max_len characters at timestamp boundaries"""
    chunks = []
    current_chunk = []
    current_length = 0
    
    for line in text.splitlines():
        # If adding this line would exceed the max length and we already have content,
        # save the current chunk and start a new one
        if current_length + len(line) > max_len and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(line)
        current_length += len(line)
    
    # Add the last chunk if it has content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks

def generate_notes(transcript, model="gpt-4o-mini"):
    """Use OpenAI to generate meeting notes from the transcript"""
    client = OpenAI()
    
    # System message to instruct the model on the task
    system_message = """
    You are an expert meeting notes summarizer. Convert the meeting transcript into well-structured Markdown notes.
    Include the following sections:
    1. Summary - A brief overview of what was discussed (3-5 sentences)
    2. Key Points - The main topics and decisions from the meeting
    3. Action Items - Extract any tasks or to-dos mentioned in the meeting, with responsible persons if mentioned
    
    Format using proper Markdown with headers, bullet points, and emphasis where appropriate.
    Be factual and only include information that was actually mentioned in the transcript.
    """
    
    chunks = chunk_text(transcript)
    print(f"Processing transcript in {len(chunks)} chunks...")
    
    partial_summaries = []
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": chunk}
            ],
            temperature=0.3,  # Lower temperature for more factual responses
        )
        
        partial_summaries.append(response.choices[0].message.content)
    
    # If we have multiple chunks, create a final summary
    if len(partial_summaries) > 1:
        print("Generating final summary from all chunks...")
        
        # Create a condensed version of all partial summaries
        combined_summary = "\n\n---\n\n".join(partial_summaries)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"{system_message}\nYou are synthesizing multiple partial summaries into one cohesive set of notes."},
                {"role": "user", "content": combined_summary}
            ],
            temperature=0.3,
        )
        
        final_notes = response.choices[0].message.content
    else:
        final_notes = partial_summaries[0]
    
    # Add a header with the date
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"# Meeting Notes - {today}\n\n"
    
    return header + final_notes

def save_notes(notes, output_file):
    """Save the generated notes to a file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(notes)
        print(f"✓ Meeting notes saved to {output_file}")
    except Exception as e:
        print(f"Error saving notes: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert transcript to formatted meeting notes")
    parser.add_argument("--transcript", default="meeting01_transcript_tiny.txt", 
                        help="Path to the transcript file")
    parser.add_argument("--output", default="meeting_notes.md",
                        help="Path for the output Markdown file")
    parser.add_argument("--model", default="gpt-4o-mini",
                       choices=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                       help="OpenAI model to use for summarization")
    parser.add_argument("--api-key", 
                       help="OpenAI API key (alternative to setting OPENAI_API_KEY environment variable)")
    
    args = parser.parse_args()
    
    # Set API key from command line argument if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY environment variable not set and --api-key not provided.")
        print("Please either:")
        print("  1. Set environment variable: $env:OPENAI_API_KEY='your-api-key' (PowerShell)")
        print("  2. Pass API key as argument: --api-key your-api-key")
        sys.exit(1)
    
    # Check if transcript file exists
    if not os.path.exists(args.transcript):
        print(f"Error: Transcript file not found: {args.transcript}")
        sys.exit(1)
    
    print(f"» Reading transcript from {args.transcript}...")
    transcript = read_transcript(args.transcript)
    
    print(f"» Generating meeting notes using {args.model}...")
    notes = generate_notes(transcript, args.model)
    
    print(f"» Saving meeting notes to {args.output}...")
    save_notes(notes, args.output)
    
    print("Done!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 