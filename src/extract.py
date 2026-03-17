from contextlib import redirect_stdout, redirect_stderr
import re
import os
import logging

logger = logging.getLogger("exam_reader")

def save_pdf(file_buffer , path):
    """Saves PDF buffer to a file safely without exhausting the stream."""
    if hasattr(file_buffer, 'getvalue'):
        data = file_buffer.getvalue()
    elif hasattr(file_buffer, 'read'):
        original_pos = 0
        if hasattr(file_buffer, 'tell'):
            original_pos = file_buffer.tell()
        if hasattr(file_buffer, 'seek'):
            file_buffer.seek(0)
        data = file_buffer.read()
        if hasattr(file_buffer, 'seek'):
            file_buffer.seek(original_pos)
    else:
        data = file_buffer

    with open(path, 'wb') as file:
        file.write(data)

def convert_to_markdown(docling_stream):
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

    # Configure pipeline options for better table extraction
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True
    
    # Optional: Enable OCR if needed (can be very slow)
    # pipeline_options.do_ocr = True 

    logger.log(10, "Initializing DocumentConverter.")
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    logger.log(40, "Starting converter...")
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            conversion = converter.convert(docling_stream)
    # Export to markdown as it contains the table structures
    logger.log(30, "Conversion done! Exporting to markdown")
    return conversion.document.export_to_markdown()

def extract_text_and_regex(file_buffer, regex_pattern, save_markdown_to: str="", save_pdf_to: str=""):
    from docling.datamodel.base_models import DocumentStream

    """Uses docling to extract text/tables from PDF and returns as Markdown."""
    # Ensure we are at the start of the buffer
    if hasattr(file_buffer, 'seek'):
        file_buffer.seek(0)

    if save_pdf_to:
        save_pdf(file_buffer, save_pdf_to)

    logger.log(30, "Streaming document into DocumentStream")
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            # docling needs a DocumentStream for in-memory buffers
            doc_stream = DocumentStream(name="exam.pdf", stream=file_buffer)

    logger.log(30, f"INFO: Running docling extraction on the provided PDF...")
    md_text = convert_to_markdown(doc_stream)
    logger.log(30, f"INFO: Extraction finished. Markdown length: {len(md_text)} characters.")

    if not md_text.strip():
        logger.log(40, "WARNING: Docling extraction returned empty text. Check the PDF content.")

    if save_markdown_to:
        with open(save_markdown_to, "w") as file:
            file.write(md_text)
            logger.log(30, f"Markdown sucessfully written to: {save_markdown_to}")

    # The original function returned (matches, full_text).
    # We return ([], md_text) to maintain signature, though matches isn't used much in main.py
    return [], md_text

