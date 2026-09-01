import argparse
import logging
from os import path

import src.drive as drive
import src.extract as extract
import src.config as config
import src.iufen_exam_scraper as iu
import src.tracker as tracker
from .logger import setup_logger

logger = logging.getLogger("exam_reader")


def main():
    CONFIG = config.CONFIG()
    setup_logger()

    parser = argparse.ArgumentParser(
        prog="exams",
        description="Scrapes University's webpage exam schedule PDF from a Google Drive folder, extracts text, and filters exam schedules.",
    )

    # Mandatory arguments
    parser.add_argument(
        "--url", default=CONFIG.URL, help="The university's web address."
    )

    # Optional arguments with defaults
    parser.add_argument(
        "--prefix",
        default=CONFIG.file_name_prefix,
        help="The starting string of the target PDF file name (e.g., 'MOLEKÜLER'). Default: MOLEKÜLER.",
    )

    parser.add_argument(
        "--semester",
        default=CONFIG.target_yariyil,
        help="The target semester(s) to filter. Can be a number (e.g., '7') or a regex pattern (e.g., '\\d+' for all, or '1|3' for semesters 1 and 3).",
    )

    parser.add_argument(
        "--port", default=CONFIG.port, help="The port for the webdriver."
    )

    parser.add_argument(
        "--text", default=CONFIG.text, help="The pattern for search inside document."
    )

    parser.add_argument(
        "--chromium",
        default=CONFIG.chromium_path,
        help="The absolute path for the chromium's binary.",
    )

    parser.add_argument(
        "--json",
        default=CONFIG.is_json_default,
        action=argparse.BooleanOptionalAction,
        help="Serialize the output as json formatting.",
    )

    parser.add_argument(
        "--show-link",
        default=CONFIG.is_show_link_default,
        action=argparse.BooleanOptionalAction,
        help="show google drive folder link.",
    )

    parser.add_argument(
        "--cache",
        default=CONFIG.cache_md_always,
        action=argparse.BooleanOptionalAction,
        help="Cache original PDF as markdown",
    )

    parser.add_argument(
        "--cached",
        default=CONFIG.use_cached_md,
        action=argparse.BooleanOptionalAction,
        help="Use directly cached markdown instead of parsing pdf.",
    )

    parser.add_argument("--verbose", "-v", action="count", help="Add more verbosity")

    parser.add_argument(
        "--labels",
        default=CONFIG.labels,
        action=argparse.BooleanOptionalAction,
        help="Show/Hide column labels of normal output.",
    )

    parser.add_argument(
        "--extend",
        default=CONFIG.extend,
        action=argparse.BooleanOptionalAction,
        help="Extend column width as long as it goes",
    )

    parser.add_argument(
        "--track",
        default=CONFIG.track,
        action=argparse.BooleanOptionalAction,
        help="Check for changes from previous run.",
    )

    parser.add_argument(
        "--sleep-time",
        default=CONFIG.sleep_time,
        type=int,
        help="Seconds to wait for webpage to render",
    )

    args = parser.parse_args()
    run_pipeline(args, CONFIG, is_cli=True)


