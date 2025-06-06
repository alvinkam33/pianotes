import pretty_midi
import music21 as m21
import os
import sys
import numpy as np

# Constants
VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]  # Whole to 16th notes
DEFAULT_TIME_SIGNATURE = (4, 4)

def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def group_notes_into_measures(notes, measure_duration):
    measures = {}
    for note in notes:
        # Calculate which measure this note starts in
        start_measure = int(note.start / measure_duration)
        
        # Check if the note extends significantly into the next measure
        end_measure = int(note.end / measure_duration)
        
        # If the note extends into the next measure, we need to split it
        if end_measure > start_measure:
            # Calculate the split point at the measure boundary
            split_time = (start_measure + 1) * measure_duration
            
            # Create a copy of the note for the first measure
            first_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start,
                end=split_time
            )
            measures.setdefault(start_measure, []).append(first_note)
            
            # Create a copy of the note for the second measure
            second_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=split_time,
                end=note.end
            )
            measures.setdefault(end_measure, []).append(second_note)
        else:
            measures.setdefault(start_measure, []).append(note)
    
    return measures

def calculate_rhythmic_duration(note_start, next_start, measure_start, measure_end, measure_notes):
    """Calculate note duration considering measure context and neighboring notes."""
    # If this is the last note in the measure, extend to measure end if within threshold
    if next_start is None:
        if measure_end - note_start < 1.5 * (measure_end - measure_start) / len(measure_notes):
            return measure_end - note_start
    
    # Calculate the ideal subdivision based on number of notes in measure
    ideal_subdivision = (measure_end - measure_start) / len(measure_notes)
    
    if next_start is not None:
        actual_duration = next_start - note_start
        # If the actual duration is close to a multiple of the ideal subdivision,
        # adjust to that multiple
        multiple = round(actual_duration / ideal_subdivision)
        if abs(actual_duration - multiple * ideal_subdivision) < ideal_subdivision * 0.2:
            return multiple * ideal_subdivision
    
    return ideal_subdivision

def quantize_notes_in_measure(notes, quarter_note_duration, measure_start, measure_end):
    # Group notes by start time to form chords
    chords = []
    chord = []
    sorted_notes = sorted(notes, key=lambda n: n.start)
    epsilon = quarter_note_duration * 0.1  # Threshold for simultaneous notes
    
    # First pass: group simultaneous notes into chords
    for note in sorted_notes:
        if not chord:
            chord.append(note)
        elif abs(note.start - chord[0].start) < epsilon:
            chord.append(note)
        else:
            chords.append(chord)
            chord = [note]
    if chord:
        chords.append(chord)
    
    # Second pass: calculate durations based on measure context
    quantized = []
    for i, chord in enumerate(chords):
        start_time = chord[0].start
        next_start = chords[i + 1][0].start if i + 1 < len(chords) else None
        
        # Calculate duration considering measure context
        duration = calculate_rhythmic_duration(
            start_time, 
            next_start,
            measure_start,
            measure_end,
            chords
        )
        
        # Convert to quarter note units and round to valid duration
        duration_qn = round_duration(duration / quarter_note_duration)
        quantized.append((start_time, chord, duration_qn))
    
    return quantized

def create_part(measures, clef, quarter_note_duration, measure_duration):
    part = m21.stream.Part()
    part.append(m21.clef.TrebleClef() if clef == 'treble' else m21.clef.BassClef())

    for idx in sorted(measures):
        m = m21.stream.Measure(number=idx + 1)
        quantized_chords = quantize_notes_in_measure(
            measures[idx], 
            quarter_note_duration,
            idx * measure_duration,
            (idx + 1) * measure_duration
        )
        for _, chord_notes, dur in quantized_chords:
            if len(chord_notes) == 1:
                n = m21.note.Note(chord_notes[0].pitch)
            else:
                n = m21.chord.Chord([note.pitch for note in chord_notes])
            n.duration = m21.duration.Duration(dur)
            m.append(n)
        part.append(m)
    return part

def midi_to_musicxml(midi_path, bpm):
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    quarter_note_duration = 60 / bpm
    measure_duration = DEFAULT_TIME_SIGNATURE[0] * quarter_note_duration

    treble_notes, bass_notes = [], []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                (treble_notes if note.pitch >= 60 else bass_notes).append(note)

    treble_measures = group_notes_into_measures(treble_notes, measure_duration)
    bass_measures = group_notes_into_measures(bass_notes, measure_duration)

    score = m21.stream.Score()
    score.append(m21.tempo.MetronomeMark(number=bpm))
    score.append(m21.meter.TimeSignature(f"{DEFAULT_TIME_SIGNATURE[0]}/{DEFAULT_TIME_SIGNATURE[1]}"))
    score.insert(0, create_part(treble_measures, 'treble', quarter_note_duration, measure_duration))
    score.insert(0, create_part(bass_measures, 'bass', quarter_note_duration, measure_duration))

    output_path = f"{os.path.splitext(midi_path)[0]}.musicxml"
    score.write('musicxml', fp=output_path)
    print(f"Exported MusicXML to {output_path}")
    return output_path

# Optional CLI usage
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <midi_file> <bpm>")
    else:
        midi_to_musicxml(sys.argv[1], float(sys.argv[2]))
