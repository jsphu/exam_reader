# exam_reader
Selenium web scraping for automatically get latest
updates of 'exam schedules'

## important
this repository allows only for personal usage

---
## installation
1. **simply clone the repo**
```
git clone https://github.com/jsphu/exam_reader.git
```
2. **change directory to the repo**
```shell
cd exam_reader
```
3. **install requirements** (tested with python 3.13.3) 
```shell
pip install -r requirements.txt
```
**NOTE**: extra libraries exist such as `pynvim`

4. (**OPTIONAL**) **if you'd like to change config go to **`config.py`. But no need for now, the script accepts these as arguments now.
     
    a. `URL` for university web which is "fen.istanbul.edu.tr"

    b. `file_name_prefix` for the faculty programs name. default: 'MOLEK' -prefix of MOLEKÜLER BİYOLOJİ VE GENETİK-

    c. `chromium_path` is for the binary of chromium located on your OS. default: `/snap/bin/chromium`

    d. `target_yariyil` is for the regex to search the column 'YARIYIL' in the pdf. default: `r'\d+'` leave it like this if you want to get every exams.

    e. `credentials_json` is the secret for your googleapi. you can get from [google console](https://console.cloud.google.com/apis/credentials) install and move the json file in the same directory.

**NOTE**: First run might want you to give access to your account. After that it will create `token.json` file to not bother you again.

---

## running
```bash
python main.py
```

Getting only the semester '5'
```bash
python3 main.py --semester 5
```

Examine different programs. (F for FİZİK)
```bash
python main.py --prefix F
```

further applications, add this to your `.bashrc`
```bash
alias exams="python3 /path/to/exam_reader/main.py"
```

usage:
```bash
usage: exams [-h] [--url URL] [--prefix PREFIX] [--semester SEMESTER]
             [--port PORT] [--text TEXT] [--chromium CHROMIUM]

Scrapes a specific PDF from a Google Drive folder, extracts text, and filters
exam schedules.

options:
  -h, --help           show this help message and exit
  --url URL            The university's web address.
  --prefix PREFIX      The starting string of the target PDF file name (e.g.,
                       'MOLEKÜLER'). Default: MOLEKÜLER.
  --semester SEMESTER  The target semester(s) to filter. Can be a number
                       (e.g., '7') or a regex pattern (e.g., '\d+' for all, or
                       '1|3' for semesters 1 and 3).
  --port PORT          The port for the webdriver.
  --text TEXT          The pattern for search inside document.
  --chromium CHROMIUM  The absolute path for the chromium's binary.
```
