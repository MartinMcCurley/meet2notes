#!/usr/bin/env python3
"""
meeting2notes.py ──────────────────────────────────────────────────────────────
A script that converts a meeting recording video into:
  • `audio.wav` – extracted audio file
  • `transcript.txt` – plain‑text transcript (timestamped)

Steps performed
───────────────
1. Extracts the first audio track to 16‑bit 16 kHz WAV using **ffmpeg**.
2. Transcribes locally with **OpenAI Whisper** (CPU or GPU).

Prerequisites
─────────────
• Python 3.6+
• ffmpeg in PATH or in the extracted folder
• pip install:
    pip install openai-whisper

Usage example
──────────────
python meeting2notes.py recording.mkv

Arguments
─────────
positional:
  INPUT              Path to video or audio file.
optional flags:
  -o, --output BASE  Base name for output files (default: input file stem)
  -m, --model NAME   Whisper model size (tiny, base, small, medium, large) (default: base)
  --no-timestamps    Do not include timestamps in transcript
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Add ffmpeg to PATH for Whisper to find it
FFMPEG_PATH = os.path.abspath(os.path.join("ffmpeg-7.1.1-essentials_build", "bin"))
os.environ["PATH"] = f"{FFMPEG_PATH};{os.environ['PATH']}"

# --------------------------- helpers --------------------------------------- #

def run(cmd: List[str]) -> None:
    """Run a subprocess, streaming stdout/stderr in real time."""
    print(f"Running command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {proc.returncode}: {' '.join(cmd)}")

def extract_audio(src: Path, dst: Path) -> None:
    """Extract first audio track to 16‑bit PCM WAV."""
    cmd = [
        os.path.join(FFMPEG_PATH, "ffmpeg.exe"),  # Use the path variable
        "-y",  # overwrite
        "-i", str(src),
        "-map", "0:a:0",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        str(dst),
    ]
    run(cmd)

def transcribe(audio_file: Path, model_name: str, with_timestamps: bool) -> str:
    """Transcribe audio file to text."""
    try:
        import whisper
    except ImportError:
        print("Whisper not installed. Run: pip install openai-whisper", file=sys.stderr)
        raise
    
    print(f"Loading Whisper {model_name} model...")
    model = whisper.load_model(model_name)
    
    print("Transcribing audio...")
    result = model.transcribe(str(audio_file))
    
    if with_timestamps:
        # Format with timestamps
        lines = []
        for segment in result["segments"]:
            start_time = int(segment["start"])
            hours = start_time // 3600
            minutes = (start_time % 3600) // 60
            seconds = start_time % 60
            timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
            lines.append(f"{timestamp} {segment['text'].strip()}")
        return "\n".join(lines)
    else:
        # Just return the plain text
        return result["text"]

# --------------------------- main ----------------------------------------- #

def main() -> None:
    p = argparse.ArgumentParser(description="Video → transcript")
    p.add_argument("INPUT", type=Path, help="Video or audio file")
    p.add_argument("-o", "--output", dest="base", metavar="BASE", help="Base name for output files")
    p.add_argument("-m", "--model", default="base", 
                   choices=["tiny", "base", "small", "medium", "large"],
                   help="Whisper model size (default: base)")
    p.add_argument("--no-timestamps", action="store_true", help="Do not include timestamps in transcript")
    
    args = p.parse_args()
    base = args.base or args.INPUT.stem
    
    # Extract audio if input is not already a WAV file
    if args.INPUT.suffix.lower() != '.wav':
        wav_path = Path(f"{base}_audio.wav")
        print("» Extracting audio…")
        extract_audio(args.INPUT, wav_path)
        print(f"✓ Audio saved to {wav_path}")
    else:
        wav_path = args.INPUT
        print("Input is already a WAV file, skipping extraction")
    
    # Transcribe
    print("» Transcribing with Whisper…")
    transcript = transcribe(wav_path, args.model, not args.no_timestamps)
    
    # Save transcript
    transcript_path = Path(f"{base}_transcript.txt")
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"✓ Transcript saved to {transcript_path}")
    
    print("Done!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted by user")
