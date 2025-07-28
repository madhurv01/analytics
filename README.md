
# PDF Outline Extractor - Hackathon Solution

This project provides a solution for extracting a structured outline (Title, H1, H2, H3) from PDF documents.

## Approach

The solution uses a heuristic-based feature extraction pipeline built with Python. It avoids large machine learning models to remain lightweight and fast, adhering to the competition constraints. The core logic is as follows:

1.  **PDF Parsing**: The `PyMuPDF` library is used to parse the PDF and extract all text blocks along with their low-level properties (text, font size, font name, color, and position).

2.  **Feature Engineering**: For each text block, a rich set of features is calculated:
    *   **Font Style**: Boldness, relative font size (compared to the document's main body text), and text case (UPPER, Title).
    *   **Structural Cues**: Checks for heading-like numbering (e.g., "1.2", "A.1") to directly determine hierarchy level.
    *   **Positional Filtering**: Text in common header/footer areas is identified and filtered out to reduce noise.
    *   **Content Cues**: Word count is used to filter out long paragraphs.

3.  **Classification Logic**:
    *   **Title**: The title is identified first from the PDF metadata, falling back to the largest text on the first page.
    *   **Body Text Identification**: The most common font style (size and name) is identified as the body text, establishing a baseline.
    *   **Heading Classification**: A block is classified as a heading if it meets certain criteria (e.g., larger font size than body, concise word count). The levels (H1, H2, H3) are determined primarily by a combination of numbering depth and a ranked list of font styles. Numbering (e.g., "2.1.3") is treated as the most reliable signal, overriding style-based guesses.

This approach is robust because it doesn't rely on a single feature like font size, but rather a weighted combination of multiple strong indicators of document structure.

## Models or Libraries Used

*   **PyMuPDF (`fitz`)**: A high-performance Python library for PDF processing. It's chosen for its speed, low memory footprint, and ability to provide detailed text and font metadata without external dependencies. No other models are used.

## How to Build and Run

The solution is containerized using Docker and is designed to run offline.

**1. Build the Docker Image:**

Navigate to the project's root directory (where the `Dockerfile` is located) and run:

```sh
docker build -t pdf-extractor .
```

**2. Run the Container:**

To process PDFs, you need to mount an `input` directory containing your PDFs and an `output` directory for the JSON results.

*   Create `input` and `output` directories on your host machine if they don't exist.
*   Place your PDF files into the `input` directory.
*   Run the container using the following command:

```sh
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-extractor
```
*(For Windows PowerShell users, replace `$(pwd)` with `${pwd}`)*

The container will automatically find all `.pdf` files in `/app/input`, process them, and write the corresponding `.json` files to `/app/output`.
=======
# pdf_outline_extractor

