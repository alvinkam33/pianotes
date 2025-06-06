import pretty_midi
import music21 as m21
import os
import sys

# Constants
VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]  # Whole to 16th notes
DEFAULT_TIME_SIGNATURE = (4, 4)

def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def group_notes_into_measures(notes, measure_duration):
    measures = {}
    for note in notes:
        start_measure = int(note.start / measure_duration)
        measures.setdefault(start_measure, []).append(note)
    return measures

def quantize_notes_in_measure(notes, quarter_note_duration):
    # Group notes by start time to form chords
    chords = []
    chord = []
    sorted_notes = sorted(notes, key=lambda n: n.start)
    epsilon = 1e-3  # small threshold to group simultaneous notes
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

    quantized = []
    for i, chord in enumerate(chords):
        start_time = chord[0].start
        end_time = min(n.end for n in chord)
        if i + 1 < len(chords):
            next_start = chords[i + 1][0].start
            end_time = min(end_time, next_start)
        duration_qn = round_duration((end_time - start_time) / quarter_note_duration)
        quantized.append((start_time, chord, duration_qn))
    return quantized

def create_part(measures, clef, quarter_note_duration, measure_duration):
    part = m21.stream.Part()
    part.append(m21.clef.TrebleClef() if clef == 'treble' else m21.clef.BassClef())

    for idx in sorted(measures):
        m = m21.stream.Measure(number=idx + 1)
        quantized_chords = quantize_notes_in_measure(measures[idx], quarter_note_duration)
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
