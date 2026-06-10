import gradio as gr
import shutil
import os

def generate_dub(ref_audio, srt_file):

    shutil.copy(
        ref_audio,
        "reference.wav"
    )

    shutil.copy(
        srt_file,
        "input.srt"
    )

    exec(open("srt_dubber.py").read())

    return "dubbed.wav"

demo = gr.Interface(
    fn=generate_dub,
    inputs=[
        gr.Audio(type="filepath",
                 label="Reference Audio"),
        gr.File(label="SRT File")
    ],
    outputs=gr.File(
        label="Dubbed Audio"
    ),
    title="Operation Fail"
)

demo.launch(share=True)
