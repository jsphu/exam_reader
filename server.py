import os
import sys
import uvicorn
import argparse
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Add current workspace directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import run_pipeline
from src.config import CONFIG as ExamConfig


# Setup capturing log handler
class ListLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        # We format with simple messages as setup_logger does
        self.records.append(self.format(record))


app = FastAPI(
    title="Exam Reader Dashboard",
    description="FastAPI Server for Scrapes and Filters",
)


# Pydantic model for input parameters
class RunParams(BaseModel):
    url: Optional[str] = None
    prefix: Optional[str] = None
    semester: Optional[str] = None
    port: Optional[str] = None
    text: Optional[str] = None
    chromium: Optional[str] = None
    cache: Optional[bool] = None
    cached: Optional[bool] = None
    verbose: Optional[int] = None
    labels: Optional[bool] = None
    extend: Optional[bool] = None
    sleep_time: Optional[int] = None


@app.get("/config")
def get_config():
    """Retrieve the current default configuration parameters from config.yaml"""
    try:
        cfg = ExamConfig()
        return {
            "url": cfg.URL,
            "port": cfg.port,
            "search_xpath": cfg.text,
            "file_name_prefix": cfg.file_name_prefix,
            "is_json_default": cfg.is_json_default,
            "is_show_link_default": cfg.is_show_link_default,
            "cache_pdf_always": cfg.cache_pdf_always,
            "cache_md_always": cfg.cache_md_always,
            "use_cached_pdf": cfg.use_cached_pdf,
            "use_cached_md": cfg.use_cached_md,
            "target_yariyil": cfg.target_yariyil,
            "chromium_path": cfg.chromium_path,
            "sleep_time": cfg.sleep_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


@app.post("/run")
def run_scraper(params: RunParams):
    """Execute the main exam reader scraping process and return results"""
    cfg = ExamConfig()

    # Setup custom logging capture
    log_capture = ListLogHandler()
    log_capture.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # We register this capture handler on our main logger
    logger = logging.getLogger("exam_reader")
    logger.addHandler(log_capture)

    # Build arguments namespace simulating CLI inputs
    args = argparse.Namespace()
    args.url = params.url if params.url is not None else cfg.URL
    args.prefix = params.prefix if params.prefix is not None else cfg.file_name_prefix
    args.semester = (
        params.semester if params.semester is not None else cfg.target_yariyil
    )
    args.port = params.port if params.port is not None else cfg.port
    args.text = params.text if params.text is not None else cfg.text
    args.chromium = (
        params.chromium if params.chromium is not None else cfg.chromium_path
    )
    args.cache = params.cache if params.cache is not None else cfg.cache_md_always
    args.cached = params.cached if params.cached is not None else cfg.use_cached_md

    # Make sure we ask for high level logging to capture all info messages
    args.verbose = 4

    args.labels = params.labels if params.labels is not None else cfg.labels
    args.extend = params.extend if params.extend is not None else cfg.extend
    args.track = False  # Tracking functionality is disabled for the server
    args.sleep_time = (
        params.sleep_time if params.sleep_time is not None else cfg.sleep_time
    )

    # Internal variables forced to capture raw output and run correctly
    args.json = True
    args.show_link = True

    try:
        # Run scraper logic
        result = run_pipeline(args, cfg, is_cli=False)
        result["logs"] = log_capture.records
        return result
    except Exception as e:
        logger.error(f"Uncaught exception: {str(e)}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "logs": log_capture.records}
        )
    finally:
        # Clean up the logger captures
        logger.removeHandler(log_capture)



@app.get("/", response_class=HTMLResponse)
def home():
    """Return a premium, responsive single-page application dashboard"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exam Reader Dashboard</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-main: #0b0c10;
            --bg-card: #141621;
            --bg-input: #1a1d2e;
            --border-color: rgba(255, 255, 255, 0.06);
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --accent-purple: #9c27b0;
            --text-main: #f5f6fa;
            --text-secondary: #8b92b6;
            --success: #00e676;
            --warning: #ffb300;
            --error: #ff1744;
            --glow: 0 0 20px rgba(0, 242, 254, 0.35);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at 50% 50%, #151829 0%, var(--bg-main) 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            border-bottom: 1px solid var(--border-color);
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(15px);
            background: rgba(11, 12, 16, 0.6);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo-container {
            width: 45px;
            height: 45px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--glow);
        }

        .logo-container svg {
            width: 24px;
            height: 24px;
            fill: #000;
        }

        .brand-text h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(to right, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'Space Grotesk', sans-serif;
        }

        .brand-text p {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .server-status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 230, 118, 0.1);
            border: 1px solid rgba(0, 230, 118, 0.2);
            padding: 6px 14px;
            border-radius: 50px;
            font-size: 0.85rem;
            color: var(--success);
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
            box-shadow: 0 0 10px var(--success);
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        .main-container {
            flex: 1;
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 30px;
            padding: 30px 40px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }

        @media (max-width: 1024px) {
            .main-container {
                grid-template-columns: 1fr;
            }
        }

        /* Sidebar Control Panel */
        .sidebar {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 25px;
            height: fit-content;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .panel-title {
            font-size: 1.1rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 5px;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-group label {
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .form-input {
            background: var(--bg-input);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 11px 14px;
            color: var(--text-main);
            font-family: inherit;
            font-size: 0.9rem;
            transition: all 0.3s;
            width: 100%;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.15);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .switch-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .switch-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        /* Toggle switch styling */
        .switch {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 22px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.1);
            transition: .3s;
            border-radius: 34px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
        }

        input:focus + .slider {
            box-shadow: 0 0 8px rgba(0, 242, 254, 0.3);
        }

        input:checked + .slider:before {
            transform: translateX(22px);
        }

        .btn-run {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #050608;
            border: none;
            border-radius: 12px;
            padding: 14px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
            box-shadow: var(--glow);
        }

        .btn-run:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(0, 242, 254, 0.5);
            filter: brightness(1.1);
        }

        .btn-run:active {
            transform: translateY(1px);
        }

        .btn-run:disabled {
            background: #252838;
            box-shadow: none;
            color: var(--text-secondary);
            cursor: not-allowed;
            transform: none;
        }

        /* Dashboard Main Area */
        .dashboard-main {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .stat-icon.blue {
            background: rgba(79, 172, 254, 0.1);
            border: 1px solid rgba(79, 172, 254, 0.2);
            color: var(--accent-blue);
        }

        .stat-icon.purple {
            background: rgba(156, 39, 176, 0.1);
            border: 1px solid rgba(156, 39, 176, 0.2);
            color: var(--accent-purple);
        }

        .stat-icon.cyan {
            background: rgba(0, 242, 254, 0.1);
            border: 1px solid rgba(0, 242, 254, 0.2);
            color: var(--accent-cyan);
        }

        .stat-info {
            display: flex;
            flex-direction: column;
        }

        .stat-val {
            font-size: 1.6rem;
            font-weight: 700;
            font-family: 'Space Grotesk', sans-serif;
        }

        .stat-lbl {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* Tabs and Tables */
        .content-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            gap: 20px;
            flex: 1;
        }

        .tabs-header {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            gap: 15px;
            position: relative;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 12px 18px;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            color: var(--accent-cyan);
            font-weight: 600;
        }

        .tab-btn.active::after {
            content: "";
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--accent-cyan);
            box-shadow: 0 0 10px var(--accent-cyan);
            border-radius: 4px;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Filter bar */
        .filter-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            flex-wrap: wrap;
        }

        .search-wrapper {
            position: relative;
            flex: 1;
            max-width: 400px;
        }

        .search-wrapper svg {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            fill: var(--text-secondary);
        }

        .search-input {
            padding-left: 45px !important;
        }

        .btn-download {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 10px 18px;
            border-radius: 10px;
            font-family: inherit;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
        }

        .btn-download:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--text-secondary);
        }

        /* Responsive Table */
        .table-responsive {
            overflow-x: auto;
            max-height: 500px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        thead {
            background: #191c2c;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th {
            padding: 14px 18px;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 14px 18px;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-main);
            white-space: nowrap;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .makeup-badge {
            background: rgba(156, 39, 176, 0.15);
            border: 1px solid rgba(156, 39, 176, 0.3);
            color: #e040fb;
            font-size: 0.75rem;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 8px;
            font-weight: 500;
        }

        .no-data {
            text-align: center;
            color: var(--text-secondary);
            padding: 40px;
            font-style: italic;
        }

        /* Changes Tab List */
        .changes-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .change-item {
            background: rgba(0, 230, 118, 0.03);
            border: 1px solid rgba(0, 230, 118, 0.15);
            border-left: 4px solid var(--success);
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .change-item.no-changes {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--text-secondary);
            color: var(--text-secondary);
            font-style: italic;
        }

        /* Logs Console */
        .logs-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .logs-console {
            background: #06070a;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 18px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            color: var(--accent-cyan);
            text-shadow: 0 0 5px rgba(0, 242, 254, 0.25);
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .log-line {
            word-break: break-all;
            white-space: pre-wrap;
        }

        .log-line.error { color: var(--error); text-shadow: 0 0 5px rgba(255, 23, 68, 0.2); }
        .log-line.warning { color: var(--warning); text-shadow: 0 0 5px rgba(255, 179, 0, 0.2); }
        .log-line.success { color: var(--success); text-shadow: 0 0 5px rgba(0, 230, 118, 0.2); }

        /* Loader inside button */
        .spinner {
            border: 3px solid rgba(0, 0, 0, 0.1);
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border-left-color: #050608;
            animation: spin 1s linear infinite;
            display: none;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Scrollbar customizing */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>

    <header>
        <div class="header-brand">
            <div class="logo-container">
                <svg viewBox="0 0 24 24">
                    <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm-2-7h-5v5h5v-5z"/>
                </svg>
            </div>
            <div class="brand-text">
                <h1>Exam Schedule Reader</h1>
                <p>Istanbul University Science Faculty PDF Scraper & Viewer</p>
            </div>
        </div>
        <div class="server-status">
            <div class="status-dot"></div>
            <span>System Active</span>
        </div>
    </header>

    <div class="main-container">
        <!-- Sidebar Configuration Form -->
        <aside class="sidebar">
            <div class="panel-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--accent-cyan)">
                    <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
                </svg>
                <span>Scraper Controls</span>
            </div>
            
            <div class="form-group">
                <label for="url">University URL</label>
                <input type="text" id="url" class="form-input" placeholder="https://...">
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="prefix">File Name Prefix</label>
                    <input type="text" id="prefix" class="form-input" placeholder="MOLEK">
                </div>
                <div class="form-group">
                    <label for="semester">Semester Filter (Regex)</label>
                    <input type="text" id="semester" class="form-input" placeholder="6">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="port">Webdriver Port</label>
                    <input type="text" id="port" class="form-input" placeholder="9222">
                </div>
                <div class="form-group">
                    <label for="sleep_time">Sleep Time (s)</label>
                    <input type="number" id="sleep_time" class="form-input" placeholder="2">
                </div>
            </div>

            <div class="form-group">
                <label for="text">Search Link XPath</label>
                <input type="text" id="text" class="form-input" placeholder="//a...">
            </div>

            <div class="form-group">
                <label for="chromium">Chromium Binary Path</label>
                <input type="text" id="chromium" class="form-input" placeholder="/usr/bin/... or empty">
            </div>

            <div class="switch-container">
                <span class="switch-label">Cache PDF as Markdown</span>
                <label class="switch">
                    <input type="checkbox" id="cache" checked>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="switch-container">
                <span class="switch-label">Use Cached Markdown</span>
                <label class="switch">
                    <input type="checkbox" id="cached">
                    <span class="slider"></span>
                </label>
            </div>

            <button type="button" class="btn-run" id="btn-run" onclick="executeScraper()">
                <div class="spinner" id="btn-spinner"></div>
                <span id="btn-text">Execute Scraper</span>
            </button>
        </aside>

        <!-- Main Dashboard Area -->
        <main class="dashboard-main">
            <!-- Stats -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon cyan">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10H7v-2h10v2zm0-4H7V7h10v2zm0 8H7v-2h10v2z"/>
                        </svg>
                    </div>
                    <div class="stat-info">
                        <span class="stat-val" id="stat-total-exams">-</span>
                        <span class="stat-lbl">Exams Scraped</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon purple">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>
                        </svg>
                    </div>
                    <div class="stat-info">
                        <span class="stat-val" id="stat-semester-filter">-</span>
                        <span class="stat-lbl">Target Semester</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon blue">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                        </svg>
                    </div>
                    <div class="stat-info">
                        <span class="stat-val" id="stat-source-file" style="font-size:1.1rem; line-height: 2.2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">-</span>
                        <span class="stat-lbl">Source PDF</span>
                    </div>
                </div>
            </div>

            <!-- Content Card -->
            <div class="content-card">
                <div class="panel-title" style="border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 5px;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--accent-cyan)">
                        <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm-2-7h-5v5h5v-5z"/>
                    </svg>
                    <span>Scraped Exam Schedule</span>
                </div>

                <div class="filter-bar">
                    <div class="search-wrapper">
                        <svg viewBox="0 0 24 24">
                            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                        <input type="text" class="form-input search-input" id="search-current" placeholder="Search course, location, or instructor..." oninput="filterTable('table-current', this.value)">
                    </div>
                    <button class="btn-download" onclick="downloadJSON()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/>
                        </svg>
                        <span>Download JSON</span>
                    </button>
                </div>

                <div class="table-responsive">
                    <table id="table-current">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Day</th>
                                <th>Time</th>
                                <th>Sem</th>
                                <th>Course Code/Name</th>
                                <th>Location</th>
                                <th>Instructor</th>
                            </tr>
                        </thead>
                        <tbody id="body-current">
                            <tr>
                                <td colspan="7" class="no-data">No data available. Click "Execute Scraper" to fetch.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Terminal / Logs Card -->
            <div class="logs-card">
                <div class="panel-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--accent-cyan)">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-5 12H4v-2h11v2zm3-4H4V10h14v2zm0-4H4V6h14v2z"/>
                    </svg>
                    <span>Console Logs & Process Monitoring</span>
                </div>
                <div class="logs-console" id="console">
                    <div class="log-line success">Ready. Waiting for user action...</div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let currentRunData = null;

        // Fetch defaults on load
        window.addEventListener('DOMContentLoaded', async () => {
            await fetchConfig();
        });

        async function fetchConfig() {
            try {
                const response = await fetch('/config');
                const data = await response.json();
                
                document.getElementById('url').value = data.url || '';
                document.getElementById('prefix').value = data.file_name_prefix || '';
                document.getElementById('semester').value = data.target_yariyil || '';
                document.getElementById('port').value = data.port || '9222';
                document.getElementById('sleep_time').value = data.sleep_time || 2;
                document.getElementById('text').value = data.search_xpath || '';
                document.getElementById('chromium').value = data.chromium_path || '';
                document.getElementById('cache').checked = data.cache_md_always || false;
                document.getElementById('cached').checked = data.use_cached_md || false;
                
                addLogLine(`Configuration defaults loaded from config.yaml`, 'success');
            } catch (err) {
                addLogLine(`Error fetching config: ${err.message}`, 'error');
            }
        }

        function addLogLine(text, type = '') {
            const consoleBox = document.getElementById('console');
            const line = document.createElement('div');
            line.className = `log-line ${type}`;
            line.textContent = text;
            consoleBox.appendChild(line);
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }

        function renderTable(tableBodyId, data) {
            const body = document.getElementById(tableBodyId);
            body.innerHTML = '';
            
            let items = [];
            if (Array.isArray(data)) {
                items = data;
            } else if (data && typeof data === 'object') {
                items = Object.values(data);
            }
            
            if (items.length === 0) {
                body.innerHTML = `<tr><td colspan="7" class="no-data">No results matching filters found.</td></tr>`;
                return;
            }

            // Sort items by date (earliest first)
            items.sort((a, b) => {
                const partsA = a.date.split('/');
                const partsB = b.date.split('/');
                const dateA = new Date(partsA[2], partsA[1] - 1, partsA[0]);
                const dateB = new Date(partsB[2], partsB[1] - 1, partsB[0]);
                return dateA - dateB;
            });

            items.forEach(exam => {
                const tr = document.createElement('tr');
                
                let dateStr = exam.date;
                if (exam.date_makeup) {
                    dateStr += ` <span class="makeup-badge" title="Make-up / Bütünleme Sınavı">${exam.date_makeup}</span>`;
                }

                tr.innerHTML = `
                    <td>${dateStr}</td>
                    <td>${exam.day || ''}</td>
                    <td>${exam.time || ''}</td>
                    <td>${exam.semester || ''}</td>
                    <td style="font-weight:600; color:var(--accent-cyan)">${exam.course || ''}</td>
                    <td>${exam.location || '<span style="color:var(--text-secondary)">Not specified</span>'}</td>
                    <td style="font-style:italic">${exam.instructor || ''}</td>
                `;
                body.appendChild(tr);
            });
        }

        function filterTable(tableId, query) {
            const q = query.toLowerCase().trim();
            const rows = document.querySelectorAll(`#${tableId} tbody tr`);
            
            rows.forEach(row => {
                if (row.querySelector('.no-data')) return;
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(q) ? '' : 'none';
            });
        }

        async function executeScraper() {
            const btn = document.getElementById('btn-run');
            const spinner = document.getElementById('btn-spinner');
            const btnText = document.getElementById('btn-text');
            
            // Set loading state
            btn.disabled = true;
            spinner.style.display = 'inline-block';
            btnText.textContent = 'Processing...';
            addLogLine("Starting scraper session...", "warning");

            // Extract values
            const params = {
                url: document.getElementById('url').value || null,
                prefix: document.getElementById('prefix').value || null,
                semester: document.getElementById('semester').value || null,
                port: document.getElementById('port').value || null,
                sleep_time: parseInt(document.getElementById('sleep_time').value) || null,
                text: document.getElementById('text').value || null,
                chromium: document.getElementById('chromium').value || null,
                cache: document.getElementById('cache').checked,
                cached: document.getElementById('cached').checked
            };

            try {
                const response = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail?.error || data.detail || 'Scraping failed');
                }

                currentRunData = data;
                
                // Show logs if returned
                if (data.logs && Array.isArray(data.logs)) {
                    data.logs.forEach(log => {
                        let logType = '';
                        if (log.includes('[ERROR]')) logType = 'error';
                        else if (log.includes('[WARNING]')) logType = 'warning';
                        else if (log.includes('successfully') || log.includes('Done')) logType = 'success';
                        addLogLine(log, logType);
                    });
                }
                
                // Update stats
                document.getElementById('stat-total-exams').textContent = data.exams ? data.exams.length : 0;
                document.getElementById('stat-semester-filter').textContent = params.semester || '-';
                document.getElementById('stat-source-file').textContent = data.file_name ? data.file_name.split('/').pop() : 'Direct';
                document.getElementById('stat-source-file').title = data.file_name || '';

                // Render current runs table
                renderTable('body-current', data.exams);

                addLogLine(`Scraping complete. Results rendered successfully!`, 'success');
                
            } catch (err) {
                addLogLine(`Error during scrape: ${err.message}`, 'error');
            } finally {
                // Restore button state
                btn.disabled = false;
                spinner.style.display = 'none';
                btnText.textContent = 'Execute Scraper';
            }
        }

        function downloadJSON() {
            if (!currentRunData) {
                alert('No data available to download yet.');
                return;
            }
            
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentRunData, null, 4));
            const downloadAnchor = document.createElement('a');
            downloadAnchor.setAttribute("href",     dataStr);
            downloadAnchor.setAttribute("download", "scraped_exams.json");
            document.body.appendChild(downloadAnchor);
            downloadAnchor.click();
            downloadAnchor.remove();
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
