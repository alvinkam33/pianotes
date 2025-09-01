import pretty_midi
import music21 as m21
import os
import sys

VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]  # Whole to 16th
DEFAULT_TIME_SIGNATURE = (4, 4)
CLEF_DISTANCE_THRESHOLD = 12  # Max pitch distance to prefer a clef
HAND_SWITCH_TIMEOUT = 2.0  # Seconds to allow hand switching


def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))


def assign_notes_to_clefs(all_notes):
    last_pitch = {'treble': None, 'bass': None}
    last_time = {'treble': -float('inf'), 'bass': -float('inf')}
    clef_notes = {'treble': [], 'bass': []}

    for note in all_notes:
        pitch = note.pitch
        time = note.start

        # Pitch distance to last notes
        dist_treble = abs(pitch - last_pitch['treble']) if last_pitch['treble'] is not None else float('inf')
        dist_bass = abs(pitch - last_pitch['bass']) if last_pitch['bass'] is not None else float('inf')

        # Time since last note
        time_since_treble = time - last_time['treble']
        time_since_bass = time - last_time['bass']

        if dist_treble <= dist_bass or time_since_bass > HAND_SWITCH_TIMEOUT:
            clef = 'treble'
        else:
            clef = 'bass'

        clef_notes[clef].append(note)
        last_pitch[clef] = pitch
        last_time[clef] = time

    return clef_notes


def group_notes_into_chords(notes, tolerance=1e-3):
    chords = []
    notes = sorted(notes, key=lambda n: n.start)
    i = 0
    while i < len(notes):
        chord = [notes[i]]
        j = i + 1
        while j < len(notes) and abs(notes[j].start - notes[i].start) < tolerance:
            chord.append(notes[j])
            j += 1
        chords.append(chord)
        i = j
    return chords


def split_chords_by_clef(chords):
    treble_chords = []
    bass_chords = []
    last_pitch = {'treble': None, 'bass': None}
    last_time = {'treble': -float('inf'), 'bass': -float('inf')}

    for chord in chords:
        pitches = [n.pitch for n in chord]
        avg_pitch = sum(pitches) / len(pitches)
        start = chord[0].start

        # Pitch and time distances
        dist_treble = abs(avg_pitch - last_pitch['treble']) if last_pitch['treble'] is not None else float('inf')
        dist_bass = abs(avg_pitch - last_pitch['bass']) if last_pitch['bass'] is not None else float('inf')
        time_since_treble = start - last_time['treble']
        time_since_bass = start - last_time['bass']

        if dist_treble <= dist_bass or time_since_bass > HAND_SWITCH_TIMEOUT:
            treble_chords.append(chord)
            last_pitch['treble'] = avg_pitch
            last_time['treble'] = start
        else:
            bass_chords.append(chord)
            last_pitch['bass'] = avg_pitch
            last_time['bass'] = start

    return treble_chords, bass_chords


def quantize_chords(chords, qn_duration):
    quantized = []
    for i, chord in enumerate(chords):
        start = chord[0].start
        if i + 1 < len(chords):
            end = chords[i + 1][0].start
        else:
            end = start + 2 * qn_duration
        dur = round_duration((end - start) / qn_duration)
        pitches = [n.pitch for n in chord]
        quantized.append((start, pitches, dur))
    return quantized


def create_part(quantized_chords, bpm, clef):
    part = m21.stream.Part()
    part.append(m21.tempo.MetronomeMark(number=bpm))
    part.append(m21.clef.TrebleClef() if clef == 'treble' else m21.clef.BassClef())
    part.append(m21.meter.TimeSignature(f"{DEFAULT_TIME_SIGNATURE[0]}/{DEFAULT_TIME_SIGNATURE[1]}"))

    measure_length = 60 / bpm * DEFAULT_TIME_SIGNATURE[0]
    measure = m21.stream.Measure(number=1)
    current_measure_start = 0

    for start, pitches, dur in quantized_chords:
        if start - current_measure_start >= measure_length:
            part.append(measure)
            measure = m21.stream.Measure(number=measure.number + 1)
            current_measure_start += measure_length

        if len(pitches) == 1:
            n = m21.note.Note(pitches[0])
        else:
            n = m21.chord.Chord(pitches)
        n.duration = m21.duration.Duration(dur)
        measure.append(n)

    part.append(measure)
    return part


def midi_to_musicxml(midi_path):
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    bpm = midi_data.estimate_tempo()
    qn_duration = 60 / bpm

    all_notes = [note for inst in midi_data.instruments if not inst.is_drum for note in inst.notes]
    all_notes.sort(key=lambda n: n.start)

    chords = group_notes_into_chords(all_notes)
    treble_chords, bass_chords = split_chords_by_clef(chords)

    treble_q = quantize_chords(treble_chords, qn_duration)
    bass_q = quantize_chords(bass_chords, qn_duration)

    score = m21.stream.Score()
    score.insert(0, create_part(treble_q, bpm, 'treble'))
    score.insert(0, create_part(bass_q, bpm, 'bass'))

    output_path = os.path.splitext(midi_path)[0] + '_synced.musicxml'
    score.write('musicxml', fp=output_path)
    print(f"Exported to {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python miditoxml.py <midi_file>")
        sys.exit(1)
    midi_to_musicxml(sys.argv[1])
