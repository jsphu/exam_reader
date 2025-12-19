import argparse
import unicodedata
import sys

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

    args = parser.parse_args()

    try:
        # 0. GET DRIVE LINK
        target_url = iu.href_link_scraper(URL=args.url, port=args.port, text=args.text, chromium_path=args.chromium)

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

        # 4.1 SCRAPE AND REGEX
        _, raw_text = extract.extract_text_and_regex(pdf_stream, args.semester)

        # 5. PARSE AND FILTER SCHEDULE
        matches = extract.parse_exam_schedule(raw_text, args.semester)
        # Print header

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
                details = match['details'] # Remove extra spaces
                prof_loc = match['details_without_course']
                course_name = match['course']

                padding = sum(1 for char in course_name if char in set('ÇĞÜŞİÖçğiöşü'))

                print(f"{time[:5]} {date} {day[:4]} | {course_name[:13]}{padding*' '} | {prof_loc}")
    except Exception as e:
        print(f"\nAn unrecoverable error occurred: {e}")


if __name__ == '__main__':
    main()
