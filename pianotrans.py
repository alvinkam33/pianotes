import subprocess
import pretty_midi

# Define paths
MODEL_DIR = "maestro_checkpoint"
AUDIO_PATH = "test.wav"
OUTPUT_MIDI_PATH = "test-pianotrans.mid"

# Step 1: Run Magenta’s transcription script
command = [
    "python3 example.py",
    f"--audio_path={AUDIO_PATH}",
    f"--output_midi_path={OUTPUT_MIDI_PATH} --cuda"
]

process = subprocess.run(command, capture_output=True, text=True)
print(process.stdout)
print(process.stderr)

