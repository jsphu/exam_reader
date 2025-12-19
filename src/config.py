from os import path
from glob import glob
class CONFIG:
    def __init__(self):
        self.URL = "https://fen.istanbul.edu.tr/tr/"
        self.port = "9222"
        self.text = "//a[contains(text(), 'Sınav Programları')]"
        self.file_name_prefix = "MOLEK"
        self.is_json_default = False

        self.path = self.get_path()
        self.credentials_json = self.get_credentials_json()
        self.chromium_path = self.get_chromium_path()
        self.regex_pattern = r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b" # Example: Extract emails
        self.target_yariyil = r'\d+'

    def get_chromium_path(self):
        PATH = "/snap/bin/chromium" # chromium available on snap
        if not path.exists(PATH):
            PATH = "/snap/bin/chromium-browser"
        return PATH

    def get_credentials_json(self):
        search_pattern = path.join(self.path, 'client_secret_*.json')
        files = glob(search_pattern)

        if files:
            return files[0]
        print("Warning: Client Secret is not found in the directory.")
        return 'client_secret_*.json'

    def get_path(self):
        return path.dirname(path.abspath(__file__))

# testing glob
if __name__ == '__main__':
    cfg = CONFIG()
    print(cfg.credentials_json)
