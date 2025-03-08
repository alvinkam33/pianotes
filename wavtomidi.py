import subprocess

# Define file paths
MODEL_DIR = "maestro_checkpoint"
AUDIO_PATH = "test.wav"

command = [
    "onsets_frames_transcription_transcribe",
    f"--model_dir={MODEL_DIR}",
    AUDIO_PATH
]
print("running Magenta transcription model")
process = subprocess.run(command, capture_output=True, text=True)
print(process.stdout)
print(process.stderr)
