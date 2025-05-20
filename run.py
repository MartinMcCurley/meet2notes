#!/usr/bin/env python3
"""
run.py ─────────────────────────────────────────────────────────────────────────
A simple runner script that combines all Meet2Notes steps into a single command.

Usage:
    python run.py video_file.mkv [--model MODEL] [--output OUTPUT_PREFIX]
    
Options:
    --model MODEL          Whisper model to use (tiny, base, small, medium, large)
    --output OUTPUT_PREFIX Base name for output files (default: input file stem)
    --api-key API_KEY      OpenAI API key (alternative to setting in .env)
    --no-summary           Skip the summary/notes generation step
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def run_command(command, description):
    """Run a command and display its output"""
    print(f"» {description}...")
    print(f"$ {' '.join(command)}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    for line in process.stdout:
        print(line, end="")
    
    process.wait()
    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}")
        sys.exit(process.returncode)

def main():
    parser = argparse.ArgumentParser(description="Meet2Notes: Convert meeting recordings to transcripts and notes")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model to use (default: base)")
    parser.add_argument("--output", dest="output_prefix", 
                        help="Base name for output files (default: input file stem)")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--no-summary", action="store_true", help="Skip summary/notes generation")
    
    args = parser.parse_args()
    
    # Check if video file exists
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    # Set output prefix
    output_prefix = args.output_prefix or video_path.stem
    
    # 1. Extract audio
    audio_file = f"{output_prefix}_audio.wav"
    run_command(
        ["python", "meeting2notes.py", str(video_path), "-o", output_prefix],
        "Extracting audio from video"
    )
    
    # 2. Transcribe audio
    transcript_file = f"{output_prefix}_transcript_{args.model}.txt"
    run_command(
        ["python", "quick_transcribe.py", "--model", args.model, "--transcript", audio_file, "--output", transcript_file],
        f"Transcribing audio with {args.model} model"
    )
    
    # 3. Generate meeting notes (if not skipped)
    if not args.no_summary:
        # Set up command
        notes_cmd = ["python", "notes_generator.py", "--transcript", transcript_file, "--output", f"{output_prefix}_notes.md"]
        
        # Add API key if provided
        if args.api_key:
            notes_cmd.extend(["--api-key", args.api_key])
        
        # Check if API key is available
        elif not os.environ.get("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not found in environment or command line")
            print("Summary generation will likely fail unless you've set it elsewhere")
        
        run_command(notes_cmd, "Generating meeting notes")
    
    print("\n✓ All tasks completed successfully!")
    print(f"  Audio: {audio_file}")
    print(f"  Transcript: {transcript_file}")
    if not args.no_summary:
        print(f"  Notes: {output_prefix}_notes.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 