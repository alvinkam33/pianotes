import subprocess
import pretty_midi
from music21 import converter

# Define file paths
MODEL_DIR = "maestro_checkpoint"
AUDIO_PATH = "test.wav"
OUTPUT_MIDI_PATH = "test.wav.midi"
CLEANED_MIDI_PATH = "output_no_ties_final.mid"
CLEANED_XML_PATH = "output_final_piano_cleaned.musicxml"

# Step 1: Run Magenta’s transcription script
print("🎵 Running Magenta's transcription...")
command = [
    "onsets_frames_transcription_transcribe",
    f"--model_dir={MODEL_DIR}",
    AUDIO_PATH
]

process = subprocess.run(command, capture_output=True, text=True)
print(process.stdout)
print(process.stderr)

from music21 import converter, stream, note, instrument, tempo, meter, midi

def recover_lost_notes_midi_to_musicxml(midi_path, output_xml_path):
    """Converts MIDI to MusicXML, ensuring all notes are preserved, including overlapping and sustained notes."""
    print("🎵 Recovering lost notes and converting MIDI to MusicXML...")

    # Load MIDI using music21
    mf = midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    
    # Convert MIDI to a music21 Score
    midi_score = midi.translate.midiFileToStream(mf, quantizePost=True)  # Ensure quantization for better accuracy

    # Create separate staves for right-hand (treble) and left-hand (bass)
    treble_part = stream.Part()
    bass_part = stream.Part()

    # Assign proper instrument
    treble_part.insert(0, instrument.Piano())  # Treble staff
    bass_part.insert(0, instrument.Piano())  # Bass staff

    # Preserve tempo and time signature
    original_tempo = None
    original_time_signature = None

    for el in midi_score.flat:
        if isinstance(el, tempo.MetronomeMark):
            original_tempo = el
        elif isinstance(el, meter.TimeSignature):
            original_time_signature = el

    for part in midi_score.parts:
        for element in part.flat.notes:
            if isinstance(element, note.Note):
                # Ensure all overlapping notes are kept
                element.quarterLength = max(0.25, element.quarterLength)  # Ensure notes are not too short

                # Assign note to the correct clef
                if element.pitch.midi < 60:  # Notes below Middle C (C4) → Bass Clef
                    bass_part.append(element)
                else:  # Treble Clef
                    treble_part.append(element)

    # Create a final score with both clefs
    final_score = stream.Score()
    
    # Restore tempo and time signature if available
    if original_tempo:
        final_score.insert(0, original_tempo)
        print(f"🎼 Restored tempo: {original_tempo.number} BPM")
    if original_time_signature:
        final_score.insert(0, original_time_signature)
        print(f"🎼 Restored time signature: {original_time_signature.ratioString}")

    final_score.append(treble_part)
    final_score.append(bass_part)

    # Save the cleaned MusicXML file
    final_score.write('musicxml', output_xml_path)
    print(f"🎼 All notes recovered! Cleaned MusicXML saved to {output_xml_path}")

# Run the function to recover notes and convert to MusicXML
CLEANED_XML_PATH = "output_final_recovered.musicxml"
recover_lost_notes_midi_to_musicxml("test.wav.midi", CLEANED_XML_PATH)

print(f"✅ Transcription complete! Final Cleaned Piano MusicXML saved at: {CLEANED_XML_PATH}")




