from music21 import converter

musicxml_path = "output_final_cleaned.musicxml"

# parse MusicXML file to ensure it is not corrupted
try:
    score = converter.parse(musicxml_path)
    print("✅ MusicXML file is valid and parsed successfully.")
except Exception as e:
    print(f"❌ MusicXML file has errors: {str(e)}")
