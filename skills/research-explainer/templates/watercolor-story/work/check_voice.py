"""Transcribe every tightened line again: the pause cuts must not have removed or clipped a word."""
import sys, json, pathlib, subprocess, difflib
H = pathlib.Path(__file__).parent; sys.path.insert(0, str(H))
import voice as V   # reuses transcribe() and norm(); importing it voices nothing when argv selects no line
from script import LINES
for i, text in LINES:
    mp3 = H / "voice" / "tight" / f"{i}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(H / "voice" / "tight" / f"{i}.wav"), str(mp3)], check=True)
    tr = V.transcribe(mp3.read_bytes())
    sim = difflib.SequenceMatcher(None, V.norm(text), V.norm(tr), autojunk=False).ratio()
    print(f"{i} {sim:.3f} {'OK ' if sim >= 0.95 else 'BAD'} | {tr}")
