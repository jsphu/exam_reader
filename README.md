# exam_reader
Selenium web scraping for automatically get latest
updates of 'exam schedules'

## important
this repository allows only for personal usage

---
## installation
1. simply clone the repo
```
git clone https://github.com/jsphu/exam_reader.git
```
---
2. change directory to the repo
```shell
cd exam_reader
```
---
3. install requirements (tested with python 3.13.3) 
```shell
pip install -r requirements.txt
```
NOTE: extra libraries exist such as `pynvim`

---
4. (OPTIONAL) if you'd like to change config go to `config.py`
---
  1. `URL` for university web which is "fen.istanbul.edu.tr"
  2. `file_name_prefix` for the faculty programs name. default: 'MOLEK' -prefix of MOLEKÜLER BİYOLOJİ VE GENETİK-
  3. `chromium_path` is for the binary of chromium located on your OS. default: `/snap/bin/chromium`
  4. `target_yariyil` is for the regex to search the column 'YARIYIL' in the pdf. default: `r'\d+'` leave it like this if you want to get every exams.
  5. `credentials_json` is the secret for your googleapi. you can get from [google console](https://console.cloud.google.com/apis/credentials) install and move the json file in the same directory.

NOTE: First run might want you to give access to your account. After that it will create `token.json` file to not bother you again.

---

## running
```bash
python main.py
```

with grep : Getting only the semester '5'
```bash
python3 main.py |grep "| 5 |"
```

further applications, add this to your `.bashrc`
```bash
alias exams="python3 /path/to/exam_reader/main.py"
```