def run_pipeline(args, CONFIG, is_cli=True):
    if args.verbose is not None:
        CONFIG.verbose = "v" * args.verbose
    CONFIG.set_verbose_level()

    logger.log(
        20,
        f"Starting with parameters: url={args.url}, prefix={args.prefix}, semester={args.semester}",
    )

    pdf_stream = None
    changes = []
    file_name = ""
    matches = []

    try:
        pdf_path, md_path = "", ""
        if args.cache or args.cached:
            md_path = CONFIG.cached_md
            logger.log(30, f"Markdown cache path: {md_path}")

        if args.cached:
            logger.log(30, "Using cached markdown file.")
            file_name = md_path
        else:
            # 0. GET DRIVE LINK
            target_url = iu.href_link_scraper(
                URL=args.url,
                port=args.port,
                text=args.text,
                chromium_path=args.chromium,
                sleep_time=args.sleep_time,
            )

            if args.show_link:
                logger.log(50, f"Drive Link: {target_url}")

            # 1. AUTHENTICATE
            logger.log(20, "Authenticating with Google Drive...")
            service = drive.authenticate_google_drive()

            # 2. GET FOLDER ID
            logger.log(1, "Parsing folder ID from URL...")
            folder_id = drive.get_file_id_from_url(target_url)
            if not folder_id:
                msg = "Error: Could not parse Folder ID from the provided URL."
                logger.log(50, msg)
                if is_cli:
                    return
                else:
                    raise ValueError(msg)

            # 3. FIND TARGET FILE ID
            logger.log(
                20, f"Searching for file with prefix '{args.prefix}' in Drive folder..."
            )
            file_id, file_name = drive.get_target_file_id(
                service, folder_id, args.prefix
            )

            if not file_id:
                msg = f"Error: File starting with '{args.prefix}' not found in folder."
                logger.log(50, msg)
                if is_cli:
                    return
                else:
                    raise ValueError(msg)

            # 4. DOWNLOAD PDF CONTENT
            logger.log(30, f"Downloading file: {file_name}")
            pdf_stream = drive.download_pdf_to_memory(service, file_id)

        if args.cached:
            logger.log(10, f"Reading cached markdown from: {md_path}")
            with open(md_path, "r") as file:
                raw_text = file.read()
        else:
            # 4.1 SCRAPE AND REGEX
            logger.log(20, "Extracting text and applying filters...")
            _, raw_text = extract.extract_text_and_regex(
                file_buffer=pdf_stream,
                regex_pattern=args.semester,
                save_markdown_to=md_path,
                save_pdf_to=pdf_path,
            )

        # 5. PARSE AND FILTER SCHEDULE
        logger.log(1, "Parsing raw text into schedule structure...")
        matches = extract.parse_exam_schedule(raw_text, args.semester)

        if args.track:
            logger.log(20, "Checking for changes...")
            import re

            previous_results = tracker.load_previous_results(CONFIG.tracker_storage)

            # 1. Filter matches by tracker_focus
            if CONFIG.tracker_focus:
                matches = [
                    m
                    for m in matches
                    if re.search(str(CONFIG.tracker_focus), str(m.get("semester", "")))
                ]

            # 2. Filter previous_results by tracker_focus
            if CONFIG.tracker_focus:
                filtered_previous = {}
                for cid, m in previous_results.items():
                    if re.search(str(CONFIG.tracker_focus), str(m.get("semester", ""))):
                        filtered_previous[cid] = m
                previous_results = filtered_previous

            changes, current_dict = tracker.compare_results(matches, previous_results)

            if changes:
                logger.log(50, "\n" + "=" * 40)
                logger.log(50, "   CHANGE TRACKER: UPDATES DETECTED")
                logger.log(50, "=" * 40)
                for change in changes:
                    logger.log(50, change)
                logger.log(50, "=" * 40 + "\n")
            else:
                logger.log(50, "No changes detected since last run.")

            # 3. Save only what matched the tracker_focus (and current runs results)
            # If focus is enabled, current_dict already contains ONLY focused exams.
            # If focus is NOT enabled, we update previous_results (which still has all semesters).
            if CONFIG.tracker_focus:
                tracker.save_current_results(CONFIG.tracker_storage, current_dict)
            else:
                previous_results.update(current_dict)
                tracker.save_current_results(CONFIG.tracker_storage, previous_results)

            if is_cli:
                exit(0 if changes else 1)  # Exit after tracking

        if not matches:
            logger.log(
                40, f"Warning: No exam matches found for semester '{args.semester}'."
            )
            if not args.json:
                logger.log(40, "Double-check the PDF content and the semester filter.")

        if args.json:
            import json

            JSON = json.dumps({"file": file_name, "exams": matches})

            logger.log(50, JSON)
        else:
            logger.log(40, f"{file_name=}\n")
            if args.extend:
                max_length = max((len(match["course"]) for match in matches)) if matches else 13
                logger.log(10, f"{max_length=}")
                padding = (max_length - 13) * "-" + " "
                PADDING = padding.replace("-", " ")
                day_padding = 5 * "-" + " "
                DAY_PADDING = day_padding.replace("-", " ")
            else:
                max_length = 13
                padding = " "
                PADDING = padding
                day_padding = " "
                DAY_PADDING = day_padding
            logger.log(10, f"Selected {padding=}")
            logger.log(10, rf"{day_padding=}")
            if args.labels:
                logger.log(
                    50,
                    "TARİH(LER)  GÜN "
                    + DAY_PADDING
                    + "SAAT  DERS ADI     "
                    + PADDING
                    + "YERİ",
                )
                logger.log(
                    50,
                    "----------- ----"
                    + day_padding
                    + "----- -------------"
                    + padding
                    + "--------------------",
                )
            for match in matches:
                date = match["date"]
                if makeup := match["date_makeup"]:
                    date = f"{date[:5]} {makeup[:5]}"
                else:
                    date = f"{date[:5]:<11}"
                day = match["day"]
                day = f"{day:<9}"
                time = match["time"]
                location = match["location"] or "???"
                course_name = match["course"]
                if not args.extend:
                    course_name = course_name[:13]
                    location = location[:35]
                    day = day[:4]

                logger.log(
                    50,
                    f"{date} {day:<{max(4, len(day_padding))}} {time[:5]} {course_name:<{max_length}} {location}",
                )
        return {"file_name": file_name, "exams": matches, "changes": changes}
    except Exception as e:
        logger.log(50, f"\nAn unrecoverable error occurred: {e}")
        if not is_cli:
            raise e



if __name__ == "__main__":
    main()
