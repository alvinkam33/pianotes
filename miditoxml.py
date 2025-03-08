import pretty_midi
import music21 as m21

# Input and output files
midi_file = "test.wav.midi"
output_musicxml = "output_final_corrected.musicxml"

# User-defined tempo (optional)
USER_TEMPO = float(input("Enter the intended tempo (BPM) or 0 to auto-detect: "))

def parse_midi_events(midi_path, user_tempo):
    """Reads MIDI events and extracts precise note placements."""
    print(f"🎵 Reading MIDI file: {midi_path}")
    midi = pretty_midi.PrettyMIDI(midi_path)

    # Extract tempo (or use user input)
    if user_tempo > 0:
        tempo = user_tempo
    else:
        tempo_changes = midi.get_tempo_changes()
        tempo = tempo_changes[1][0] if len(tempo_changes[1]) > 0 else 120  # Default to 120 BPM

    print(f"🎼 Using tempo: {tempo} BPM")

    # Store notes per clef and timestamp
    treble_notes = []
    bass_notes = []

    for instrument in midi.instruments:
        for note in instrument.notes:
            start_time = note.start
            end_time = note.end
            duration = end_time - start_time  # True duration

            # Convert to quarter note length
            quarter_length = duration * (tempo / 60)

            # Assign to treble or bass clef
            if note.pitch < 60:  # Below middle C → Bass Clef
                bass_notes.append((start_time, note.pitch, quarter_length, note.velocity))
            else:
                treble_notes.append((start_time, note.pitch, quarter_length, note.velocity))

    return treble_notes, bass_notes, tempo

def adjust_note_durations(notes):
    """Ensures each note starts at the correct time by trimming previous notes."""
    adjusted_notes = []
    last_end_time = {}

    for start_time, pitch, duration, velocity in sorted(notes):
        # Ensure note starts at correct time
        if pitch in last_end_time and start_time < last_end_time[pitch]:
            # Trim the previous note's duration so this note starts correctly
            prev_start, prev_pitch, prev_duration, prev_velocity = adjusted_notes[-1]
            trimmed_duration = start_time - prev_start
            adjusted_notes[-1] = (prev_start, prev_pitch, max(0.1, trimmed_duration), prev_velocity)  # Min duration 0.1

        # Store new note
        adjusted_notes.append((start_time, pitch, duration, velocity))
        last_end_time[pitch] = start_time + duration  # Update last end time

    return adjusted_notes

def construct_musicxml(treble_notes, bass_notes, tempo, output_xml):
    """Constructs a MusicXML file with corrected note placement."""
    print(f"🎼 Constructing MusicXML with accurate note placement...")

    score = m21.stream.Score()
    treble_part = m21.stream.Part()
    bass_part = m21.stream.Part()

    # Add tempo marking
    tempo_mark = m21.tempo.MetronomeMark(number=int(tempo))
    score.insert(0, tempo_mark)

    # Process notes into MusicXML
    for note_list, part in [(treble_notes, treble_part), (bass_notes, bass_part)]:
        for start_time, pitch, quarter_length, velocity in note_list:
            new_note = m21.note.Note(pitch)
            new_note.quarterLength = quarter_length  # Prioritized length
            part.append(new_note)

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
treble_notes, bass_notes, tempo = parse_midi_events(midi_file, USER_TEMPO)
adjusted_treble = adjust_note_durations(treble_notes)
adjusted_bass = adjust_note_durations(bass_notes)
construct_musicxml(adjusted_treble, adjusted_bass, tempo, output_musicxml)
