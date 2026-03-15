import argparse
import logging
from os import path

import src.drive as drive
import src.extract as extract
import src.config as config
import src.iufen_exam_scraper as iu
from .logger import setup_logger

logger = logging.getLogger("exam_reader")

def main():
    CONFIG = config.CONFIG()
    setup_logger()

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
        '--cache',
        default=CONFIG.cache_md_always,
        action=argparse.BooleanOptionalAction,
        help="Cache original PDF as markdown"
    )

    parser.add_argument(
        '--cached',
        default=CONFIG.use_cached_md,
        action=argparse.BooleanOptionalAction,
        help="Use directly cached markdown instead of parsing pdf."
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        help="Add more verbosity"
    )

    parser.add_argument(
        '--labels',
        default=CONFIG.labels,
        action=argparse.BooleanOptionalAction,
        help="Show/Hide column labels of normal output."
    )

    parser.add_argument(
        '--extend',
        default=CONFIG.extend,
        action=argparse.BooleanOptionalAction,
        help="Extend column width as long as it goes"
    )

    args = parser.parse_args()
    if args.verbose is not None:
        CONFIG.verbose = "v" * args.verbose
    CONFIG.set_verbose_level()

    logger.log(20, f"Starting with parameters: url={args.url}, prefix={args.prefix}, semester={args.semester}")

    pdf_stream = None

    try:
        pdf_path, md_path = "", ""
        if args.cache or args.cached:
            md_path=CONFIG.cached_md
            logger.log(30, f"Markdown cache path: {md_path}")

        if args.cached:
            logger.log(30, "Using cached markdown file.")
            file_name = md_path
        else:
            # 0. GET DRIVE LINK
            target_url = iu.href_link_scraper(URL=args.url, port=args.port, text=args.text, chromium_path=args.chromium)

            if args.show_link:
                logger.log(50, f"Drive Link: {target_url}")

            # 1. AUTHENTICATE
            logger.log(20, "Authenticating with Google Drive...")
            service = drive.authenticate_google_drive()

            # 2. GET FOLDER ID
            logger.log(1, "Parsing folder ID from URL...")
            folder_id = drive.get_file_id_from_url(target_url)
            if not folder_id:
                logger.log(50, "Error: Could not parse Folder ID from the provided URL.")
                return

            # 3. FIND TARGET FILE ID
            logger.log(20, f"Searching for file with prefix '{args.prefix}' in Drive folder...")
            file_id, file_name = drive.get_target_file_id(service, folder_id, args.prefix)

            if not file_id:
                logger.log(50, f"Error: File starting with '{args.prefix}' not found in folder.")
                return

            # 4. DOWNLOAD PDF CONTENT
            logger.log(30, f"Downloading file: {file_name}")
            pdf_stream = drive.download_pdf_to_memory(service, file_id)

        if args.cached:
            logger.log(10, f"Reading cached markdown from: {md_path}")
            with open(md_path, 'r') as file:
                raw_text = file.read()
        else:
            # 4.1 SCRAPE AND REGEX
            logger.log(20, "Extracting text and applying filters...")
            _, raw_text = extract.extract_text_and_regex(
                file_buffer=pdf_stream,
                regex_pattern=args.semester,
                save_markdown_to=md_path,
                save_pdf_to=pdf_path)

        # 5. PARSE AND FILTER SCHEDULE
        logger.log(1, "Parsing raw text into schedule structure...")
        matches = extract.parse_exam_schedule(raw_text, args.semester)

        if not matches:
            logger.log(40, f"Warning: No exam matches found for semester '{args.semester}'.")
            if not args.json:
                logger.log(40, "Double-check the PDF content and the semester filter.")

        if args.json:
            import json

            matches.insert(0, {"file_name": file_name})
            JSON=json.dumps(matches)

            logger.log(50, JSON)
        else:
            logger.log(40, f"{file_name=}\n")
            if args.extend:
                max_length = max((len(match['course']) for match in matches))
                logger.log(10, f"{max_length=}")
                padding = (max_length - 13) * " " + " "
                day_padding = 5 * "-" + " "
                DAY_PADDING = day_padding.replace('-', ' ')
            else:
                max_length = 13
                padding = " "
                day_padding = " "
                DAY_PADDING = day_padding
            logger.log(10, f"Selected {padding=}")
            logger.log(10, rf"{day_padding=}")
            if args.labels:
                logger.log(50, "TARİH(LER)  GÜN " + DAY_PADDING + "SAAT  DERS ADI     " + padding + "YERİ")
                logger.log(50, "----------- ----" + day_padding + "----- -------------" + padding + "--------------------")
            for match in matches:
                date = match['date']
                if (makeup:=match['date_makeup']):
                    date = f"{date[:5]} {makeup[:5]}"
                else:
                    date = f"{date[:5]:<11}"
                day = match['day']
                day = f"{day:<9}"
                time = match['time']
                # The "details" block contains Course Name, Prof, and Room mixed together.
                # We replace newlines with spaces to make it look clean.
                # dextails = match['details'] # Remove extra spaces
                prof_loc = match['details_without_course']
                location = match['location'] or "---"
                course_name = match['course']
                if not args.extend:
                    course_name = course_name[:13]
                    location = location[:35]
                    day = day[:4]

                logger.log(50, f"{date} {day:<{max(4, len(day_padding))}} {time[:5]} {course_name:<{max_length}} {location}")
    except Exception as e:
        logger.log(50, f"\nAn unrecoverable error occurred: {e}")


if __name__ == '__main__':
    main()
