# Exam Reader

A Python tool to scrape exam schedules from Istanbul University (Fen Fakültesi), download them from Google Drive, and extract specific exam details using AI/OCR-powered processing.

## Features

- **Automated Scraping:** Finds the latest exam schedule links using Selenium.
- **Google Drive Integration:** Authenticates and downloads PDF files directly from shared Drive folders.
- **AI-Powered Extraction:** Uses `docling` for high-accuracy PDF-to-Markdown conversion, handling complex table layouts better than traditional text scrapers.
- **Flexible Configuration:** Manage all settings via `config.yaml`.
- **Customizable Output:** Filter by semester, toggle between JSON and tabular views, and adjust verbosity.

## Prerequisites

- Python 3.10+
- Chromium browser (for Selenium scraping)
- Google Cloud Project with Drive API enabled and `client_secret_*.json`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jsphu/exam_reader.git
   cd exam_reader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup Google API Credentials:
   - Place your `client_secret_*.json` in the `src/` directory.
   - On the first run, a browser window will open for authentication, creating a `token.json` in `src/` for future use.

## Configuration

The project uses a `config.yaml` file for persistent settings. You can override these via CLI arguments.

### `config.yaml` Example:

```yaml
# Browser configuration
url: "https://fen.istanbul.edu.tr"
port: "9222"
chromium_path: "" # Leave empty to use auto-detection

# Scraper configuration
search_xpath: "//a[.//span[contains(., 'Sınav Programları')]]"
file_name_prefix: "MOLEK"
target_yariyil: "6"

# Output configuration
labels: true
extend: false
```

## Usage

Run the tool using `main.py`:

```bash
python main.py [OPTIONS]
```

### CLI Arguments:

- `--url`: Override the base scraping URL.
- `--prefix`: PDF filename prefix (e.g., `MOLEK`).
- `--semester`: Filter exams by semester (e.g., `6`).
- `--json`: Output results in JSON format.
- `--show-link`: Display the discovered Google Drive folder link.
- `--cache`: Cache the extracted markdown for future use.
- `--cached`: Use the cached markdown instead of re-processing the PDF.
- `--verbose`, `-v`: Increase logging verbosity (multiple levels supported).
- `--no-labels`: Hide column headers in tabular output.
- `--extend`: Expand column widths to prevent truncation.

## Technical Details

- **Extraction Engine:** Transitions from raw text extraction to `docling`, providing structural awareness for PDF tables.
- **Logging:** Implements a custom logger that scales with verbosity levels (`-v`, `-vv`, etc.).
- **Caching:** Supports both PDF and Markdown caching to reduce API calls and processing time.
