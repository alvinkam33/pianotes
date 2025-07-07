
import pretty_midi
import music21 as m21
import os
import sys

VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]
DEFAULT_TIME_SIGNATURE = (4, 4)
TREBLE_CUTOFF = 60  # middle C

def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def group_notes_by_measure(notes, beats, beats_per_measure, first_note_start):
    measures = {}
    for note in notes:
        note.start = note.start - first_note_start
        beat_index = max(0, max(i for i, b in enumerate(beats) if b <= note.start))
        measure_index = beat_index // beats_per_measure
        measures.setdefault(measure_index, []).append(note)
    return measures

def quantize_and_trim_chords(notes, beats, beats_per_measure, qn_duration, first_note_start):
    # Group notes into measures first
    measures = group_notes_by_measure(notes, beats, beats_per_measure, first_note_start)
    result = {}

    # Flatten all notes into a global ordered list
    all_notes = []
    for idx in sorted(measures):
        all_notes.extend(sorted(measures[idx], key=lambda n: n.start))

    # Group into chords (same start time)
    chords = []
    i = 0
    while i < len(all_notes):
        chord = [all_notes[i]]
        j = i + 1
        while j < len(all_notes) and abs(all_notes[j].start - chord[0].start) < 1e-3:
            chord.append(all_notes[j])
            j += 1
        chords.append(chord)
        i = j

    # Quantize chord durations based on next chord start
    for chord_index, chord_notes in enumerate(chords):
        start_time = chord_notes[0].start
        if chord_index + 1 < len(chords):
            next_start = chords[chord_index + 1][0].start
            effective_end = next_start
        else:
            # no next note — cap max length for final note
            effective_end = start_time + 2 * qn_duration  # 2 beats max

        # Get pitches
        pitches = [note.pitch for note in chord_notes]
        duration = round_duration((effective_end - start_time) / qn_duration)
        # Assign to appropriate measure
        beat_index = max(0, max(i for i, b in enumerate(beats) if b <= start_time))
        measure_index = beat_index // beats_per_measure
        result.setdefault(measure_index, []).append((pitches, duration))

    return result



def create_part(measured_chords, clef):
    part = m21.stream.Part()
    part.append(m21.clef.TrebleClef() if clef == 'treble' else m21.clef.BassClef())
    for idx in sorted(measured_chords):
        measure = m21.stream.Measure(number=idx + 1)
        for pitches, duration in measured_chords[idx]:
            if len(pitches) == 1:
                n = m21.note.Note(pitches[0])
            else:
                n = m21.chord.Chord(pitches)
            n.duration = m21.duration.Duration(duration)
            measure.append(n)
        part.append(measure)
    return part

def midi_to_musicxml_clip_duration(midi_path):
    midi_data = pretty_midi.PrettyMIDI(midi_path)

    beats = midi_data.get_beats()
    bpm = midi_data.estimate_tempo()
    beats_per_measure = DEFAULT_TIME_SIGNATURE[0]
    qn_duration = 60 / bpm

    first_note_start = float('inf')

    treble_notes = []
    bass_notes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                first_note_start = min(first_note_start, note.start)
                if note.pitch >= TREBLE_CUTOFF:
                    treble_notes.append(note)
                else:
                    bass_notes.append(note)

    treble_measures = quantize_and_trim_chords(treble_notes, beats, beats_per_measure, qn_duration, first_note_start)
    bass_measures = quantize_and_trim_chords(bass_notes, beats, beats_per_measure, qn_duration, first_note_start)

    score = m21.stream.Score()
    score.append(m21.tempo.MetronomeMark(number=bpm))
    score.append(m21.meter.TimeSignature(f"{DEFAULT_TIME_SIGNATURE[0]}/{DEFAULT_TIME_SIGNATURE[1]}"))
    score.append(create_part(treble_measures, 'treble'))
    score.append(create_part(bass_measures, 'bass'))

    output_path = os.path.splitext(midi_path)[0] + "_cleaned.musicxml"
    score.write('musicxml', fp=output_path)
    print(f"Exported cleaned MusicXML to {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python miditoxml.py <midi_file>")
        sys.exit(1)
    midi_to_musicxml_clip_duration(sys.argv[1])
