import argparse
from os import path

import src.drive as drive
import src.extract as extract
import src.config as config
import src.iufen_exam_scraper as iu

def main():
    CONFIG = config.CONFIG()

    parser = argparse.ArgumentParser(
        prog="exams",
        description="Scrapes a specific PDF from a Google Drive folder, extracts text, and filters exam schedules."
    )

    # Mandatory arguments
    parser.add_argument(
        '--url',
        default=CONFIG.URL,
        help="The university's web address."
    )

    # Optional arguments with defaults
    parser.add_argument(
        '--prefix',
        default=CONFIG.file_name_prefix,
        help="The starting string of the target PDF file name (e.g., 'MOLEKÜLER'). Default: MOLEKÜLER."
    )

    parser.add_argument(
        '--semester',
        default=CONFIG.target_yariyil,
        help="The target semester(s) to filter. Can be a number (e.g., '7') or a regex pattern (e.g., '\\d+' for all, or '1|3' for semesters 1 and 3)."
    )

    parser.add_argument(
        '--port',
        default=CONFIG.port,
        help="The port for the webdriver."
    )

    parser.add_argument(
        '--text',
        default=CONFIG.text,
        help="The pattern for search inside document."
    )

    parser.add_argument(
        '--chromium',
        default=CONFIG.chromium_path,
        help="The absolute path for the chromium's binary."
    )

    parser.add_argument(
        '--json',
        default=CONFIG.is_json_default,
        action=argparse.BooleanOptionalAction,
        help="Serialize the output as json formatting."
    )

    parser.add_argument(
        '--show-link',
        default=CONFIG.is_show_link_default,
        action=argparse.BooleanOptionalAction,
        help="show google drive folder link."
    )

    parser.add_argument(
        '--cache-pdf',
        default=CONFIG.cache_pdf_always,
        action=argparse.BooleanOptionalAction,
        help="Download original exam schedule pdf"
    )

    parser.add_argument(
        '--cache-md',
        default=CONFIG.cache_md_always,
        action=argparse.BooleanOptionalAction,
        help="Cache original PDF as markdown"
    )

    parser.add_argument(
        '--use-cached-pdf',
        default=CONFIG.use_cached_pdf,
        action=argparse.BooleanOptionalAction,
        help="Use cached pdf instead of scraping web to find it."
    )

    parser.add_argument(
        '--use-cached-md',
        default=CONFIG.use_cached_md,
        action=argparse.BooleanOptionalAction,
        help="Use directly cached markdown instead of parsing pdf."
    )

    args = parser.parse_args()

    pdf_stream = None

    try:
        pdf_path, md_path = "", ""
        if args.cache_pdf or args.use_cached_pdf:
            pdf_path=CONFIG.cached_pdf
        if args.cache_md or args.use_cached_md:
            md_path=CONFIG.cached_md

        if args.use_cached_md:
            file_name = "cached.md"
        elif args.use_cached_pdf:
            with open(pdf_path, 'rb') as pdf:
                pdf_stream = pdf.read()

            file_name = "cached.pdf"
        else:
            # 0. GET DRIVE LINK
            target_url = iu.href_link_scraper(URL=args.url, port=args.port, text=args.text, chromium_path=args.chromium)

            if args.show_link:
                print(target_url)

            # 1. AUTHENTICATE
            service = drive.authenticate_google_drive()

            # 2. GET FOLDER ID
            folder_id = drive.get_file_id_from_url(target_url)
            if not folder_id:
                print("Error: Could not parse Folder ID from the provided URL.")
                return

            # 3. FIND TARGET FILE ID
            file_id, file_name = drive.get_target_file_id(service, folder_id, args.prefix)

            if not file_id:
                print(f"Error: File starting with '{args.prefix}' not found in folder.")
                return

            # 4. DOWNLOAD PDF CONTENT
            pdf_stream = drive.download_pdf_to_memory(service, file_id)

        if args.use_cached_md:
            with open(md_path, 'r') as file:
                raw_text = file.read()
        else:
            # 4.1 SCRAPE AND REGEX
            _, raw_text = extract.extract_text_and_regex(
                file_buffer=pdf_stream,
                regex_pattern=args.semester,
                save_markdown_to=md_path,
                save_pdf_to=pdf_path)

        # 5. PARSE AND FILTER SCHEDULE
        matches = extract.parse_exam_schedule(raw_text, args.semester)

        if not matches:
            print(f"Warning: No exam matches found for semester '{args.semester}'.")
            if not args.json:
                print("Double-check the PDF content and the semester filter.")

        if args.json:
            import json

            matches.insert(0, {"file_name": file_name})
            JSON=json.dumps(matches)

            print(JSON)
        else:
            print(file_name, "\n")
            print("SAAT  TARİH(LER)  GÜN  | DERS ADI      | YERİ")
            print("----  ----------- ---- | ------------- | --------------------")
            for match in matches:
                date = match['date']
                if (makeup:=match['date_makeup']):
                    date = date[:5] + " " + makeup[:5]
                else:
                    date = date[:5] + "      "
                day = match['day']
                time = match['time']
                # The "details" block contains Course Name, Prof, and Room mixed together.
                # We replace newlines with spaces to make it look clean.
                # dextails = match['details'] # Remove extra spaces
                prof_loc = match['details_without_course']
                location = match['location']
                course_name = match['course']

                print(f"{time[:5]} {date} {day[:4]} | {course_name[:13]:<13} | {location[:35]}")
    except Exception as e:
        print(f"\nAn unrecoverable error occurred: {e}")


if __name__ == '__main__':
    main()
