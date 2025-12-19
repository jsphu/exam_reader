from pypdf import PdfReader
import re

def extract_text_and_regex(file_buffer, regex_pattern):
    """Reads PDF from memory, extracts text, and applies Regex."""
    reader = PdfReader(file_buffer)
    full_text = ""
    # Extract text from all pages
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    # Apply Regex
    matches = re.findall(regex_pattern, full_text)
    return matches, full_text

def parse_exam_schedule(text, semester_filter):
    # 1. PRE-CLEANING
    # The time is split like "11:00-\n\n12:30". Let's fix that to "11:00-12:30"
    # This makes the Regex much simpler.
    text = re.sub(r"(\d{2}:\d{2}-)\s+(\d{2}:\d{2})", r"\1\2", text)

    # 2. DEFINE THE PATTERN
    # Explanation of Regex:
    # (\d{2}/\d{2}/\d{4})      -> Capture Date (Group 1) MIDTERMS
    # (\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})? -> Capture Two Dates (Alternate Group 1) FINALS/MAKEUP
    # \s+([A-Za-zÇĞİÖŞÜçğıöşü]+) -> Capture Day (Group 2)
    # \s+(\d{2}:\d{2}-\d{2}:\d{2}) -> Capture Time (Group 3)
    # \s+(\d+)                 -> Capture SEMESTER (Group 4) - This is what we filter by!
    # \s+(.*?)                 -> Capture everything else (Course, Prof, Room) (Group 5)
    # (?=\d{2}/\d{2}/\d{4}|$)  -> Stop when we hit the Next Date OR End of String

    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})?\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{2}:\d{2}-\d{2}:\d{2})\s+(\d+)\s+(.*?)(?=\d{2}/\d{2}/\d{4}|$)",
        re.DOTALL | re.IGNORECASE
    )
    details_pattern = re.compile(
        r"(.+?)\s+"  # Capture everything up to the title (Course Name)
        r"((?:Prof\.?|Doç\.?|Dr\.?|\s*Öğr\.?|Üyesi).*$)", # Capture the title and everything after it
        re.DOTALL | re.IGNORECASE
    )

    matches = pattern.finditer(text)
    results = []

    for match in matches:
        date = match.group(1)
        date_makeup = match.group(2)
        day = match.group(3)
        time = match.group(4)
        semester = match.group(5)
        # The "details" block contains Course Name, Prof, and Room mixed together.
        # We replace newlines with spaces to make it look clean.
        details = match.group(6).replace("\n", " ").strip()
        # Remove extra spaces
        details = re.sub(r'\s+', ' ', details)

        # 3. FILTER LOGIC
        if re.fullmatch(str(semester_filter), semester):
            detail_split = details_pattern.match(details)

            if detail_split:
                course_name = detail_split.group(1).strip()
                prof_loc = detail_split.group(2).strip()

                prof_loc = re.sub(r'\s*\(.+?\)', '', prof_loc)
                prof_loc = re.sub(r'\s*\d{4}-\d{4}.*', '', prof_loc)
                prof_loc = re.sub(r'\s+', ' ', prof_loc).strip()

            else:
                course_name = details
                prof_loc = "???"

            # print(f"FOUND: {date} | {time} | {details}")
            results.append({
                "date": date,
                "date_makeup": date_makeup,
                "day": day,
                "time": time,
                "semester": semester,
                "details": details,
                "course": course_name,
                "details_without_course": prof_loc
            })

    return results

if __name__ == '__main__':
    # The raw text you scraped from the PDF
    raw_text = """
2025-2026 Güz Dönemi
Ara Sınav Programı

Tarih Gün Saat Yarıyıl Ders Adı Öğretim Üyesi Sınavın Yapılacağı Yer
12/11/2025 Çarşamba 11:00-

12:30 3 BİTKİ DOKU KÜLTÜRÜ Doç. Dr. Cüneyt

Uçarlı Derslik 6 (YENİ BİNA, KAT -2)

12/11/2025 Çarşamba 11:00-

12:30 7 GENETİK MÜHENDİSLİĞİ

Dr.Öğr. Üyesi
Semian Karaer
Uzuner

SB-Derslik 3 (YENİ BİNA),Derslik 4 (YENİ BİNA,

KAT -2)

12/11/2025 Çarşamba 13:30-

15:00 5 İŞ HUKUKU Doç. Dr. Ender

Gülver Derslik 6 (YENİ BİNA, KAT -2)

12/11/2025 Çarşamba 13:30-

15:00 7 FERMENTASYON TEKNOLOJİSİ Doç. Dr. Murat

Pekmez Derslik 6 (YENİ BİNA, KAT -2)

13/11/2025 Perşembe 09:00-

10:30 7 MOLEKÜLER EVRİM Dr.Öğr. Üyesi

Çağatay Tarhan Derslik 6 (YENİ BİNA, KAT -2)

13/11/2025 Perşembe 11:00-

12:30 3 BİYOETİK

Doç Dr. Aslıhan
Temel

SB-Derslik 3 (YENİ BİNA),Derslik 6 (YENİ BİNA,

KAT -2)

13/11/2025 Perşembe 13:30-

15:00 1 GENEL KİMYA I Dr.Öğr Üyesi
Furkan Burak Şen

Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ

BİNA, KAT -2)

13/11/2025 Perşembe 15:30-

17:00 5 RESISTANCE IN BACTERIAL PATHOGENS Dr. Öğr. Üyesi Terje

Marken Stemum Derslik 6 (YENİ BİNA, KAT -2)

14/11/2025 Cuma 09:00-

10:30 5 ENZİMOLOJİ Prof.Dr. Evren Onay
Uçar

SB-Derslik 3 (YENİ BİNA),Derslik 4 (YENİ BİNA,

KAT -2)

14/11/2025 Cuma 11:00-

12:30 5 VİRÜS BİYOLOJİSİ Prof.Dr. Ali Karagöz SB-Derslik 3 (YENİ BİNA)

14/11/2025 Cuma 14:00-

15:30 7 KÖK HÜCRE BİYOLOJİSİ Prof. Dr. Gülruh

Albayrak Derslik 6 (YENİ BİNA, KAT -2)

14/11/2025 Cuma 15:45-

17:15 3 HAYVAN DOKU KÜLTÜRÜ Prof. Dr. Ali Karagöz SB-Derslik 3 (YENİ BİNA)

17/11/2025 Pazartesi 09:00-

10:30 7 KANSER BİYOLOJİSİ Prof.Dr. Ali Karagöz Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ

BİNA, KAT -2)

17/11/2025 Pazartesi 11:00-

12:30 1
    """

    # --- RUN IT ---
    target_yariyil = 5
    exams = parse_exam_schedule(raw_text, target_yariyil)
