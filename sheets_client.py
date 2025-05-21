import os
import json
import gspread
from google.oauth2 import service_account
from utils.logger import logger

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_NAME = os.getenv("SHEET_NAME")

_default_ws = None  # lazy‑loaded worksheet cache

def _authorize():
    creds_path = os.getenv("GSHEETS_SERVICE_ACCOUNT_JSON_PATH")
    if not creds_path:
        raise RuntimeError("GSHEETS_SERVICE_ACCOUNT_JSON_PATH not set")
    with open(creds_path, "r", encoding="utf-8") as f:
        creds_dict = json.load(f)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def get_ws():
    """
    Get the worksheet object (lazy-loaded)
    
    Returns:
        gspread.Worksheet: Google Sheets worksheet object
    """
    global _default_ws
    if _default_ws:
        return _default_ws
    gc = _authorize()
    _default_ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    return _default_ws

def append_row(values: list[str]):
    """
    Append a row to the worksheet
    
    Args:
        values (list[str]): List of values to append as a new row
    """
    ws = get_ws()
    ws.append_row(values, value_input_option="USER_ENTERED")
    logger.info("Appended row: %s", values) 