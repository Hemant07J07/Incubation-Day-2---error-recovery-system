import os
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except Exception:
    gspread = None


def append_row_to_sheet(sheet_id, row, creds_path_env="GOOGLE_SERVICE_ACCOUNT_JSON_PATH", creds_path=None):
    """
    Append `row` (list) to first sheet of spreadsheet with key sheet_id.
    Requires env GOOGLE_SERVICE_ACCOUNT_JSON_PATH set to a service account JSON path,
    or creds_path parameter provided.
    """
    if gspread is None:
        print("gspread not installed or failed to import. Skipping Google Sheets append.")
        return False
    
    # Check for direct path first, then env var
    json_path = creds_path or os.getenv(creds_path_env)
    if not json_path or not os.path.exists(json_path):
        print("Google service account JSON not found or env var not set. Skipping Google Sheets append.")
        return False

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    sheet.append_row(row)
    return True