import pretty_midi
import music21 as m21

# Input and output files
midi_file = "test.wav.midi"
output_musicxml = "output_final_fixed.musicxml"

# Define valid note durations (whole, half, quarter, etc.)
VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625]  # Whole, Half, Quarter, 8th, 16th, 32nd, 64th
MIN_VALID_DURATION = 0.0625  # Prevents ultra-short "2048th" notes

# Ask the user for tempo (optional)
USER_TEMPO = float(input("Enter the intended tempo (BPM) or 0 to auto-detect: "))

def round_duration(duration):
    """Rounds a note's duration to the nearest valid value."""
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def parse_midi_events(midi_path, user_tempo):
    """Reads MIDI events and extracts precise note timings."""
    print(f"🎵 Reading MIDI file: {midi_path}")
    midi = pretty_midi.PrettyMIDI(midi_path)

    # Extract tempo (or use user input)
    if user_tempo > 0:
        tempo = user_tempo
    else:
        tempo_changes = midi.get_tempo_changes()
        tempo = tempo_changes[1][0] if len(tempo_changes[1]) > 0 else 120  # Default to 120 BPM

    print(f"🎼 Using tempo: {tempo} BPM")

    # Store notes per timestamp
    notes_by_time = {}

    for instrument in midi.instruments:
        for note in instrument.notes:
            start_time = note.start
            end_time = note.end
            raw_duration = end_time - start_time  # Use exact duration

            # Convert to quarter note length
            quarter_length = raw_duration * (tempo / 60)  # Align timing with tempo

            # Ensure duration is valid
            if quarter_length < MIN_VALID_DURATION:
                quarter_length = MIN_VALID_DURATION  # Set to minimum valid duration

            quarter_length = round_duration(quarter_length)  # Round to the nearest valid note

            if start_time not in notes_by_time:
                notes_by_time[start_time] = []
            notes_by_time[start_time].append((note.pitch, quarter_length, note.velocity))

    return notes_by_time, tempo

def fit_notes_to_measures(notes_by_time, tempo):
    """Ensures notes fit correctly into measures based on tempo."""
    quarter_note_length = 60.0 / tempo  # One quarter note duration in seconds

    # Convert raw durations into music21-compatible quarter lengths
    fitted_notes = {}
    for start_time, notes in notes_by_time.items():
        fitted_notes[start_time] = []
        for pitch, duration, velocity in notes:
            fitted_notes[start_time].append((pitch, duration, velocity))

    return fitted_notes

def construct_musicxml(notes_by_time, tempo, output_xml):
    """Constructs a MusicXML file while ensuring note timing accuracy."""
    print(f"🎼 Constructing MusicXML with corrected timing...")

    score = m21.stream.Score()
    treble_part = m21.stream.Part()
    bass_part = m21.stream.Part()

    # Add tempo marking
    tempo_mark = m21.tempo.MetronomeMark(number=int(tempo))
    score.insert(0, tempo_mark)

    # Process notes
    for start_time in sorted(notes_by_time.keys()):
        for pitch, quarter_length, velocity in notes_by_time[start_time]:
            new_note = m21.note.Note(pitch)
            new_note.quarterLength = quarter_length  # Validated duration

            # Assign to treble or bass clef
            if pitch < 60:  # Below middle C → Bass Clef
                bass_part.append(new_note)
            else:
                treble_part.append(new_note)

    # Assign clefs
    treble_part.insert(0, m21.clef.TrebleClef())
    bass_part.insert(0, m21.clef.BassClef())

    # Add parts to score
    score.append(treble_part)
    score.append(bass_part)

    # Export to MusicXML
    print(f"📄 Exporting to MusicXML: {output_xml}")
    score.write("musicxml", output_xml)
    print("✅ Processing complete! Open the file in MuseScore.")

# Run processing
notes_by_time, tempo = parse_midi_events(midi_file, USER_TEMPO)
fitted_notes = fit_notes_to_measures(notes_by_time, tempo)
construct_musicxml(fitted_notes, tempo, output_musicxml)
