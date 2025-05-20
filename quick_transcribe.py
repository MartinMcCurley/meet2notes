#!/usr/bin/env python3
"""
quick_transcribe.py ─────────────────────────────────────────────────────────────
A script to transcribe audio files using Whisper with progress indication.

Usage:
    python quick_transcribe.py [--model MODEL]
    
Options:
    --model MODEL   Whisper model to use (tiny, base, small, medium, large)
                    Default: tiny (fastest, less accurate)
                    Recommended for better quality: base or small
"""
import argparse
import os
import sys
import time
import whisper
from pathlib import Path
from tqdm import tqdm

# Add ffmpeg to PATH for Whisper to find it
FFMPEG_PATH = os.path.abspath(os.path.join("ffmpeg-7.1.1-essentials_build", "bin"))
os.environ["PATH"] = f"{FFMPEG_PATH};{os.environ['PATH']}"

def format_time(seconds):
    """Format seconds into hours:minutes:seconds"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Transcribe audio using Whisper")
    parser.add_argument("--model", type=str, default="tiny", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model to use (default: tiny)")
    parser.add_argument("--transcript", type=str, default="meeting01_audio.wav",
                       help="Path to the audio file to transcribe (default: meeting01_audio.wav)")
    parser.add_argument("--output", type=str, default=None,
                       help="Path for the output transcript file (default: based on input filename)")
    args = parser.parse_args()
    
    # Input and output files
    audio_file = args.transcript
    
    # Set default output filename if not specified
    if args.output:
        output_file = args.output
    else:
        # Extract base name from input file
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = f"{base_name}_transcript_{args.model}.txt"
    
    # Check if the audio file exists
    if not os.path.exists(audio_file):
        print(f"Error: {audio_file} not found")
        return
    
    print(f"» Loading Whisper {args.model} model...")
    model = whisper.load_model(args.model)
    
    print(f"» Transcribing {audio_file}...")
    print(f"  This may take a while. Model: {args.model}")
    
    start_time = time.time()
    
    # The transcribe function doesn't provide progress, but we'll show a spinner
    # and periodically update with elapsed time
    with tqdm(total=100, desc="Processing", unit="%") as pbar:
        # Initial progress update
        last_update = time.time()
        
        # Define a callback function to update progress
        def progress_callback(current_progress):
            nonlocal last_update
            current_time = time.time()
            if current_time - last_update > 5:  # Update every 5 seconds
                elapsed = current_time - start_time
                pbar.set_postfix_str(f"Elapsed: {format_time(elapsed)}")
                last_update = current_time
                # Update progress to show movement
                pbar.update(1)
        
        # Set up progress display thread
        import threading
        stop_flag = threading.Event()
        
        def update_progress():
            while not stop_flag.is_set():
                progress_callback(0)
                time.sleep(1)
                
        progress_thread = threading.Thread(target=update_progress)
        progress_thread.start()
        
        try:
            # Perform the transcription
            result = model.transcribe(audio_file)
            
            # Signal the progress thread to stop
            stop_flag.set()
            progress_thread.join()
            
            # Complete the progress bar
            pbar.n = 100
            pbar.refresh()
        except Exception as e:
            stop_flag.set()
            progress_thread.join()
            raise e
    
    # Format with timestamps
    lines = []
    for segment in result["segments"]:
        start_time = segment["start"]
        timestamp = format_time(start_time)
        lines.append(f"[{timestamp}] {segment['text'].strip()}")
    
    transcript = "\n".join(lines)
    
    # Save the transcript
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    # Calculate statistics
    end_time = time.time()
    elapsed = end_time - start_time
    audio_duration = result["segments"][-1]["end"] if result["segments"] else 0
    
    print(f"✓ Transcription complete!")
    print(f"  - Elapsed time: {format_time(elapsed)}")
    print(f"  - Audio duration: {format_time(audio_duration)}")
    print(f"  - Processing ratio: {audio_duration/elapsed:.2f}x real-time")
    print(f"  - Transcript saved to: {output_file}")
    print(f"  - Segments: {len(result['segments'])}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}") 