#!/usr/bin/env python3
"""
Merge all PDFs in a directory (non-recursive), prepend a cover page and Table of Contents,
and add clickable bookmarks for each source PDF.

Usage:
  python main.py OUTPUT.pdf INPUT_DIR
"""

import os
import sys
import glob
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from PIL import Image


def make_cover_pdf(cover_image_path):
    """
    Create a cover page with the provided image.
    Returns a PdfReader over the in-memory PDF.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    page_w, page_h = letter

    if os.path.exists(cover_image_path):
        try:
            # Open image to get dimensions
            img = Image.open(cover_image_path)
            img_w, img_h = img.size

            # Calculate scaling to fit the page while maintaining aspect ratio
            scale = min(page_w / img_w, page_h / img_h)
            new_w = img_w * scale
            new_h = img_h * scale

            # Center the image on the page
            x = (page_w - new_w) / 2
            y = (page_h - new_h) / 2

            # Draw the image
            c.drawImage(
                cover_image_path,
                x,
                y,
                width=new_w,
                height=new_h,
                preserveAspectRatio=True,
            )
        except Exception as e:
            print(f"Warning: Could not add cover image: {e}")
            # Fallback to a simple title page
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(page_w / 2, page_h / 2, "Document Collection")
    else:
        # Fallback if no cover image
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(page_w / 2, page_h / 2, "Document Collection")

    c.save()
    buf.seek(0)
    return PdfReader(buf)


def make_toc_pdf(entries):
    """
    Build a beautiful multi-page TOC PDF from (display_name, start_page) entries.
    Returns a PdfReader over the in-memory PDF.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    page_w, page_h = letter
    margin = 0.9 * inch
    right_margin = page_w - margin
    y = page_h - margin

    # Color scheme
    primary_color = HexColor("#2C3E50")  # Dark blue-gray
    accent_color = HexColor("#3498DB")  # Light blue
    text_color = HexColor("#34495E")  # Gray

    c.setTitle("Table of Contents")

    # Draw header with decorative line
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(margin, y, "Table of Contents")
    y -= 0.3 * inch

    # Draw decorative line under header
    c.setStrokeColor(accent_color)
    c.setLineWidth(2)
    c.line(margin, y, margin + 200, y)
    y -= 0.5 * inch

    # Reset for entries
    c.setFillColor(text_color)
    c.setStrokeColor(text_color)
    c.setLineWidth(0.5)

    page_num = 1
    for idx, (name, start_page) in enumerate(entries):
        # Check if we need a new page
        if y < margin + 0.5 * inch:
            # Add page number at bottom
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#95A5A6"))
            c.drawCentredString(page_w / 2, 0.5 * inch, f"- {page_num} -")

            c.showPage()
            page_num += 1
            y = page_h - margin

            # Re-add header on new pages
            c.setFillColor(primary_color)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(margin, y, "Table of Contents (continued)")
            y -= 0.15 * inch

            # Decorative line
            c.setStrokeColor(accent_color)
            c.setLineWidth(1)
            c.line(margin, y, margin + 150, y)
            y -= 0.4 * inch

            # Reset colors for entries
            c.setFillColor(text_color)
            c.setStrokeColor(text_color)
            c.setLineWidth(0.5)

        # Alternate background for readability
        if idx % 2 == 0:
            c.setFillColor(HexColor("#ECF0F1"))
            c.rect(
                margin - 10,
                y - 5,
                right_margin - margin + 20,
                0.28 * inch,
                fill=1,
                stroke=0,
            )
            c.setFillColor(text_color)

        # Clean up filename for display (remove .pdf extension)
        display_name = name.replace(".pdf", "").replace("_", " ")

        # Draw entry name
        c.setFont("Helvetica", 11)
        c.drawString(margin, y, display_name)

        # Draw dotted line
        dot_start_x = margin + c.stringWidth(display_name, "Helvetica", 11) + 10
        dot_end_x = right_margin - 40

        if dot_start_x < dot_end_x:
            c.setDash([2, 4])
            c.line(dot_start_x, y + 3, dot_end_x, y + 3)
            c.setDash([])

        # Draw page number with nice formatting
        c.setFont("Helvetica-Bold", 11)
        page_str = str(start_page)
        c.drawRightString(right_margin, y, page_str)

        y -= 0.32 * inch

    # Add page number at bottom of last page
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#95A5A6"))
    c.drawCentredString(page_w / 2, 0.5 * inch, f"- {page_num} -")

    c.save()
    buf.seek(0)
    return PdfReader(buf)


def merge_with_index(output_path, pdf_paths):
    """
    Merge given PDFs (already sorted), add cover, TOC page(s) and bookmarks.
    """
    writer = PdfWriter()

    # Path to cover image
    cover_path = os.path.join(os.path.dirname(__file__), "static", "cover.png")

    # Read PDFs and compute starting pages (for human-readable TOC)
    entries = []
    readers = []
    page_cursor = 0  # counts pages before cover and TOC are inserted
    for p in pdf_paths:
        try:
            r = PdfReader(p)
        except Exception as e:
            print(f"WARNING: Skipping '{p}' ({e})")
            continue
        readers.append((os.path.basename(p), r))
        entries.append((os.path.basename(p), page_cursor + 1))
        page_cursor += len(r.pages)

    if not readers:
        raise RuntimeError("No readable PDFs to merge.")

    # Build and add cover page first
    cover_pdf = make_cover_pdf(cover_path)
    cover_pages = len(cover_pdf.pages)
    for i in range(cover_pages):
        writer.add_page(cover_pdf.pages[i])

    # Build and add TOC PDF
    toc_pdf = make_toc_pdf(entries)
    toc_pages = len(toc_pdf.pages)
    for i in range(toc_pages):
        writer.add_page(toc_pdf.pages[i])

    # Add bookmarks for cover and TOC
    writer.add_outline_item(title="Cover", page_number=0)
    writer.add_outline_item(title="Table of Contents", page_number=cover_pages)

    # Append all PDFs and add bookmarks at their actual start pages
    running_index = cover_pages + toc_pages  # writer uses 0-based page indices
    for name, reader in readers:
        # Clean up name for bookmark
        bookmark_name = name.replace(".pdf", "").replace("_", " ")
        # Add a top-level bookmark for this document
        writer.add_outline_item(title=bookmark_name, page_number=running_index)

        for page in reader.pages:
            writer.add_page(page)
        running_index += len(reader.pages)

    # Write output file
    with open(output_path, "wb") as f:
        writer.write(f)


def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py OUTPUT.pdf INPUT_DIR")
        sys.exit(1)

    out_path = sys.argv[1]
    in_dir = sys.argv[2]

    if not os.path.isdir(in_dir):
        print(f"Error: '{in_dir}' is not a directory")
        sys.exit(1)

    pdfs = sorted(glob.glob(os.path.join(in_dir, "*.pdf")))
    if not pdfs:
        print(f"No PDFs found in {in_dir}")
        sys.exit(1)

    print(f"Merging {len(pdfs)} PDFs from '{in_dir}' → '{out_path}'")
    print(f"Adding cover page and beautiful Table of Contents...")
    merge_with_index(out_path, pdfs)
    print("Done. Your beautiful PDF is ready!")


if __name__ == "__main__":
    main()
