```python
import os
import argparse
import srt
import soundfile as sf
from pydub import AudioSegment
from omnivoice import OmniVoice
import torch

# ==============================
# SETTINGS
# ==============================

SAFETY_MARGIN = 0.20

SPEED_STEPS = [
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0
]

# ==============================
# LOAD MODEL ONLY ONCE
# ==============================

print("Loading OmniVoice model...")

model = OmniVoice.from_pretrained(
    "k2-fsa/OmniVoice",
    device_map="cuda:0",
    dtype=torch.float16
)

print("Model loaded successfully")

# ==============================
# PROCESS ONE JOB
# ==============================

def process_job(
        SRT_FILE,
        REFERENCE_AUDIO,
        OUTPUT_FILE,
        TARGET_LANGUAGE):

    print("\n" + "=" * 80)
    print("Starting job")
    print("SRT:", SRT_FILE)
    print("Reference:", REFERENCE_AUDIO)
    print("Language:", TARGET_LANGUAGE)
    print("Output:", OUTPUT_FILE)
    print("=" * 80)

    with open(
        SRT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        subtitles = list(
            srt.parse(
                f.read()
            )
        )

    print(f"Found {len(subtitles)} subtitles")

    final_audio = AudioSegment.silent(
        duration=0
    )

    current_position_ms = 0

    for idx, sub in enumerate(subtitles):

        text = sub.content.strip()

        window = (
            sub.end.total_seconds()
            - sub.start.total_seconds()
        )

        target = max(
            0.5,
            window - SAFETY_MARGIN
        )

        print(
            f"\n[{idx+1}/{len(subtitles)}]"
        )

        selected = None
        selected_speed = None

        for speed in SPEED_STEPS:

            audio = model.generate(
                text=text,
                language=TARGET_LANGUAGE,
                ref_audio=REFERENCE_AUDIO,
                speed=speed
            )

            temp = f"temp_{idx}.wav"

            sf.write(
                temp,
                audio[0],
                24000
            )

            seg = AudioSegment.from_wav(
                temp
            )

            dur = (
                len(seg) / 1000
            )

            if dur <= target:

                selected = seg
                selected_speed = speed
                break

        if selected is None:

            audio = model.generate(
                text=text,
                language=TARGET_LANGUAGE,
                ref_audio=REFERENCE_AUDIO,
                duration=target
            )

            temp = f"temp_{idx}_d.wav"

            sf.write(
                temp,
                audio[0],
                24000
            )

            selected = AudioSegment.from_wav(
                temp
            )

            selected_speed = "duration"

        start_ms = int(
            sub.start.total_seconds()
            * 1000
        )

        if start_ms > current_position_ms:

            final_audio += AudioSegment.silent(
                start_ms - current_position_ms
            )

        final_audio += selected

        current_position_ms = len(
            final_audio
        )

    final_audio.export(
        OUTPUT_FILE,
        format="wav"
    )

    print(
        f"\nFinished: {OUTPUT_FILE}"
    )

# ==============================
# COMMAND LINE
# ==============================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--jobs",
    required=True,
    help="srt,ref,out,lang;srt,ref,out,lang"
)

args = parser.parse_args()

jobs = args.jobs.split(";")

for job in jobs:

    job = job.strip()

    if not job:
        continue

    srt_file, ref_audio, output_file, language = job.split(",")

    process_job(
        srt_file.strip(),
        ref_audio.strip(),
        output_file.strip(),
        language.strip()
    )

print("\nALL JOBS COMPLETED")
```
