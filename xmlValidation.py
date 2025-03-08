from music21 import converter

musicxml_path = "output_final_cleaned.musicxml"  # Replace with your actual file path

# Attempt to parse the MusicXML file with music21
try:
    score = converter.parse(musicxml_path)
    print("✅ MusicXML file is valid and parsed successfully.")
except Exception as e:
    print(f"❌ MusicXML file has errors: {str(e)}")
