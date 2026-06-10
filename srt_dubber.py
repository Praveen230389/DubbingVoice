import srt
import soundfile as sf
from pydub import AudioSegment

# ==========================================
# SETTINGS
# ==========================================

SRT_FILE = "input.srt"
REFERENCE_AUDIO = "reference.mp3"
OUTPUT_FILE = "dubbed.wav"

# ==========================================
# LOAD SRT
# ==========================================

with open(SRT_FILE, "r", encoding="utf-8") as f:
    subtitles = list(srt.parse(f.read()))

print(f"Found {len(subtitles)} subtitles")

# ==========================================
# BUILD FINAL AUDIO
# ==========================================

final_audio = AudioSegment.silent(duration=0)

current_position_ms = 0

for idx, sub in enumerate(subtitles):

    print("\n" + "=" * 60)
    print(f"Subtitle #{idx+1}")

    text = sub.content.strip()

    print("Text:", text)

    # ======================================
    # GENERATE SPEECH USING OMNIVOICE
    # ======================================

    audio = model.generate(
        text=text,
        ref_audio=REFERENCE_AUDIO
    )

    temp_file = f"segment_{idx}.wav"

    sf.write(
        temp_file,
        audio[0],
        24000
    )

    segment = AudioSegment.from_wav(temp_file)

    # ======================================
    # SRT START TIME
    # ======================================

    start_ms = int(
        sub.start.total_seconds() * 1000
    )

    # ======================================
    # INSERT SILENCE IF NEEDED
    # ======================================

    if start_ms > current_position_ms:

        silence_duration = (
            start_ms - current_position_ms
        )

        print(
            "Adding silence:",
            round(silence_duration / 1000, 2),
            "sec"
        )

        silence = AudioSegment.silent(
            duration=silence_duration
        )

        final_audio += silence

    # ======================================
    # ADD GENERATED SPEECH
    # ======================================

    final_audio += segment

    current_position_ms = len(final_audio)

    print(
        "Generated:",
        round(len(segment) / 1000, 2),
        "sec"
    )

# ==========================================
# EXPORT
# ==========================================

final_audio.export(
    OUTPUT_FILE,
    format="wav"
)

print("\n" + "=" * 60)
print("DONE")
print("Created:", OUTPUT_FILE)
print(
    "Final Duration:",
    round(len(final_audio) / 1000, 2),
    "sec"
)
