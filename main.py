from drive import *
from extract import *
from iufen_exam_scraper import href_link_scraper
from config import CONFIG as cfg

if __name__ == '__main__':

    CONFIG = cfg() # initiation

    URL = CONFIG.URL
    port = CONFIG.port
    text = CONFIG.text
    chromium_path = CONFIG.chromium_path
    prefix = CONFIG.file_name_prefix
    regex = CONFIG.regex_pattern
    target_yariyil = CONFIG.target_yariyil

    # --- CONFIGURATION ---
    target_url = href_link_scraper(URL=URL, port=port, text=text, chromium_path=chromium_path)
    my_regex = regex
    # ---------------------

    try:
        # 1. Authenticate
        service = authenticate_google_drive()

        # 2. Get ID from Link
        folder_id = get_file_id_from_url(target_url)
        if not folder_id:
            print("Could not find a valid Folder ID in that URL.")
            exit()

        file_id = get_target_file_id(service, folder_id, prefix=prefix)

        if file_id:
            # 3. Download content to RAM (no file saved)
            pdf_stream = download_pdf_to_memory(service, file_id)

            # 4. Scrape and Regex
            _, raw_text = extract_text_and_regex(pdf_stream, my_regex)

            matches = parse_exam_schedule(raw_text, target_yariyil)

            print("")
            print("SAAT  TARİH GÜN  | YARIYIL | DERS ADI ... YERİ")
            print("----  ----- ---- | ------- | -------- ... ----")
            for match in matches:
                date = match['date']
                day = match['day']
                time = match['time']
                semester = match['semester']
                # The "details" block contains Course Name, Prof, and Room mixed together.
                # We replace newlines with spaces to make it look clean.
                details = match['details'] # Remove extra spaces

                print(f"{time[:5]} {date[:5]} {day[:4]} | {semester} | {details[:20]}...{details[-35:]}")
        else:
            print(f"File with {prefix=} is not found in the folder.")
            print(f"Target link was: {target_url}")
    except Exception as e:
        print(f"An error occurred: {e}")
