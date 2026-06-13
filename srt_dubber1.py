import srt
import soundfile as sf

from pydub import AudioSegment

from language_config import (
    REFERENCE_LANGUAGE,
    TARGET_LANGUAGE,
    SAFETY_MARGIN,
    SPEED_STEPS
)

# ==========================================
# SETTINGS
# ==========================================

SRT_FILE = "input.srt"

REFERENCE_AUDIO = "reference.mp3"

OUTPUT_FILE = "dubbed.wav"

# ==========================================
# LOAD SRT
# ==========================================

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

print(
    f"Found {len(subtitles)} subtitles"
)

# ==========================================
# BUILD FINAL AUDIO
# ==========================================

final_audio = AudioSegment.silent(
    duration=0
)

current_position_ms = 0

for idx, sub in enumerate(subtitles):

    print(
        "\n" + "=" * 60
    )

    print(
        f"Subtitle #{idx+1}"
    )

    text = sub.content.strip()

    print(
        "Text:",
        text
    )

    # ======================================
    # SRT WINDOW
    # ======================================

    window_duration = (
        sub.end.total_seconds()
        - sub.start.total_seconds()
    )

    target_duration = (
        window_duration
        - SAFETY_MARGIN
    )

    if target_duration < 0.5:

        target_duration = 0.5

    print(
        "SRT Window:",
        round(window_duration, 2),
        "sec"
    )

    print(
        "Target:",
        round(target_duration, 2),
        "sec"
    )

    # ======================================
    # TRY SPEED LEVELS
    # ======================================

    selected_segment = None

    selected_duration = None

    selected_speed = None

    for speed in SPEED_STEPS:

        print(
            "Trying speed:",
            speed
        )

        audio = model.generate(
            text=text,
            language=TARGET_LANGUAGE,
            ref_audio=REFERENCE_AUDIO,
            speed=speed
        )

        temp_file = (
            f"temp_{idx}.wav"
        )

        sf.write(
            temp_file,
            audio[0],
            24000
        )

        segment = AudioSegment.from_wav(
            temp_file
        )

        generated_duration = (
            len(segment)
            / 1000
        )

        print(
            "Generated:",
            round(
                generated_duration,
                2
            ),
            "sec"
        )

        if generated_duration <= target_duration:

            selected_segment = segment

            selected_duration = generated_duration

            selected_speed = speed

            break

    # ======================================
    # IF NOTHING FITS
    # ======================================

    if selected_segment is None:

        print(
            "Nothing fit."
        )

        print(
            "Using duration control."
        )

        audio = model.generate(
            text=text,
            language=TARGET_LANGUAGE,
            ref_audio=REFERENCE_AUDIO,
            duration=target_duration
        )

        temp_file = (
            f"temp_{idx}.wav"
        )

        sf.write(
            temp_file,
            audio[0],
            24000
        )

        selected_segment = (
            AudioSegment.from_wav(
                temp_file
            )
        )

        selected_duration = (
            len(selected_segment)
            / 1000
        )

        selected_speed = "duration"

    print(
        "Selected:",
        selected_speed
    )

    print(
        "Final duration:",
        round(
            selected_duration,
            2
        ),
        "sec"
    )

    # ======================================
    # INSERT SILENCE
    # ======================================

    start_ms = int(
        sub.start.total_seconds()
        * 1000
    )

    if start_ms > current_position_ms:

        silence_duration = (
            start_ms
            - current_position_ms
        )

        print(
            "Adding silence:",
            round(
                silence_duration / 1000,
                2
            ),
            "sec"
        )

        final_audio += (
            AudioSegment.silent(
                duration=silence_duration
            )
        )

    # ======================================
    # APPEND AUDIO
    # ======================================

    final_audio += selected_segment

    current_position_ms = (
        len(final_audio)
    )

# ==========================================
# EXPORT
# ==========================================

final_audio.export(
    OUTPUT_FILE,
    format="wav"
)

print(
    "\n" + "=" * 60
)

print("DONE")

print(
    "Created:",
    OUTPUT_FILE
)

print(
    "Final Duration:",
    round(
        len(final_audio) / 1000,
        2
    ),
    "sec"
)
