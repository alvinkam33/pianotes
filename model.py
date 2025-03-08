import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import os

from magenta.models.onsets_frames_transcription import configs
from magenta.models.onsets_frames_transcription import onsets_frames_transcription_transcribe as transcribe
from magenta.music import midi_io
from music21 import converter

# Paths
MODEL_DIR = "maestro_checkpoint"  # Replace with the actual checkpoint path
AUDIO_PATH = "test.wav"           # Replace with your audio file
OUTPUT_MIDI_PATH = "output.mid"   # Path to save the output MIDI file
OUTPUT_SHEET_MUSIC_PATH = "output_sheet_music.xml"  # Path to save the sheet music

# Load the model configuration
config = configs.CONFIG_MAP["onsets_frames"]
hparams = config.hparams
hparams.use_cudnn = False  # Disable CuDNN if not using a GPU

# Create a TensorFlow session
with tf.Session() as sess:
    # 🔹 Restore the model from the latest checkpoint
    checkpoint = tf.train.latest_checkpoint(MODEL_DIR)
    if not checkpoint:
        raise FileNotFoundError(f"No checkpoint found in {MODEL_DIR}")
    
    print(f"Using checkpoint: {checkpoint}")

    # 🔹 Use `transcribe` module to run inference
    sequence_prediction = transcribe.infer_util(AUDIO_PATH, checkpoint, hparams)

    # 🔹 Save the predictions as a MIDI file
    midi_io.sequence_proto_to_midi_file(sequence_prediction, OUTPUT_MIDI_PATH)

# Convert MIDI to sheet music
score = converter.parse(OUTPUT_MIDI_PATH)
score.write('musicxml', fp=OUTPUT_SHEET_MUSIC_PATH)

print(f"Sheet music saved to {OUTPUT_SHEET_MUSIC_PATH}")
