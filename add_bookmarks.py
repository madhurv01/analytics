import fitz  # PyMuPDF
import json
import sys

def add_bookmarks_to_pdf(pdf_input_path, json_input_path, pdf_output_path):
    """
    Takes a PDF and a JSON outline, and creates a new PDF with bookmarks.
    """
    try:
        # Load the JSON outline we created earlier
        with open(json_input_path, 'r', encoding='utf-8') as f:
            # --- THIS IS THE CORRECTED LINE ---
            data = json.load(f)  # Load from the file object 'f', not the non-existent 'data'
        
        outline = data.get("outline", [])
        if not outline:
            print("No outline data found in JSON. Exiting.")
            return

        # PyMuPDF uses a list of lists for its table of contents (TOC)
        # Format: [level, title, page_number]
        toc = []
        for item in outline:
            level = int(item['level'].replace('H', '')) # Convert 'H1' to 1
            title = item['text']
            page = item['page']
            toc.append([level, title, page])

        # Open the original PDF
        doc = fitz.open(pdf_input_path)

        # Set the table of contents
        doc.set_toc(toc)

        # Save the new PDF with bookmarks
        doc.save(pdf_output_path)
        print(f"Successfully created '{pdf_output_path}' with bookmarks.")

    except FileNotFoundError:
        print(f"Error: The file '{json_input_path}' or '{pdf_input_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file '{json_input_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Example Usage:
    # python add_bookmarks.py input/sample_numbered.pdf output/sample_numbered.json output/sample_numbered_bookmarked.pdf
    if len(sys.argv) != 4:
        print("Usage: python add_bookmarks.py <input_pdf> <input_json> <output_pdf>")
        sys.exit(1)
    
    add_bookmarks_to_pdf(sys.argv[1], sys.argv[2], sys.argv[3])