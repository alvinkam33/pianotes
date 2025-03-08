import subprocess

# Define file paths
MODEL_DIR = "maestro_checkpoint"
AUDIO_PATH = "test.wav"
OUTPUT_MIDI_PATH = "test.wav.midi"
CLEANED_MIDI_PATH = "output_no_ties_final.mid"
CLEANED_XML_PATH = "output_final_piano_cleaned.musicxml"

command = [
    "onsets_frames_transcription_transcribe",
    f"--model_dir={MODEL_DIR}",
    AUDIO_PATH
]

process = subprocess.run(command, capture_output=True, text=True)
print(process.stdout)
print(process.stderr)
