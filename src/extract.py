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
    # "11:00-\n\n12:30" to "11:00-12:30"
    # This makes the Regex much simpler.
    text = re.sub(r"(\d{2}:\d{2}-)\s+(\d{2}:\d{2})", r"\1\2", text)

    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{4})"         # Date (Group 1)
        r"\s*(\d{2}/\d{2}/\d{4})?"     # Second Date (Group 2)
        r"\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)"  # Day (Group 3)
        r"\s+(\d{2}:\d{2}-\d{2}:\d{2})"# Time (Group 4)
        r"\s+(\d+)"                    # SEMESTER (Group 5)
        r"\s+(.*?)"                    # everything else (Group 6)
        r"(?=\d{2}/\d{2}/\d{4}|$)",    # Stop Next Date OR End of String
        re.DOTALL | re.IGNORECASE
    )
    details_pattern = re.compile(
        r"(.+?)\s+"  # everything up to Course Name
        r"((?:Prof\.?|Doç\.?|Dr\.?|\s*Öğr\.?|Üyesi).*$)", # title and everything after it
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
Bitirme ve Bütünleme Sınav Programı

Tarih Gün Saat Yarıyıl Ders Adı Öğretim Üyesi Sınavın Yapılacağı Yer
19/01/2026 Pazartesi 09:00-

10:30 1 ATATURK ILKELERI VE İNKILAP TARİHİ I

Öğr. Gör. Melda
Ağaoğlu

Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ

BİNA, KAT -2)

19/01/2026 Pazartesi 09:00-
10:30 1

YABANCI OGREN CİLER İÇİN ATATÜRK İLKELERİ

VE İNKILAP TARİHİ I

Öğr.Gör. Melda
Ağaoğlu

Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ

BİNA, KAT -2)

19/01/2026 Pazartesi 11:00-

12:30 1 TÜRK DİLİ I

Okt. Emine
V.O.Çamlıbel

Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ
BİNA, KAT -2), MGB-118

19/01/2026 Pazartesi 11:00-

12:30 1 YABANCI OGRENCILER İÇİN TÜRK DİLİ I

Okt. Emine
Y.O.Çamlıbel

Derslik 6 (YENİ BİNA, KAT -2) DERSLİK 5 (YENİ
BİNA, KAT -2), MGB-118

19/01/2026 Pazartesi 13:30-

15:00 3 MOLEKÜLER MİKROBİYOLOJİ Prof. Dr. Gülruh

Albayrak SB-Amfi (YENİ BİNA)

19/01/2026 Pazartesi 15:30-

17:00 7 GENETİK KAYNAKLAR VE KORUMA

Dr.Öğr. Üyesi Fatma
Elif Çepni
Yüzbaşioğlu

MBG-118

20/01/2026 Salı 11:00-

12:30 3 İŞ SAĞLIĞI VE GÜVENLİĞİ Prof. Dr. Sabriye

Perçin Özkorucuklu Derslik 6 (YENİ BİNA, KAT -2)

20/01/2026 Salı 11:00-

12:30 5 GÖNÜLLÜLÜK ÇALIŞMALARI

Dr. Öğr. Üyesi
Semian Karaer
Uzuner

Derslik 6 (YENİ BİNA, KAT -2)

20/01/2026 Salı 11:00-

12:30 7 GENOMİK Prof. Dr. Şule An Derslik 6 (YENİ BİNA, KAT -2)

20/01/2026 Salı 13:30-

15:00 5 HÜCRE BİYOLOJİSİ II Prof Dr. Bedia
Palabıyık

SB-Derslik 3 (YENİ BİNA),Derslik 6 (YENİ BİNA,

KAT -2)

20/01/2026 Salı 15:30-

17:00 7 BİYOKOZMETİKLER

Dr. Öğr. Üyesi
Fatma Elif Çepni
Yüzbaşioğlu

MAT.BÖL. SEM. SAL.

21/01/2026 Çarşamba 09:00-
10:30 1

INTRODUCTION TO COMPUTER SCIENCE AND

PROGRAMMING

Dr.Oğr. Üyesi
Kemal Şanlı Derslik 4 (YENİ BİNA, KAT -2)

21/01/2026 Çarşamba 09:00-

10:30 3 BİLİM TARİHİ VE FELSEFESİ Dr. Öğr. Üyesi

Çağatay Tarhan Derslik 4 (YENİ BİNA, KAT -2)
    """

    # --- RUN IT ---
    target_yariyil = 5
    exams = parse_exam_schedule(raw_text, target_yariyil)
