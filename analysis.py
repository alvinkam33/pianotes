# Reattempt tempo analysis now that pretty_midi is installed
import pretty_midi

# Define file paths
original_midi_path = "test.wav.midi"
cleaned_midi_path = "output_cleaned.mid"

# Load the MIDI files
original_midi = pretty_midi.PrettyMIDI(original_midi_path)
cleaned_midi = pretty_midi.PrettyMIDI(cleaned_midi_path)

# Extract tempo changes
original_tempo_times, original_tempo_bpm = original_midi.get_tempo_changes()
cleaned_tempo_times, cleaned_tempo_bpm = cleaned_midi.get_tempo_changes()

# Get first tempo value if available
original_tempo_value = original_tempo_bpm[0] if len(original_tempo_bpm) > 0 else "Unknown"
cleaned_tempo_value = cleaned_tempo_bpm[0] if len(cleaned_tempo_bpm) > 0 else "Unknown"

# Extract MIDI duration
original_duration = original_midi.get_end_time()
cleaned_duration = cleaned_midi.get_end_time()

# Output findings
tempo_analysis = {
    "Original Tempo (BPM)": original_tempo_value,
    "Cleaned Tempo (BPM)": cleaned_tempo_value,
    "Original MIDI Duration (Seconds)": original_duration,
    "Cleaned MIDI Duration (Seconds)": cleaned_duration
}

print(tempo_analysis)
