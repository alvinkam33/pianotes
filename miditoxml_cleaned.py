
import pretty_midi
import music21 as m21
import os
import sys

VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]
DEFAULT_TIME_SIGNATURE = (4, 4)
TREBLE_CUTOFF = 60  # middle C

def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def group_notes_by_measure(notes, beats, beats_per_measure):
    measures = {}
    for note in notes:
        beat_index = max(0, max(i for i, b in enumerate(beats) if b <= note.start))
        measure_index = beat_index // beats_per_measure
        measures.setdefault(measure_index, []).append(note)
    return measures

def quantize_and_trim_chords(notes, beats, beats_per_measure, qn_duration):
    measures = group_notes_by_measure(notes, beats, beats_per_measure)
    result = {}
    for idx in sorted(measures):
        result[idx] = []
        bar_notes = sorted(measures[idx], key=lambda n: n.start)
        i = 0
        while i < len(bar_notes):
            chord_notes = [bar_notes[i]]
            j = i + 1
            while j < len(bar_notes) and abs(bar_notes[j].start - bar_notes[i].start) < 1e-3:
                chord_notes.append(bar_notes[j])
                j += 1
            i = j
            start_time = chord_notes[0].start
            end_time = min(n.end for n in chord_notes)

            if i < len(bar_notes):
                next_start = bar_notes[i].start
                end_time = min(end_time, next_start)

            bar_start = beats[idx * beats_per_measure]
            bar_end = beats[min(len(beats) - 1, (idx + 1) * beats_per_measure)]
            end_time = min(end_time, bar_end)

            duration = round_duration((end_time - start_time) / qn_duration)
            result[idx].append(([note.pitch for note in chord_notes], duration))
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

    treble_notes = []
    bass_notes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                if note.pitch >= TREBLE_CUTOFF:
                    treble_notes.append(note)
                else:
                    bass_notes.append(note)

    treble_measures = quantize_and_trim_chords(treble_notes, beats, beats_per_measure, qn_duration)
    bass_measures = quantize_and_trim_chords(bass_notes, beats, beats_per_measure, qn_duration)

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
