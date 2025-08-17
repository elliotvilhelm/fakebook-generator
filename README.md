# PDF Music Book Generator

Merges multiple PDF files into a single document with cover page, table of contents, and bookmarks.

## Usage

```bash
python main.py OUTPUT.pdf INPUT_DIR
```

Examples:
```bash
python main.py fiddle_tunes.pdf static/tunes
```

## Setup

```bash
pip install -r requirements.txt
```

## File Structure

```
pdf-music/
├── main.py              # Main script
├── static/
│   ├── cover.png       # Cover image (used automatically if present)
│   └── tunes/          # Your PDF files to merge
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Notes

- Put cover image at `static/cover.png` (optional)
- PDFs merged alphabetically 
- Creates TOC and bookmarks automatically 