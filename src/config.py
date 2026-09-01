import yaml
import os
import logging
from glob import glob

logger = logging.getLogger("exam_reader")

class CONFIG:
    def __init__(self):
        # Determine the project root (where config.yaml is expected)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.config_file = os.path.join(self.project_root, "config.yaml")

        # Default values (fallbacks)
        self.URL = "https://fen.istanbul.edu.tr"
        self.port = "9222"
        self.text = "//a[.//span[contains(., 'Sınav Programları')]]"
        self.file_name_prefix = "MOLEK"
        self.is_json_default = False
        self.is_show_link_default = False
        self.cache_pdf_always = False
        self.cache_md_always = False
        self.use_cached_pdf = False
        self.use_cached_md = False
        self.regex_pattern = r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
        self.target_yariyil = r'6'
        self.chromium_path = ""
        self.verbose = ""
        self.labels = True
        self.extend = False
        self.track = False
        self.tracker_focus = ""
        self.sleep_time = 2

        # Load from config.yaml if it exists
        self._load_config()

        # Dynamic logic
        self.path = self.get_path()
        self.credentials_json = self.get_credentials_json()
        if not self.chromium_path:
            self.chromium_path = self.get_chromium_path()
            
        self.cached_pdf = self.get_cached_pdf()
        self.cached_md = self.get_cached_md()
        self.tracker_storage = os.path.join(self.get_path(), "previous_results.json")

        self.set_verbose_level()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            logger.warning(f"Warning: {self.config_file} not found. Using default values.")
            return

        try:
            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f)
                if not data:
                    return

                # Map YAML keys to class attributes
                self.URL = data.get("url", self.URL)
                self.port = str(data.get("port", self.port))
                self.text = data.get("search_xpath", self.text)
                self.file_name_prefix = data.get("file_name_prefix", self.file_name_prefix)
                self.is_json_default = data.get("is_json_default", self.is_json_default)
                self.is_show_link_default = data.get("is_show_link_default", self.is_show_link_default)
                self.cache_pdf_always = data.get("cache_pdf_always", self.cache_pdf_always)
                self.cache_md_always = data.get("cache_md_always", self.cache_md_always)
                self.use_cached_pdf = data.get("use_cached_pdf", self.use_cached_pdf)
                self.use_cached_md = data.get("use_cached_md", self.use_cached_md)
                self.regex_pattern = data.get("regex_pattern", self.regex_pattern)
                self.target_yariyil = str(data.get("target_yariyil", self.target_yariyil))
                self.chromium_path = data.get("chromium_path", self.chromium_path)
                self.verbose = data.get("verbose") or self.verbose
                self.labels = data.get("labels") or self.labels
                self.extend = data.get("extend") or self.extend
                self.track = data.get("track") or self.track
                self.tracker_focus = str(data.get("tracker_focus", self.tracker_focus))
                self.sleep_time = int(data.get("sleep_time", self.sleep_time))
        except Exception as e:
            logger.error(f"Error loading {self.config_file}: {e}")

    def set_verbose_level(self):
        if not isinstance(self.verbose, str):
            self.verbose = ""
        # 0 'v': 50, 1 'v': 40, 2 'v': 30, 3 'v': 20, 4 'v': 10, 5 'v': 0
        verbosity = max(0, 50 - (self.verbose.lower().count('v') * 10))
        logger.setLevel(verbosity)

    def get_chromium_path(self):
        paths = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            "/snap/bin/chromium-browser",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return "/usr/bin/chromium"

    def get_credentials_json(self):
        # Look in src directory for credentials (as before)
        search_pattern = os.path.join(self.get_path(), 'client_secret_*.json')
        files = glob(search_pattern)

        if files:
            return files[0]
        logger.warning("Warning: Client Secret is not found in the directory.")
        return 'client_secret_*.json'

    def get_path(self):
        # Returns the directory of this file (src/)
        return os.path.dirname(os.path.abspath(__file__))

    def get_cached_pdf(self):
        search_pattern = os.path.join(self.get_path(), '*.pdf')
        files = glob(search_pattern)
        if files:
            return files[0]
        return ""

    def get_cached_md(self):
        search_pattern = os.path.join(self.get_path(), '*.md')
        files = glob(search_pattern)
        if files:
            return files[0]
        return ""

if __name__ == '__main__':
    from .logger import setup_logger
    cfg = CONFIG()
    setup_logger()
    logger.info(f"URL: {cfg.URL}")
    logger.info(f"Port: {cfg.port}")
    logger.info(f"Chromium: {cfg.chromium_path}")
    logger.info(f"Credentials: {cfg.credentials_json}")
