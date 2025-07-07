import pretty_midi
import music21 as m21
import os
import sys

TREBLE_CUTOFF = 60  # Middle C

def group_notes_by_start_time(notes):
    # Groups notes by their start time to form chords
    notes.sort(key=lambda n: n.start)
    groups = []
    current_group = []

    for note in notes:
        if not current_group or abs(note.start - current_group[0].start) < 1e-3:
            current_group.append(note)
        else:
            groups.append(current_group)
            current_group = [note]
    if current_group:
        groups.append(current_group)

    return groups

def build_part_from_chords(note_groups, clef, qn_duration):
    part = m21.stream.Part()
    part.append(m21.clef.TrebleClef() if clef == 'treble' else m21.clef.BassClef())

    for group in note_groups:
        pitches = [n.pitch for n in group]
        start = group[0].start
        end = min(n.end for n in group)
        duration = (end - start) / qn_duration

        if len(pitches) == 1:
            n = m21.note.Note(pitches[0])
        else:
            n = m21.chord.Chord(pitches)
        n.duration = m21.duration.Duration(duration)
        n.offset = start / qn_duration
        part.append(n)

    return part

def midi_to_musicxml_norounding(midi_path):
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    qn_duration = 60 / midi_data.estimate_tempo()

    treble_notes = []
    bass_notes = []

    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            for note in instrument.notes:
                if note.pitch >= TREBLE_CUTOFF:
                    treble_notes.append(note)
                else:
                    bass_notes.append(note)

    treble_groups = group_notes_by_start_time(treble_notes)
    bass_groups = group_notes_by_start_time(bass_notes)

    treble_part = build_part_from_chords(treble_groups, 'treble', qn_duration)
    bass_part = build_part_from_chords(bass_groups, 'bass', qn_duration)

    score = m21.stream.Score()
    score.insert(0, treble_part)
    score.insert(0, bass_part)
    score.makeMeasures(inPlace=True)  # allow irregular measures

    output_path = os.path.splitext(midi_path)[0] + "_norounding.musicxml"
    score.write('musicxml', fp=output_path)
    print(f"Exported to {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python miditoxml_norounding.py <midi_file>")
        sys.exit(1)
    midi_to_musicxml_norounding(sys.argv[1])
