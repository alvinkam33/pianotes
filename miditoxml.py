import pretty_midi
import music21 as m21

# Input and output files
midi_file = "test.wav.midi"
output_musicxml = f'{midi_file}.musicxml'

# define valid note durations (whole, half, quarter, etc.)
VALID_DURATIONS = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625]
MIN_VALID_DURATION = 0.0625  # prevents ultra-short "2048th" notes (causing conversion error)

USER_TEMPO = float(input("Enter the intended tempo (BPM) or 0 to auto-detect: "))
print("running midi to musicxml conversion")

def round_duration(duration):
    return min(VALID_DURATIONS, key=lambda x: abs(x - duration))

def parse_midi_events(midi_path, user_tempo):
    midi = pretty_midi.PrettyMIDI(midi_path)

    # extract tempo from user input
    if user_tempo > 0:
        tempo = user_tempo
    else:
        tempo_changes = midi.get_tempo_changes()
        tempo = tempo_changes[1][0] if len(tempo_changes[1]) > 0 else 120

    notes_by_time = {}

    for instrument in midi.instruments:
        for note in instrument.notes:
            start_time = note.start
            end_time = note.end
            raw_duration = end_time - start_time 

            quarter_length = (raw_duration * tempo) / 60.0

            if quarter_length < MIN_VALID_DURATION:
                quarter_length = MIN_VALID_DURATION

            quarter_length = round_duration(quarter_length)

            if start_time not in notes_by_time:
                notes_by_time[start_time] = []
            notes_by_time[start_time].append((note.pitch, quarter_length, note.velocity))

    return notes_by_time, tempo

def fit_notes_to_measures(notes_by_time, tempo):
    fitted_notes = {}
    for start_time, notes in notes_by_time.items():
        fitted_notes[start_time] = []
        for pitch, duration, velocity in notes:
            fitted_notes[start_time].append((pitch, duration, velocity))

    return fitted_notes

def construct_musicxml(notes_by_time, tempo, output_xml):
    score = m21.stream.Score()
    treble_part = m21.stream.Part()
    bass_part = m21.stream.Part()

    tempo_mark = m21.tempo.MetronomeMark(number=int(tempo))
    score.insert(0, tempo_mark)

    for start_time in sorted(notes_by_time.keys()):
        for pitch, quarter_length, _ in notes_by_time[start_time]:
            new_note = m21.note.Note(pitch)
            new_note.quarterLength = quarter_length

            # assign to treble or bass clef
            if pitch < 60:
                bass_part.append(new_note)
            else:
                treble_part.append(new_note)

    treble_part.insert(0, m21.clef.TrebleClef())
    bass_part.insert(0, m21.clef.BassClef())

    score.append(treble_part)
    score.append(bass_part)

    score.write("musicxml", output_xml)
    print("processed midi to musicxml", output_musicxml)

notes_by_time, tempo = parse_midi_events(midi_file, USER_TEMPO)
fitted_notes = fit_notes_to_measures(notes_by_time, tempo)
construct_musicxml(fitted_notes, tempo, output_musicxml)
