from pathlib import Path


FIXTURES_DIR = Path(__file__).parents[0]

# These fixtures taken from `sands` repo, location: `sands/tests/fixtures/ingest_example_files/john_stevens/`
john_stevens_txt_filepath = Path(FIXTURES_DIR, 'john-stevens.pdf.txt')
john_stevens_text_lines_filepath = Path(FIXTURES_DIR, 'john-stevens.text_lines.json')
john_stevens_text_coords_filepath = Path(FIXTURES_DIR, 'john-stevens.text_coordinates.json')