def parse_exam_schedule(text, semester_filter):
    """Parses exam schedule from docling-generated markdown text."""

    # Regex patterns for identifying fields in cells
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
    time_pattern = re.compile(r"\d{2}:\d{2}\s*-\s*\d{2}:\d{2}")
    day_pattern = re.compile(r"(Pazartesi|Salı|Çarşamba|Perşembe|Cuma|Cumartesi|Pazar)", re.IGNORECASE)
    semester_pattern = re.compile(r"^\s*(\d+)\s*$")

    # Instructor identification
    instructor_keywords = r"(Prof\.|Doç\.|Dr\.|Öğr\.)"
    instructor_pattern = re.compile(instructor_keywords + r".*", re.IGNORECASE)

    results = []

    # Split text into lines
    lines = text.split('\n')

    for line in lines:
        if '|' not in line:
            continue

        # Skip header separators
        if '---' in line:
            continue

        cells = [cell.strip() for cell in line.split('|')]
        # Remove empty first and last cells if they exist (due to leading/trailing |)
        if cells and not cells[0]: cells.pop(0)
        if cells and not cells[-1]: cells.pop(-1)

        # Skip headers or empty lines
        if not cells or any(h in cells[0] for h in ["Tarih", "Ara Sınav", "Sınav Programı"]):
            continue

        data = {
            "date": "",
            "date_makeup": "", # Not easily separable in docling table sometimes, but we'll try
            "day": "",
            "time": "",
            "semester": "",
            "course": "",
            "instructor": "",
            "location": "",
            "details": "" # For compatibility with original main.py expectations
        }

        assigned_cells = set()

        # Pass 1: Extract clearly identifiable fields
        for i, cell in enumerate(cells):
            if not cell: continue

            found = False
            # Date
            date_matches = date_pattern.findall(cell)
            if date_matches:
                if not data["date"]:
                    data["date"] = date_matches[0]
                    if len(date_matches) > 1:
                        data["date_makeup"] = date_matches[1]
                found = True

            # Time
            time_match = time_pattern.search(cell)
            if time_match:
                if not data["time"]: data["time"] = time_match.group().replace(" ", "")
                found = True

            # Day
            day_match = day_pattern.search(cell)
            if day_match:
                if not data["day"]: data["day"] = day_match.group()
                found = True

            # Semester
            sem_match = semester_pattern.search(cell)
            if sem_match:
                if not data["semester"]: data["semester"] = sem_match.group(1)
                found = True

            # Instructor
            inst_match = instructor_pattern.search(cell)
            if inst_match:
                if not data["instructor"]: data["instructor"] = inst_match.group().strip()
                found = True

            if found:
                assigned_cells.add(i)

        # Pass 2: Course and Location based on remaining cells
        unassigned = [i for i in range(len(cells)) if i not in assigned_cells and cells[i]]

        for i in unassigned:
            cell = cells[i]
            # Heuristic: Location often contains specific keywords
            if any(word in cell.upper() for word in ["DERSLİK", "AMFİ", "LAB", "BİNA", "MBG-", "SB-", "ODASI"]):
                if not data["location"]:
                    data["location"] = cell
                else:
                    data["location"] += ", " + cell
            elif not data["course"]:
                data["course"] = cell
            else:
                # If we already have a course, check if it's an instructor we missed or more location
                if any(word in cell for word in ["Prof", "Dr", "Gör", "Doç"]):
                    if not data["instructor"]: data["instructor"] = cell
                    else: data["instructor"] += ", " + cell
                else:
                    data["location"] = (data["location"] + ", " + cell) if data["location"] else cell

        # Filter by semester if semester_filter is provided
        if semester_filter and data["semester"]:
            try:
                if not re.fullmatch(str(semester_filter), data["semester"]):
                    continue
            except re.error:
                # If filter is not a valid regex, try direct comparison
                if str(semester_filter) != data["semester"]:
                    continue

        # Post-processing
        if data["date"] or data["course"]:
            # Clean up instructor/location
            data["instructor"] = re.sub(r'\s+', ' ', data["instructor"]).strip()
            data["location"] = re.sub(r'\s+', ' ', data["location"]).strip()

            # For main.py compatibility
            data["details"] = f"{data['instructor']} {data['location']}".strip()
            data["course"] = data["course"].strip()
            data["details_without_course"] = data["details"]

            results.append(data)

    return results

if __name__ == '__main__':
    # Test with the example file
    try:
        from .logger import setup_logger
        setup_logger(True) # Force true for testing
        with open("../docling_output.md", "r") as f:
            md_content = f.read()

        # Test semester filter
        semester="6"
        matches = parse_exam_schedule(md_content, semester)
        logger.warning(f"WARNING: Running through src/extract.py, outside of CLI. Selected {semester=}")
        logger.info("SAAT  TARİH(LER)  GÜN  | DERS ADI      | YERİ\n"
        "----  ----------- ---- | ------------- | --------------------")
        for m in matches:
            logger.info(f"{m['time'][:5]} {m['date'][:5]:<11} {m['day'][:4]} | {m['course'][:13]:<13} | {m['location'][:35]}")
    except FileNotFoundError:
        logger.error("docling_output.md not found for testing")
    except ImportError:
        # Fallback if logger can't be imported during direct execution
        print("Logger not found, falling back to print for test")
