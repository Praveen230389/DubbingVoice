import os
import srt
import soundfile as sf
from pydub import AudioSegment

from omnivoice import OmniVoice
import torch

from language_config import (
    TARGET_LANGUAGE,
    SAFETY_MARGIN,
    SPEED_STEPS
)

# ==============================
# LOAD MODEL (ONLY ONCE)
# ==============================

print("Loading OmniVoice model...")

model = OmniVoice.from_pretrained(
    "k2-fsa/OmniVoice",
    device_map="cuda:0",
    dtype=torch.float16
)

print("Model loaded successfully")

# ==============================
# FILES
# ==============================

SRT_FILE = "input.srt"
REFERENCE_AUDIO = "reference.mp3"
OUTPUT_FILE = "dubbed.wav"

# ==============================
# LOAD SRT
# ==============================

with open(SRT_FILE, "r", encoding="utf-8") as f:
    subtitles = list(srt.parse(f.read()))

print(f"Found {len(subtitles)} subtitles")

# ==============================
# AUDIO BUILD
# ==============================

final_audio = AudioSegment.silent(duration=0)
current_position_ms = 0

for idx, sub in enumerate(subtitles):

    text = sub.content.strip()

    window = sub.end.total_seconds() - sub.start.total_seconds()
    target = max(0.5, window - SAFETY_MARGIN)

    print(f"\n[{idx+1}] {text}")
    print("Target duration:", target)

    selected = None
    selected_speed = None

    # --------------------------
    # TRY SPEEDS
    # --------------------------

    for speed in SPEED_STEPS:

        audio = model.generate(
            text=text,
            language=TARGET_LANGUAGE,
            ref_audio=REFERENCE_AUDIO,
            speed=speed
        )

        temp = f"temp_{idx}.wav"
        sf.write(temp, audio[0], 24000)

        seg = AudioSegment.from_wav(temp)
        dur = len(seg) / 1000

        if dur <= target:
            selected = seg
            selected_speed = speed
            break

    # --------------------------
    # FALLBACK
    # --------------------------

    if selected is None:

        audio = model.generate(
            text=text,
            language=TARGET_LANGUAGE,
            ref_audio=REFERENCE_AUDIO,
            duration=target
        )

        temp = f"temp_{idx}_d.wav"
        sf.write(temp, audio[0], 24000)

        selected = AudioSegment.from_wav(temp)
        selected_speed = "duration"

    print("Selected:", selected_speed)

    # --------------------------
    # SILENCE FILL
    # --------------------------

    start_ms = int(sub.start.total_seconds() * 1000)

    if start_ms > current_position_ms:
        final_audio += AudioSegment.silent(start_ms - current_position_ms)

    final_audio += selected
    current_position_ms = len(final_audio)

# ==============================
# EXPORT
# ==============================

final_audio.export(OUTPUT_FILE, format="wav")

print("\nDONE")
print("Saved:", OUTPUT_FILE)
