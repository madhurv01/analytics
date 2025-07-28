import os
import json
import re
from collections import Counter
import fitz  # PyMuPDF

# --- Configuration ---
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

# Heuristic parameters
MIN_HEADING_WORD_COUNT = 1  # Lowered to 1 to catch single-word headings like "Introduction"
MAX_HEADING_WORD_COUNT = 20
HEADER_FOOTER_MARGIN = 50
MIN_FONT_SIZE_INCREASE = 1.05

# --- Feature Engineering Helpers ---

def get_numbering_info(text):
    """Checks for numbering like '1.', '1.1', 'A.' etc."""
    match = re.match(r'^([A-Z]|\d+(\.\d+)*)\.?\s+', text)
    if match:
        numbering = match.group(1)
        depth = numbering.count('.') + (1 if re.match(r'^[A-Z]$', numbering) else 0)
        return {"numbering": numbering, "depth": depth + 1}
    return None

def is_bold(font_name):
    """Checks if font name suggests it's bold."""
    return any(x in font_name.lower() for x in ['bold', 'black', 'heavy', 'cmb'])

def get_text_case(text):
    """Determines the case of the text."""
    if text.isupper():
        return "UPPER"
    if text.istitle():
        return "TITLE"
    return "SENTENCE"

# --- Main Extraction Pipeline ---

def extract_features(doc):
    """Extracts raw text blocks from a PDF document along with rich features."""
    blocks = []
    for page_num, page in enumerate(doc):
        page_height = page.rect.height
        # Use flags=4 for backward compatibility with older PyMuPDF versions
        page_blocks = page.get_text("dict", flags=4) 
        
        for block in page_blocks["blocks"]:
            if "lines" not in block:
                continue
            
            full_text = " ".join([span['text'] for line in block['lines'] for span in line['spans']]).strip()
            if not full_text:
                continue

            first_span = block["lines"][0]["spans"][0]
            bbox = block["bbox"]
            
            if bbox[1] < HEADER_FOOTER_MARGIN or bbox[3] > page_height - HEADER_FOOTER_MARGIN:
                continue

            word_count = len(full_text.split())

            blocks.append({
                "text": full_text,
                "page": page_num + 1,
                "size": first_span["size"],
                "font": first_span["font"],
                "color": first_span["color"],
                "bold": is_bold(first_span["font"]),
                "case": get_text_case(full_text),
                "numbering": get_numbering_info(full_text),
                "word_count": word_count,
                "bbox": bbox
            })
    return blocks

def identify_body_text_size(blocks):
    """
    Identifies the most common font size, assumed to be the body text.
    This is a more robust approach.
    """
    if not blocks:
        return 10.0  # Default fallback

    # Count all font sizes, rounded to nearest integer
    sizes = [round(b['size']) for b in blocks]
    if not sizes:
        return 10.0

    # The most common size is very likely the body text
    most_common_size = Counter(sizes).most_common(1)[0][0]
    return float(most_common_size)

def classify_headings(blocks, body_text_size):
    """
    Classifies blocks into H1, H2, H3.
    This logic has been refactored for clarity and correctness.
    """
    # 1. First, find all potential heading candidates
    heading_candidates = []
    for b in blocks:
        is_potential_heading = (
            b['size'] > body_text_size and
            MIN_HEADING_WORD_COUNT <= b['word_count'] <= MAX_HEADING_WORD_COUNT and
            not b['text'].strip().endswith('.')
        )
        if is_potential_heading:
            heading_candidates.append(b)

    # 2. Identify unique heading styles (size, bold) from the candidates
    heading_styles = sorted(
        list(set((round(b['size']), b['bold']) for b in heading_candidates)),
        key=lambda x: x[0],
        reverse=True
    )
    
    # 3. Map the top 3 styles to H1, H2, H3
    style_to_level = {style: f"H{i+1}" for i, style in enumerate(heading_styles[:3])}
    if not style_to_level:
        return [] # No valid heading styles found

    # 4. Classify and build the outline in a single pass
    outline = []
    for b in heading_candidates:
        level = None
        # Priority 1: Numbering is the most reliable signal
        if b['numbering'] and b['numbering']['depth'] <= 3:
            level = f"H{b['numbering']['depth']}"
        # Priority 2: Style-based classification
        else:
            style = (round(b['size']), b['bold'])
            if style in style_to_level:
                level = style_to_level[style]

        if level:
            outline.append({"level": level, "text": b['text'], "page": b['page']})

    return outline

def find_title(doc, blocks):
    """Finds the document title."""
    if doc.metadata and doc.metadata['title']:
        return doc.metadata['title']

    first_page_blocks = [b for b in blocks if b['page'] == 1]
    if not first_page_blocks:
        return "Untitled Document"
    
    # Sort by size, then by vertical position (y-coordinate) to find the topmost largest text
    first_page_blocks.sort(key=lambda b: (b['size'], -b['bbox'][1]), reverse=True)
    return first_page_blocks[0]['text']

def process_pdf(pdf_path):
    """Main function to process a single PDF and return its structured outline."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return None

    all_blocks = extract_features(doc)
    body_size = identify_body_text_size(all_blocks)
    title = find_title(doc, all_blocks)
    headings = classify_headings(all_blocks, body_size)

    return {
        "title": title,
        "outline": headings
    }

def main():
    """Entry point of the script."""
    input_dir = "input" if "input" in os.listdir('.') else INPUT_DIR
    output_dir = "output" if "input" in os.listdir('.') else OUTPUT_DIR

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Scanning for PDF files in '{input_dir}'...")
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing '{filename}'...")

            result = process_pdf(pdf_path)

            if result:
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"Successfully generated '{output_filename}'")

if __name__ == "__main__":
    main()