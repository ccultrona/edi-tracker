import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import re
from collections import defaultdict
import urllib.request
import io
from difflib import get_close_matches

st.set_page_config(
    page_title="EDI Connection Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Cabinet+Grotesk:wght@400;500;700;800;900&display=swap');

:root {
    --bg:      #080b10;
    --bg2:     #0d1117;
    --bg3:     #161b22;
    --bg4:     #1c2333;
    --accent:  #e8ff47;
    --blue:    #58a6ff;
    --purple:  #bc8cff;
    --green:   #3fb950;
    --orange:  #f0883e;
    --red:     #ff7b72;
    --text:    #e6edf3;
    --muted:   #7d8590;
    --muted2:  #30363d;
    --border:  #21262d;
    --border2: #30363d;
}

/* ── Base ── */
html, body, [class*="css"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stApp { background: var(--bg) !important; }
h1,h2,h3,h4 { font-family: 'Cabinet Grotesk', sans-serif !important; font-weight: 800 !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { font-size: 0.82rem !important; }
section[data-testid="stSidebar"] h3 {
    font-family: 'Cabinet Grotesk', sans-serif !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: var(--muted) !important;
    margin: 16px 0 8px !important;
}
.stTextInput input, .stMultiSelect > div, div[data-baseweb="select"] {
    background: var(--bg3) !important;
    border-color: var(--border2) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(232,255,71,0.12) !important; }
.stFileUploader { background: var(--bg3) !important; border: 1px dashed var(--border2) !important; border-radius: 8px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg2) !important;
    border-radius: 0 !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    letter-spacing: 0.02em !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; background: var(--bg3) !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--bg3) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 7px 16px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: var(--bg4) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 12px rgba(232,255,71,0.1) !important;
}
/* Primary buttons (download) */
.stDownloadButton > button {
    background: var(--accent) !important;
    color: #080b10 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
}
.stDownloadButton > button:hover { opacity: 0.88 !important; }

/* ── Cards ── */
.kpi-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px 20px 16px;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border2), transparent);
}
.kpi-num {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 2.4rem;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -0.03em;
}
.kpi-label {
    font-size: 0.68rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 500;
}
.kpi-sub {
    font-size: 0.6rem;
    color: var(--muted2);
    margin-top: 6px;
    letter-spacing: 0.03em;
}

/* ── Connection rows ── */
.conn-row {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 6px;
    transition: border-color 0.12s, background 0.12s;
    position: relative;
}
.conn-row:hover { border-color: var(--border2); background: var(--bg3); }
.conn-name { font-size: 0.88rem; font-weight: 500; color: var(--text); letter-spacing: -0.01em; }
.conn-partner { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }
.conn-meta { font-size: 0.68rem; color: var(--muted); text-align: right; }
.conn-pred { font-size: 0.72rem; font-weight: 600; text-align: right; margin-top: 1px; }

/* ── Progress bar ── */
.prog-bg {
    background: var(--bg3);
    border-radius: 2px;
    height: 3px;
    margin-top: 10px;
    overflow: hidden;
}
.prog-fill {
    height: 3px;
    border-radius: 2px;
    transition: width 0.3s ease;
}

/* ── Stage flow pill ── */
.stage-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    border: 1px solid;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Section header ── */
.sec-head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.25em;
    color: var(--muted);
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Alert / info boxes ── */
.box-warn  { background: #150f00; border: 1px solid #453200; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.box-info  { background: #0a1628; border: 1px solid #1f3459; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.box-ok    { background: #0a1f0f; border: 1px solid #1a4d24; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }
.box-muted { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; }

/* ── Tables ── */
div[data-testid="metric-container"] { background: var(--bg2) !important; padding: 16px !important; border-radius: 8px !important; border: 1px solid var(--border) !important; }
thead tr th { background: var(--bg3) !important; color: var(--muted) !important; font-size: 0.65rem !important; text-transform: uppercase !important; letter-spacing: 0.12em !important; border-bottom: 1px solid var(--border2) !important; font-family: 'IBM Plex Mono', monospace !important; }
tbody tr td { background: var(--bg2) !important; color: var(--text) !important; font-size: 0.78rem !important; border-bottom: 1px solid var(--border) !important; }
tbody tr:hover td { background: var(--bg3) !important; }
.dataframe { border: 1px solid var(--border) !important; border-radius: 8px !important; overflow: hidden !important; }

/* ── Spinner / success / warning Streamlit native ── */
div[data-testid="stAlert"] { border-radius: 6px !important; font-size: 0.8rem !important; font-family: 'IBM Plex Mono', monospace !important; }
.stSpinner { color: var(--accent) !important; }
.stCheckbox label { font-size: 0.8rem !important; color: var(--muted) !important; }

/* ── Sidebar logo ── */
.logo-block { padding: 4px 0 16px; border-bottom: 1px solid var(--border); margin-bottom: 4px; }
.logo-name  { font-family: 'Cabinet Grotesk', sans-serif; font-size: 1.2rem; font-weight: 900; color: var(--text); letter-spacing: -0.02em; }
.logo-tag   { font-size: 0.58rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.18em; margin-top: 2px; }
.logo-dot   { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); margin-right: 6px; box-shadow: 0 0 6px var(--accent); }

/* ── Page title ── */
.page-title { font-family: 'Cabinet Grotesk', sans-serif; font-size: 1.75rem; font-weight: 900; color: var(--text); letter-spacing: -0.03em; line-height: 1; margin-bottom: 2px; }
.page-sub   { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.04em; margin-bottom: 20px; }

/* ── Last refreshed badge ── */
.refresh-badge { display: inline-block; font-size: 0.62rem; color: var(--muted); background: var(--bg3); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; }

/* ── Confidence badges ── */
.conf-high { color: var(--green); }
.conf-med  { color: var(--orange); }
.conf-low  { color: var(--muted); }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_FILE = "edi_data.json"

STAGE_ORDER = {
    "1 Live": 1,
    "2 Ready to Go Live": 2,
    "3 In Testing": 3,
    "4 In Development": 4,
    "5 Up Next": 5,
    "6 Waiting": 6,
    "7 Flag - For Toro Review": 7,
    "8 Request to Cancel": 8,
    "9 No Longer Needed": 9,
    "9 Turned off": 9,
}
ACTIVE_STAGES = {1, 2, 3, 4, 5}
SNAPSHOT_COL_RE = re.compile(
    r"Expected Next Step\s+(\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?)",
    re.IGNORECASE
)

# ── Persistence ────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "connections": {},
        "import_log": [],       # [{label, source, date, new, updated, recovered}]
        "sheet_url": None,
        "last_sheet_refresh": None,
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

# ── Normalisation helpers ──────────────────────────────────────────────────────
def normalize_status(raw):
    if not raw or (isinstance(raw, float) and np.isnan(raw)):
        return None
    s = str(raw).strip()
    for key in STAGE_ORDER:
        if key.lower() in s.lower():
            return key
    m = re.search(r'\b([1-9])\b', s)
    if m:
        n = int(m.group(1))
        for key, val in STAGE_ORDER.items():
            if val == n:
                return key
    return None

def parse_excel_date(val):
    if val is None:
        return None
    try:
        if isinstance(val, float) and not np.isnan(val):
            return (datetime(1899, 12, 30) + timedelta(days=val)).strftime("%Y-%m-%d")
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d")
        s = str(val).strip()
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"]:
            try:
                return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
            except:
                pass
    except:
        pass
    return None

def parse_date_str(raw):
    """Parse a date string from various formats → YYYY-MM-DD or None."""
    if not raw:
        return None
    for fmt in ["%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m/%d"]:
        try:
            if fmt == "%m/%d":
                year_guess = "2025"
                parsed = datetime.strptime(str(raw).strip() + "/" + year_guess, "%m/%d/%Y")
                # bump year if date is in the past by more than 6 months — crude but ok
                if parsed < datetime.now() - timedelta(days=365):
                    parsed = parsed.replace(year=parsed.year + 1)
            else:
                parsed = datetime.strptime(str(raw).strip(), fmt)
            return parsed.strftime("%Y-%m-%d")
        except:
            pass
    return None

def extract_snapshot_cols(columns):
    """Return sorted list of (col_name, date_str) for weekly snapshot columns."""
    results = []
    for col in columns:
        m = SNAPSHOT_COL_RE.match(str(col))
        if m:
            d = parse_date_str(m.group(1))
            if d:
                results.append((col, d))
    return sorted(results, key=lambda x: x[1])

def parse_provider_shipper(raw):
    """
    Parse 'Vendor EDI Provider Shipper' field into (provider, shipper).
    Returns (provider, None) when only a provider is present — never duplicates
    a single value into both fields.

    Handles patterns:
      - 'Ryder / AMI'              -> ('Ryder', 'AMI')
      - 'Penske/Polaris'           -> ('Penske', 'Polaris')
      - 'Brenntag - Transplace'    -> ('Brenntag', 'Transplace')
      - 'Uber Freight (Poland Springs)' -> ('Uber Freight', 'Poland Springs')
      - 'Bello Tank (shipper), Princeton (provider)' -> ('Princeton', 'Bello Tank')
      - 'CNH'                      -> ('CNH', None)
      - 'E2Open'                   -> ('E2Open', None)
    """
    if not raw or (isinstance(raw, float) and np.isnan(raw)):
        return "Unknown", None
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return "Unknown", None

    # Pattern 1: explicit (shipper) / (provider) labels
    shipper_m = re.search(r'([^,()]+)\s*\(shipper\)', s, re.IGNORECASE)
    provider_m = re.search(r'([^,()]+)\s*\(provider\)', s, re.IGNORECASE)
    if shipper_m and provider_m:
        return provider_m.group(1).strip(), shipper_m.group(1).strip()
    if provider_m:
        return provider_m.group(1).strip(), None
    if shipper_m:
        return "Unknown", shipper_m.group(1).strip()

    # Pattern 2: 'Name (Shipper Name)' — parenthetical is the shipper
    paren_m = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', s)
    if paren_m:
        return paren_m.group(1).strip(), paren_m.group(2).strip()

    # Pattern 3: separator (/, -, or comma) → left=provider, right=shipper
    parts = re.split(r'\s*/\s*|\s+-\s+', s, maxsplit=1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()

    # Pattern 4: no separator → provider only, no shipper
    return s.strip(), None

def connection_key(customer, vendor):
    c = str(customer).strip() if customer and not (isinstance(customer, float) and np.isnan(customer)) else "Unknown"
    v = str(vendor).strip() if vendor and not (isinstance(vendor, float) and np.isnan(vendor)) else "Unknown"
    return f"{c}||{v}"

# ── Auto-detect snapshot date from file ───────────────────────────────────────
def auto_detect_snapshot_date(df):
    """
    Try to determine the most recent date this snapshot represents by:
    1. Finding the latest snapshot column date (e.g. 'Expected Next Step 11/21')
    2. Finding the latest 'Latest Status Update' date in the data
    Returns (date_str, source_description)
    """
    candidates = []

    # Method 1: latest snapshot column header date
    snap_cols = extract_snapshot_cols(df.columns)
    if snap_cols:
        latest_col_date = snap_cols[-1][1]
        candidates.append((latest_col_date, f"latest snapshot column ({snap_cols[-1][0]})"))

    # Method 2: latest 'Latest Status Update' date in rows
    update_col = next((c for c in df.columns if "latest status update" in str(c).lower()),
                      next((c for c in df.columns if "status update" in str(c).lower()), None))
    if update_col is not None:
        dates = []
        for val in df[update_col]:
            d = parse_excel_date(val)
            if d:
                dates.append(d)
        if dates:
            candidates.append((max(dates), "latest 'Status Update' date in data"))

    if not candidates:
        return datetime.today().strftime("%Y-%m-%d"), "today (no date found in file)"

    # Use the latest of the two
    best = max(candidates, key=lambda x: x[0])
    return best[0], best[1]

# ── Google Sheets fetch ────────────────────────────────────────────────────────
def fetch_google_sheet(url):
    """
    Fetch a public Google Sheet as a DataFrame.
    Extracts sheet ID and gid directly from the URL — no tab guessing needed.
    """
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        raise ValueError("Could not find spreadsheet ID. Paste the full Google Sheets URL.")
    sheet_id = m.group(1)

    # Extract gid — check both ?gid= and #gid= patterns
    gid_m = re.search(r'[#?&]gid=(\d+)', url)
    gid = gid_m.group(1) if gid_m else "0"

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    req = urllib.request.Request(csv_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; EDITracker/1.0)",
        "Accept": "text/csv,text/plain,*/*",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")

    df = pd.read_csv(io.StringIO(raw))

    # Validate we got the right tab
    if "EDI Connection Status" not in df.columns and "Customer" not in df.columns:
        raise ValueError(
            f"The tab loaded (gid={gid}) doesn't look like the Connections & Status sheet. "
            "Make sure you paste the URL while on the correct tab."
        )
    return df

# ── Fuzzy column mapping ───────────────────────────────────────────────────────
# Each canonical field lists aliases in priority order (most specific first)
COLUMN_SCHEMA = {
    "customer": {
        "required": True,
        "aliases": ["customer", "carrier", "customer name", "client", "company"],
        "description": "Customer / Carrier name",
    },
    "vendor": {
        "required": True,
        "aliases": [
            "vendor edi provider shipper", "vendor (edi provider / shipper)",
            "vendor edi provider", "vendor", "provider shipper", "provider / shipper",
            "edi provider", "connection", "shipper provider", "provider"
        ],
        "description": "Vendor / EDI Provider / Shipper",
    },
    "status": {
        "required": True,
        "aliases": [
            "edi connection status", "connection status", "edi status",
            "status", "customer stage", "stage", "connection stage"
        ],
        "description": "EDI Connection Status",
    },
    "last_update": {
        "required": False,
        "aliases": [
            "latest status update", "last update", "status update",
            "last updated", "updated", "date updated", "update date", "latest update"
        ],
        "description": "Latest Status Update date",
    },
    "ball_in_court": {
        "required": False,
        "aliases": ["ball in court", "bic", "waiting on", "blocked by", "owner"],
        "description": "Ball In Court",
    },
}

def fuzzy_map_columns(df_columns):
    """
    Map actual DataFrame columns to canonical field names.
    Returns (mapping, warnings, errors)
      mapping  = {canonical: actual_col_name}
      warnings = list of non-fatal notices (fuzzy matches, missing optional cols)
      errors   = list of fatal problems (missing required cols)
    """
    cols_lower = {str(c).lower().strip(): str(c) for c in df_columns}
    mapping = {}
    warnings = []
    errors = []

    for canonical, info in COLUMN_SCHEMA.items():
        found = None
        match_detail = None

        # 1. Exact match
        for alias in info["aliases"]:
            if alias in cols_lower:
                found = cols_lower[alias]
                match_detail = "exact"
                break

        # 2. Substring match (alias inside column name or vice versa)
        if not found:
            for alias in info["aliases"]:
                for col_lower, col_actual in cols_lower.items():
                    if alias in col_lower or col_lower in alias:
                        found = col_actual
                        match_detail = f"partial match on '{col_actual}'"
                        break
                if found:
                    break

        # 3. Fuzzy difflib match
        if not found:
            all_lowers = list(cols_lower.keys())
            for alias in info["aliases"]:
                hits = get_close_matches(alias, all_lowers, n=1, cutoff=0.72)
                if hits:
                    found = cols_lower[hits[0]]
                    match_detail = f"fuzzy match on '{found}'"
                    break

        if found:
            mapping[canonical] = found
            if match_detail != "exact":
                warnings.append(
                    f"⚠️ **{info['description']}** — matched to column **'{found}'** ({match_detail}). "
                    f"If this is wrong, rename the column to one of: `{info['aliases'][0]}`"
                )
        elif info["required"]:
            errors.append(
                f"❌ **{info['description']}** — required column not found. "
                f"Expected a column named like: `{'`, `'.join(info['aliases'][:3])}`"
            )
        else:
            warnings.append(
                f"ℹ️ **{info['description']}** — optional column not found, will be skipped."
            )

    return mapping, warnings, errors

def validate_dataframe(df, mapping):
    """
    After column mapping, run data-level validation.
    Returns (warnings, errors) with row-level detail.
    """
    warnings = []
    errors = []
    customer_col = mapping.get("customer")
    status_col = mapping.get("status")
    vendor_col = mapping.get("vendor")

    if not customer_col or customer_col not in df.columns:
        errors.append("❌ Cannot find any rows — customer column is missing.")
        return warnings, errors

    # Count data rows
    data_rows = df[df[customer_col].notna() & (df[customer_col].astype(str).str.strip() != "") & (df[customer_col].astype(str).str.strip() != "nan")]
    total = len(data_rows)
    if total == 0:
        errors.append("❌ No data rows found — the file appears to be empty after the header row.")
        return warnings, errors

    # Check status values
    if status_col and status_col in df.columns:
        no_status = data_rows[data_rows[status_col].isna() | (data_rows[status_col].astype(str).str.strip() == "")].shape[0]
        if no_status > 0:
            warnings.append(f"⚠️ **{no_status} of {total} rows** have no status value — they will still be imported but won't count toward predictions.")

        # Check for unrecognized status values
        all_statuses = data_rows[status_col].dropna().unique()
        unrecognized = [s for s in all_statuses if normalize_status(str(s)) is None and str(s).strip() not in ("", "nan")]
        if unrecognized:
            warnings.append(
                f"⚠️ **Unrecognized status values** found: {', '.join(f'`{s}`' for s in unrecognized[:5])}. "
                "These rows will be imported but excluded from predictions. "
                "Expected values like: `1 Live`, `2 Ready to Go Live`, `3 In Testing`, `4 In Development`, `5 Up Next`."
            )

    # Check vendor column
    if vendor_col and vendor_col in df.columns:
        no_vendor = data_rows[data_rows[vendor_col].isna() | (data_rows[vendor_col].astype(str).str.strip() == "")].shape[0]
        if no_vendor > 0:
            warnings.append(f"⚠️ **{no_vendor} rows** are missing a vendor/provider value — predictions won't be available for these connections.")

    return warnings, errors

# ── Core ingestion ─────────────────────────────────────────────────────────────
def ingest_dataframe(df, snapshot_label, existing_data, mark_missing_as_deleted=False):
    """
    Parse df and merge into existing_data using fuzzy column mapping.
    Returns (data, new, updated, recovered, total, col_warnings, col_errors, data_warnings)
    """
    connections = existing_data.get("connections", {})
    new_count = updated_count = recovered_count = 0

    # Fuzzy-map columns
    mapping, col_warnings, col_errors = fuzzy_map_columns(df.columns)

    # Stop if required columns missing
    if col_errors:
        return existing_data, 0, 0, 0, 0, col_warnings, col_errors, []

    customer_col = mapping["customer"]
    vendor_col   = mapping["vendor"]
    status_col   = mapping["status"]
    update_col   = mapping.get("last_update")
    bic_col      = mapping.get("ball_in_court")

    # Data-level validation
    data_warnings, data_errors = validate_dataframe(df, mapping)
    col_errors.extend(data_errors)
    if data_errors:
        return existing_data, 0, 0, 0, 0, col_warnings, col_errors, data_warnings

    # Drop blank rows
    df = df[df[customer_col].notna()]
    df = df[df[customer_col].astype(str).str.strip().str.lower() != ""]
    df = df[df[customer_col].astype(str).str.strip().str.lower() != "nan"]

    snap_cols = extract_snapshot_cols(df.columns)
    keys_in_this_upload = set()

    for _, row in df.iterrows():
        customer = row.get(customer_col, "")
        vendor   = row.get(vendor_col, "") if vendor_col else ""
        if not customer or (isinstance(customer, float) and np.isnan(customer)):
            continue
        if str(customer).strip() in ("", "nan"):
            continue

        key = connection_key(customer, vendor)
        keys_in_this_upload.add(key)

        provider, shipper = parse_provider_shipper(vendor)
        current_status = normalize_status(row.get(status_col, ""))
        last_update    = parse_excel_date(row.get(update_col)) if update_col else None
        ball_in_court  = str(row.get(bic_col, "")).strip() if bic_col else ""

        is_new = key not in connections
        if is_new:
            new_count += 1
            connections[key] = {
                "customer":     str(customer).strip(),
                "vendor":       str(vendor).strip() if not (isinstance(vendor, float) and np.isnan(vendor)) else "",
                "provider":     provider,
                "shipper":      shipper,
                "snapshots":    {},
                "status":       current_status,
                "last_update":  last_update,
                "ball_in_court": ball_in_court,
                "deleted":      False,
                "first_seen":   snapshot_label,
            }
        else:
            updated_count += 1
            if connections[key].get("deleted"):
                recovered_count += 1
                connections[key]["deleted"] = False

        conn = connections[key]

        existing_snaps = conn.get("snapshots", {})
        latest_known = max(existing_snaps.keys()) if existing_snaps else "0000-00-00"

        if snapshot_label >= latest_known:
            if current_status:
                conn["status"] = current_status
            if last_update:
                existing_lu = conn.get("last_update") or "0000-00-00"
                if last_update > existing_lu:
                    conn["last_update"] = last_update
            conn["ball_in_court"] = ball_in_court

        if current_status:
            conn["snapshots"][snapshot_label] = current_status

        for col, date_str in snap_cols:
            val = row.get(col, "")
            if val and not (isinstance(val, float) and np.isnan(val)):
                s = normalize_status(str(val))
                if s and date_str not in conn["snapshots"]:
                    conn["snapshots"][date_str] = s

    if mark_missing_as_deleted:
        for key, conn in connections.items():
            if key not in keys_in_this_upload and not conn.get("deleted"):
                conn["deleted"] = True

    existing_data["connections"] = connections
    return existing_data, new_count, updated_count, recovered_count, len(keys_in_this_upload), col_warnings, col_errors, data_warnings

# ── Statistical model ──────────────────────────────────────────────────────────
def compute_stage_transitions(conn):
    snapshots = conn.get("snapshots", {})
    if not snapshots:
        return {}
    transitions = {}
    prev = None
    for date_str, status in sorted(snapshots.items()):
        n = STAGE_ORDER.get(status)
        if n and n in ACTIVE_STAGES and n != prev:
            if n not in transitions:
                transitions[n] = date_str
            prev = n
    return transitions

def compute_duration(conn):
    t = compute_stage_transitions(conn)
    start = t.get(5)
    end = t.get(2) or t.get(1)
    if not start:
        return None, None, None
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
    except:
        return None, None, None
    if end:
        try:
            e = datetime.strptime(end, "%Y-%m-%d")
            return (e - s).days, start, end
        except:
            pass
    return None, start, None

def build_model(connections):
    by_provider = defaultdict(list)
    by_shipper = defaultdict(list)
    by_combined = defaultdict(list)
    overall = []

    for conn in connections.values():
        status = conn.get("status", "")
        if STAGE_ORDER.get(status, 99) not in {1, 2}:
            continue
        dur, _, _ = compute_duration(conn)
        if dur and 1 <= dur <= 730:
            p = conn.get("provider", "Unknown")
            s = conn.get("shipper")  # May be None if no shipper in field
            by_provider[p].append(dur)
            if s:  # Only add to shipper stats if a shipper actually exists
                by_shipper[s].append(dur)
                by_combined[f"{p} / {s}"].append(dur)
            overall.append(dur)

    def stats(lst):
        if not lst:
            return None
        a = np.array(lst)
        return {
            "mean": float(np.mean(a)),
            "median": float(np.median(a)),
            "p25": float(np.percentile(a, 25)),
            "p75": float(np.percentile(a, 75)),
            "min": float(np.min(a)),
            "max": float(np.max(a)),
            "n": len(lst),
        }

    return {
        "by_provider": {k: stats(v) for k, v in by_provider.items()},
        "by_shipper": {k: stats(v) for k, v in by_shipper.items()},
        "by_combined": {k: stats(v) for k, v in by_combined.items()},
        "overall": stats(overall),
    }

# ── Historical data export / import ───────────────────────────────────────────
HISTORICAL_EXPORT_VERSION = "2"  # v2: prediction-power focused

# ── Prediction Power Export ────────────────────────────────────────────────────
# This export stores the computed durations that drive the model.
# It does NOT need raw snapshots — just the duration facts per connection.
# Re-importing this file fully restores predictive power with zero retraining.

def build_export_df(connections):
    """
    Export the data that matters for predictions: completed connection durations
    by provider and shipper. This is what the model actually uses.
    Raw snapshot history is included as a secondary record but is not required for restore.
    """
    rows = []
    for key, conn in connections.items():
        transitions = compute_stage_transitions(conn)
        duration, start, end = compute_duration(conn)
        rows.append({
            # Identity
            "_export_version": HISTORICAL_EXPORT_VERSION,
            "_connection_key": key,
            "customer":        conn.get("customer", ""),
            "vendor":          conn.get("vendor", ""),
            "provider":        conn.get("provider", ""),
            "shipper":         conn.get("shipper") or "",
            # The predictive data — this is what the model uses
            "duration_days":   duration if duration else "",
            "stage_5_date":    transitions.get(5, ""),
            "stage_4_date":    transitions.get(4, ""),
            "stage_3_date":    transitions.get(3, ""),
            "stage_2_date":    transitions.get(2, ""),
            "stage_1_date":    transitions.get(1, ""),
            # Current state
            "current_status":  conn.get("status", ""),
            "last_update":     conn.get("last_update", ""),
            "deleted":         conn.get("deleted", False),
            "first_seen":      conn.get("first_seen", ""),
        })
    return pd.DataFrame(rows)

def build_model_summary_df(model):
    """
    Export a human-readable summary of what the model has learned —
    median build time per provider and per shipper. Good for reviewing
    and understanding the model's predictive power at a glance.
    """
    rows = []
    for provider, stats in sorted(model.get("by_provider", {}).items(), key=lambda x: -x[1]["n"]):
        rows.append({
            "type":         "Provider",
            "name":         provider,
            "median_days":  round(stats["median"]),
            "best_case_p25": round(stats["p25"]),
            "likely_max_p75": round(stats["p75"]),
            "completed_jobs": stats["n"],
            "min_days":     round(stats["min"]),
            "max_days":     round(stats["max"]),
        })
    for shipper, stats in sorted(model.get("by_shipper", {}).items(), key=lambda x: -x[1]["n"]):
        rows.append({
            "type":         "Shipper",
            "name":         shipper,
            "median_days":  round(stats["median"]),
            "best_case_p25": round(stats["p25"]),
            "likely_max_p75": round(stats["p75"]),
            "completed_jobs": stats["n"],
            "min_days":     round(stats["min"]),
            "max_days":     round(stats["max"]),
        })
    for combined, stats in sorted(model.get("by_combined", {}).items(), key=lambda x: -x[1]["n"]):
        rows.append({
            "type":         "Combined",
            "name":         combined,
            "median_days":  round(stats["median"]),
            "best_case_p25": round(stats["p25"]),
            "likely_max_p75": round(stats["p75"]),
            "completed_jobs": stats["n"],
            "min_days":     round(stats["min"]),
            "max_days":     round(stats["max"]),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def restore_from_export(df, existing_data):
    """
    Re-import an exported CSV to restore predictive power.
    Only needs duration_days + stage dates + provider/shipper — no snapshots required.
    Returns (data, restored_count, updated_count, warnings, errors)
    """
    connections = existing_data.get("connections", {})
    restored = updated = 0
    warnings = []
    errors = []

    required = {"customer", "provider", "duration_days"}
    missing = required - set(df.columns)
    if missing:
        errors.append(
            f"❌ Not a valid prediction export file — missing columns: {missing}. "
            "Only upload files downloaded from the Export tab of this app."
        )
        return existing_data, 0, 0, warnings, errors

    for _, row in df.iterrows():
        customer = str(row.get("customer", "")).strip()
        vendor   = str(row.get("vendor", "")).strip()
        if not customer or customer == "nan":
            continue

        key = str(row.get("_connection_key", "")).strip() or connection_key(customer, vendor)
        provider = str(row.get("provider", "")).strip()
        shipper_raw = str(row.get("shipper", "")).strip()
        shipper = shipper_raw if shipper_raw and shipper_raw != "nan" else None
        if not provider or provider == "nan":
            provider, shipper = parse_provider_shipper(vendor)

        is_new = key not in connections
        if is_new:
            restored += 1
            connections[key] = {
                "customer":      customer,
                "vendor":        vendor,
                "provider":      provider,
                "shipper":       shipper,
                "snapshots":     {},
                "status":        str(row.get("current_status", "")).strip() or "",
                "last_update":   str(row.get("last_update", ""))[:10] if str(row.get("last_update", "")) not in ("", "nan") else None,
                "ball_in_court": "",
                "deleted":       str(row.get("deleted", "False")).lower() == "true",
                "first_seen":    str(row.get("first_seen", "")).strip(),
            }
        else:
            updated += 1

        conn = connections[key]

        # Restore stage dates as synthetic snapshots — this is what drives duration calculation
        stage_map = {
            "stage_5_date": (5, "5 Up Next"),
            "stage_4_date": (4, "4 In Development"),
            "stage_3_date": (3, "3 In Testing"),
            "stage_2_date": (2, "2 Ready to Go Live"),
            "stage_1_date": (1, "1 Live"),
        }
        for col, (stage_num, stage_status) in stage_map.items():
            date_val = str(row.get(col, "")).strip()
            if date_val and date_val not in ("", "nan"):
                # Only add if we don't already have this stage — never overwrite
                existing_transitions = compute_stage_transitions(conn)
                if stage_num not in existing_transitions:
                    conn["snapshots"][date_val] = stage_status

        # If no stage dates but duration_days is present, synthesize start/end dates
        dur_raw = str(row.get("duration_days", "")).strip()
        if dur_raw and dur_raw not in ("", "nan"):
            try:
                dur = int(float(dur_raw))
                transitions = compute_stage_transitions(conn)
                if 5 not in transitions and 2 not in transitions and dur > 0:
                    # Synthesize: use first_seen as approximate start
                    first_seen = conn.get("first_seen", "")
                    if first_seen and first_seen not in ("", "nan"):
                        try:
                            start_dt = datetime.strptime(first_seen[:10], "%Y-%m-%d")
                            end_dt   = start_dt + timedelta(days=dur)
                            conn["snapshots"][first_seen[:10]] = "5 Up Next"
                            conn["snapshots"][end_dt.strftime("%Y-%m-%d")] = "2 Ready to Go Live"
                        except:
                            pass
            except:
                pass

    existing_data["connections"] = connections
    return existing_data, restored, updated, warnings, errors

def predict(conn, model):
    """
    Build a blended prediction using both provider AND shipper history independently.
    
    Priority logic:
    1. If we have combined (provider+shipper) history with enough samples → use that (most specific)
    2. Otherwise blend provider signal + shipper signal together, weighted by sample size
    3. Fall back to whichever single signal exists
    4. Last resort: overall historical average
    
    Always returns (stats_dict, basis_label, basis_name, detail_dict)
    detail_dict contains the individual provider/shipper signals for display.
    """
    p = conn.get("provider", "Unknown")
    s = conn.get("shipper")  # May be None
    combined_key = f"{p} / {s}" if s else None

    by_combined  = model.get("by_combined", {})
    by_provider  = model.get("by_provider", {})
    by_shipper   = model.get("by_shipper", {})
    overall      = model.get("overall")

    provider_stats  = by_provider.get(p) if p and p != "Unknown" else None
    shipper_stats   = by_shipper.get(s) if s else None
    combined_stats  = by_combined.get(combined_key) if combined_key else None

    detail = {
        "provider": provider_stats,
        "shipper":  shipper_stats,
        "combined": combined_stats,
    }

    # ── Case 1: combined has enough samples → most specific, highest confidence ──
    if combined_stats and combined_stats["n"] >= 3:
        return combined_stats, "combined", combined_key, detail

    # ── Case 2: blend provider + shipper signals weighted by sample size ──
    signals = []
    if provider_stats and provider_stats["n"] >= 1:
        signals.append((provider_stats, provider_stats["n"], "provider"))
    if shipper_stats and shipper_stats["n"] >= 1:
        signals.append((shipper_stats, shipper_stats["n"], "shipper"))

    if len(signals) == 2:
        # Weighted blend of both medians
        w_total = signals[0][1] + signals[1][1]
        blended_median = (signals[0][0]["median"] * signals[0][1] + signals[1][0]["median"] * signals[1][1]) / w_total
        blended_p25    = (signals[0][0]["p25"]    * signals[0][1] + signals[1][0]["p25"]    * signals[1][1]) / w_total
        blended_p75    = (signals[0][0]["p75"]    * signals[0][1] + signals[1][0]["p75"]    * signals[1][1]) / w_total
        blended_n      = w_total
        blended = {
            "median": blended_median,
            "p25":    blended_p25,
            "p75":    blended_p75,
            "mean":   blended_median,
            "min":    min(signals[0][0]["min"], signals[1][0]["min"]),
            "max":    max(signals[0][0]["max"], signals[1][0]["max"]),
            "n":      blended_n,
        }
        basis_name = f"{p} (provider) + {s} (shipper)"
        return blended, "blended", basis_name, detail

    # ── Case 3: only one signal available ──
    if len(signals) == 1:
        stats, _, src = signals[0]
        name = p if src == "provider" else s
        return stats, src, name, detail

    # ── Case 4: combined with < 3 samples (better than nothing) ──
    if combined_stats:
        return combined_stats, "combined", combined_key, detail

    # ── Case 5: overall fallback ──
    if overall:
        return overall, "overall", "historical average", detail

    return None, None, None, detail

def confidence_label(basis, n):
    if basis == "combined" and n >= 5:
        return "HIGH", "conf-high"
    if basis in ("combined", "blended") and n >= 3:
        return "MED", "conf-med"
    if basis in ("provider", "shipper") and n >= 2:
        return "MED", "conf-med"
    return "LOW", "conf-low"

# ── Load state + auto-fetch on startup ────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.auto_loaded = False

# Auto-fetch from Google Sheet every time the app starts (solves Streamlit Cloud persistence)
if not st.session_state.get("auto_loaded"):
    _saved_url = st.session_state.data.get("sheet_url")
    if _saved_url:
        with st.spinner("Loading latest data from Google Sheet..."):
            try:
                _df = fetch_google_sheet(_saved_url)
                _snap_date, _snap_source = auto_detect_snapshot_date(_df)
                _result = ingest_dataframe(
                    _df, _snap_date, st.session_state.data, mark_missing_as_deleted=True
                )
                st.session_state.data = _result[0]
                if _result[6]:  # col_errors on startup — log silently, don't block UI
                    st.session_state["startup_errors"] = _result[6]
                if _result[5]:
                    st.session_state["startup_warnings"] = _result[5]
                st.session_state.data["last_sheet_refresh"] = datetime.now().isoformat()
                save_data(st.session_state.data)
            except Exception as _e:
                st.warning(f"Could not auto-refresh sheet on startup: {_e}")
    st.session_state.auto_loaded = True

data = st.session_state.data
connections = data.get("connections", {})
model = build_model(connections)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-block">
        <div class="logo-name"><span class="logo-dot"></span>EDI Tracker</div>
        <div class="logo-tag">Connection Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live Google Sheet section ──
    st.markdown("### 🔗 Live Google Sheet")

    saved_url = data.get("sheet_url", "")
    sheet_url = st.text_input(
        "Paste your Google Sheet URL",
        value=saved_url or "",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Share your sheet as 'Anyone with link can view', then paste the URL here."
    )

    if sheet_url and sheet_url != saved_url:
        data["sheet_url"] = sheet_url
        save_data(data)

    if sheet_url:
        last_refresh = data.get("last_sheet_refresh")
        if last_refresh:
            st.markdown(f'<div style="font-size:0.68rem;color:var(--muted)">Last refreshed: {last_refresh[:16].replace("T"," ")}</div>', unsafe_allow_html=True)

        if st.button("🔄 Refresh from Google Sheet"):
            with st.spinner("Fetching latest data..."):
                try:
                    df = fetch_google_sheet(sheet_url)
                    # Auto-detect date
                    snap_date, snap_source = auto_detect_snapshot_date(df)
                    data, new_c, upd_c, rec_c, total, col_warns, col_errs, data_warns = ingest_dataframe(
                        df, snap_date, data, mark_missing_as_deleted=True
                    )

                    # Show column mapping issues before proceeding
                    for w in col_warns:
                        st.warning(w)
                    for e in col_errs:
                        st.error(e)
                    for w in data_warns:
                        st.warning(w)

                    if col_errs:
                        st.error("⛔ Import stopped due to column errors above. Check your sheet structure.")
                    else:
                        data["last_sheet_refresh"] = datetime.now().isoformat()
                        log_entry = {
                            "label": snap_date,
                            "source": "Google Sheet (live)",
                            "date_detected_from": snap_source,
                            "imported_at": datetime.now().isoformat(),
                            "new": new_c,
                            "updated": upd_c,
                            "recovered": rec_c,
                            "total": total,
                        }
                        data.setdefault("import_log", []).append(log_entry)
                        save_data(data)
                        st.session_state.data = data
                        connections = data["connections"]
                        model = build_model(connections)
                        st.success(f"✅ Refreshed — {total} rows · snapshot date: {snap_date}")
                        if rec_c:
                            st.info(f"🔁 {rec_c} deleted connections recovered")
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not fetch sheet: {e}")
                    st.markdown("""
                    <div style="font-size:0.72rem;color:var(--muted);margin-top:8px">
                    Make sure your sheet is shared as <b>Anyone with the link can view</b>.<br>
                    File → Share → Change to Anyone with the link.
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── CSV / Excel upload section ──
    st.markdown("### 📥 Upload Historical Snapshots")
    st.markdown('<div style="font-size:0.72rem;color:var(--muted);margin-bottom:10px">Upload older versions in any order — dates are auto-detected from the file.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Excel or CSV snapshot",
        type=["xlsx", "csv", "xls"],
    )

    def load_upload_df(f):
        """Load uploaded file into a DataFrame, finding the right tab for Excel files."""
        f.seek(0)
        if f.name.endswith(".csv"):
            return pd.read_csv(f)
        else:
            xl = pd.ExcelFile(f)
            # Score each sheet and pick the one most likely to be Connections & Status
            best_sheet = xl.sheet_names[0]
            best_score = -1
            for sname in xl.sheet_names:
                score = 0
                if "connection" in sname.lower(): score += 3
                if "status" in sname.lower(): score += 3
                # Also peek at columns
                try:
                    peek = pd.read_excel(f, sheet_name=sname, nrows=1)
                    cols = [str(c).lower() for c in peek.columns]
                    if any("edi connection status" in c for c in cols): score += 10
                    if any("customer" == c.strip() for c in cols): score += 3
                    if any("vendor edi" in c for c in cols): score += 5
                except:
                    pass
                if score > best_score:
                    best_score = score
                    best_sheet = sname
            f.seek(0)
            return pd.read_excel(f, sheet_name=best_sheet)

    if uploaded:
        try:
            preview_df = load_upload_df(uploaded)
            auto_date, auto_source = auto_detect_snapshot_date(preview_df)
            row_count = preview_df["Customer"].notna().sum() if "Customer" in preview_df.columns else len(preview_df)
            st.markdown(
                f'<div style="font-size:0.7rem;color:var(--accent);margin-bottom:6px">' +
                f'📅 Auto-detected: <b>{auto_date}</b><br>' +
                f'<span style="color:var(--muted)">from {auto_source} · {row_count} connections found</span></div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            preview_df = None
            auto_date = datetime.today().strftime("%Y-%m-%d")
            auto_source = "today (auto-detect failed)"
            st.warning(f"Could not preview file: {e}")

        override = st.checkbox("Override detected date", value=False)
        if override:
            try:
                default_dt = datetime.strptime(auto_date, "%Y-%m-%d")
            except:
                default_dt = datetime.today()
            snap_date_input = st.date_input("Snapshot date", value=default_dt)
            snap_label = snap_date_input.strftime("%Y-%m-%d")
        else:
            snap_label = auto_date

        if st.button("⬆️ Import Snapshot"):
            try:
                df = load_upload_df(uploaded)
                data, new_c, upd_c, rec_c, total, col_warns, col_errs, data_warns = ingest_dataframe(df, snap_label, data)

                # Always show column mapping feedback
                if col_warns or col_errs or data_warns:
                    with st.expander("📋 Import diagnostics", expanded=bool(col_errs or data_warns)):
                        if col_errs:
                            st.markdown("**Column errors — import blocked:**")
                            for e in col_errs:
                                st.error(e)
                        if col_warns:
                            st.markdown("**Column mapping notes:**")
                            for w in col_warns:
                                st.warning(w)
                        if data_warns:
                            st.markdown("**Data quality notes:**")
                            for w in data_warns:
                                st.warning(w)

                if col_errs:
                    st.error("⛔ Import stopped — fix the column errors above and try again.")
                else:
                    log_entry = {
                        "label": snap_label,
                        "source": uploaded.name,
                        "date_detected_from": auto_source,
                        "imported_at": datetime.now().isoformat(),
                        "new": new_c,
                        "updated": upd_c,
                        "recovered": rec_c,
                        "total": total,
                        "warnings": len(col_warns) + len(data_warns),
                    }
                    data.setdefault("import_log", []).append(log_entry)
                    save_data(data)
                    st.session_state.data = data
                    connections = data["connections"]
                    model = build_model(connections)
                    parts = []
                    if new_c: parts.append(f"🆕 {new_c} new")
                    if upd_c: parts.append(f"🔄 {upd_c} updated")
                    if rec_c: parts.append(f"🔁 {rec_c} recovered")
                    st.success(f"✅ Imported {total} rows · {snap_label}" + (f" — {', '.join(parts)}" if parts else ""))
                    st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
                st.info("If this is an older file format, check that it has at least a Customer column and a Status column.")

    st.markdown("---")

    # Filters
    st.markdown("### 🔍 Filters")
    all_providers = sorted(set(c.get("provider", "Unknown") for c in connections.values() if not c.get("deleted")))
    sel_providers = st.multiselect("Provider", all_providers)
    all_statuses = ["1 Live", "2 Ready to Go Live", "3 In Testing", "4 In Development", "5 Up Next", "6 Waiting"]
    sel_statuses = st.multiselect("Status", all_statuses)
    show_deleted = st.checkbox("Show recovered (deleted) connections")

    st.markdown("---")
    total_conns = len([c for c in connections.values() if not c.get("deleted")])
    st.markdown(f'<div style="font-size:0.65rem;color:var(--muted)">{total_conns} connections tracked</div>', unsafe_allow_html=True)

# ── Filter helper ──────────────────────────────────────────────────────────────
def filter_conns(conns):
    out = {}
    for k, c in conns.items():
        if c.get("deleted") and not show_deleted:
            continue
        if sel_providers and c.get("provider") not in sel_providers:
            continue
        if sel_statuses and c.get("status") not in sel_statuses:
            continue
        out[k] = c
    return out

filtered = filter_conns(connections)
active = {k: c for k, c in filtered.items() if STAGE_ORDER.get(c.get("status", ""), 99) in ACTIVE_STAGES}
in_progress = {k: c for k, c in active.items() if STAGE_ORDER.get(c.get("status", ""), 99) in {2, 3, 4, 5}}
completed = {k: c for k, c in filtered.items() if STAGE_ORDER.get(c.get("status", ""), 99) in {1, 2}}

# ── Main UI ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-title">EDI Tracker</div>
<div class="page-sub">Statistical prediction engine &nbsp;·&nbsp; {len(connections)} connections tracked</div>
""", unsafe_allow_html=True)

# Show any startup warnings from auto-load
if st.session_state.get("startup_errors"):
    with st.expander("⚠️ Sheet load issues", expanded=True):
        for e in st.session_state["startup_errors"]:
            st.error(e)
        st.caption("Fix column names in your sheet, then click Refresh in the sidebar.")
    del st.session_state["startup_errors"]
if st.session_state.get("startup_warnings"):
    with st.expander("Notes from last auto-load", expanded=False):
        for w in st.session_state["startup_warnings"]:
            st.warning(w)
    del st.session_state["startup_warnings"]

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Dashboard", "🔮 Predictions", "📈 Historical", "🗄️ All Connections", "📋 Import Log", "💾 Export & Restore"])

# ══ TAB 1 — DASHBOARD ══════════════════════════════════════════════════════════
with tab1:
    if not connections:
        st.markdown("""
        <div class="box-info">
            <b style="font-family:'Cabinet Grotesk',sans-serif;font-size:1rem">Get started</b><br><br>
            <span style="color:var(--muted)">1. Paste your Google Sheet URL in the sidebar → Refresh<br>
            2. Or upload a historical snapshot below</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        total_up_next  = sum(1 for c in connections.values() if c.get("status") == "5 Up Next")
        total_dev      = sum(1 for c in connections.values() if c.get("status") == "4 In Development")
        total_testing  = sum(1 for c in connections.values() if c.get("status") == "3 In Testing")
        total_ready    = sum(1 for c in connections.values() if c.get("status") == "2 Ready to Go Live")
        total_live     = sum(1 for c in connections.values() if c.get("status") == "1 Live")
        total_waiting  = sum(1 for c in connections.values() if c.get("status") == "6 Waiting")
        total_inactive = sum(1 for c in connections.values() if STAGE_ORDER.get(c.get("status",""), 99) in {8, 9})
        overall        = model.get("overall")
        avg_days       = f"{overall['median']:.0f}d" if overall else "—"

        # ── Stage flow bar ──
        last_refresh = data.get("last_sheet_refresh", "")
        refresh_str  = last_refresh[:16].replace("T"," ") if last_refresh else "never"
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px">' +
            f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">' +
            f'<span class="stage-pill" style="background:#111;color:#64748b;border-color:#21262d">5 · Up Next&nbsp;<b style="color:var(--text)">{total_up_next}</b></span>' +
            f'<span style="color:var(--muted);font-size:0.65rem">›</span>' +
            f'<span class="stage-pill" style="background:#120e00;color:#d97706;border-color:#2d1f00">4 · In Dev&nbsp;<b style="color:#f0883e">{total_dev}</b></span>' +
            f'<span style="color:var(--muted);font-size:0.65rem">›</span>' +
            f'<span class="stage-pill" style="background:#0d0a1a;color:#9333ea;border-color:#1f1345">3 · Testing&nbsp;<b style="color:#bc8cff">{total_testing}</b></span>' +
            f'<span style="color:var(--muted);font-size:0.65rem">›</span>' +
            f'<span class="stage-pill" style="background:#061220;color:#1d4ed8;border-color:#0f2a4a">2 · Ready&nbsp;<b style="color:#58a6ff">{total_ready}</b></span>' +
            f'<span style="color:var(--muted);font-size:0.65rem">›</span>' +
            f'<span class="stage-pill" style="background:#061410;color:#166534;border-color:#0d2b1a">1 · Live&nbsp;<b style="color:#3fb950">{total_live}</b></span>' +
            f'</div>' +
            f'<span class="refresh-badge">↺ {refresh_str}</span>' +
            f'</div>',
            unsafe_allow_html=True
        )

        # ── KPI row: one card per stage ──
        cols = st.columns(7)
        kpis = [
            (cols[0], str(total_up_next),  "#64748b", "5 · Up Next",          "queued"),
            (cols[1], str(total_dev),       "#f0883e", "4 · In Development",   "building"),
            (cols[2], str(total_testing),   "#bc8cff", "3 · In Testing",       "testing"),
            (cols[3], str(total_ready),     "#58a6ff", "2 · Ready to Go Live", "awaiting flip"),
            (cols[4], str(total_live),      "#3fb950", "1 · Live",             "complete"),
            (cols[5], str(total_waiting),   "#d97706", "6 · Waiting",          "stalled"),
            (cols[6], avg_days,             "#e8ff47", "Median Build",         "stage 5→2"),
        ]
        for col, val, color, label, sub in kpis:
            with col:
                st.markdown(
                    f'<div class="kpi-card">' +
                    f'<div class="kpi-num" style="color:{color}">{val}</div>' +
                    f'<div class="kpi-label">{label}</div>' +
                    f'<div class="kpi-sub">{sub}</div>' +
                    '</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<div class="sec-head">Connections by Stage</div>', unsafe_allow_html=True)

            stage_config = [
                ("2 Ready to Go Live", "2 · Ready to Go Live", "#58a6ff", "#061220"),
                ("3 In Testing",       "3 · In Testing",        "#bc8cff", "#0d0a1a"),
                ("4 In Development",   "4 · In Development",    "#f0883e", "#120e00"),
                ("5 Up Next",          "5 · Up Next",            "#64748b", "#111"),
            ]
            any_shown = False
            for stage_key, label, color, bg in stage_config:
                stage_conns = {k: c for k, c in in_progress.items() if c.get("status") == stage_key}
                if not stage_conns:
                    continue
                any_shown = True
                count = len(stage_conns)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:14px 0 8px">'
                    f'<span style="background:{bg};color:{color};border:1px solid rgba(100,100,100,0.2);'
                    f'border-radius:4px;padding:3px 10px;font-size:0.68rem;font-weight:600;'
                    f'letter-spacing:0.04em">{label}</span>'
                    f'<span style="color:var(--muted);font-size:0.65rem">{count} connection{"s" if count != 1 else ""}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                for key, conn in list(stage_conns.items())[:20]:
                    dur, start, _ = compute_duration(conn)
                    pred, basis, basis_name, pred_detail = predict(conn, model)
                    elapsed_str = ""
                    pct = 0
                    if start:
                        try:
                            elapsed_days = (datetime.now() - datetime.strptime(start, "%Y-%m-%d")).days
                            elapsed_str = f"{elapsed_days}d"
                            if pred:
                                pct = min(100, int(elapsed_days / pred["median"] * 100))
                        except: pass
                    pred_text    = f"{int(pred['p25'])}–{int(pred['p75'])}d est." if pred else "—"
                    provider_str = conn.get("provider", "") or ""
                    shipper_str  = conn.get("shipper") or ""
                    partner_str  = provider_str + (f" / {shipper_str}" if shipper_str else "")
                    bic          = conn.get("ball_in_court", "") or ""
                    bic_html     = f'<span style="color:#d97706;font-size:0.62rem;margin-left:6px;opacity:0.8">· {bic}</span>' if bic and bic.lower() not in ("","nan","toro") else ""
                    over = pct > 100
                    bar_color = "#ff7b72" if over else color
                    st.markdown(
                        f'<div class="conn-row">' +
                        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">' +
                        f'<div style="flex:1;min-width:0">' +
                        f'<div class="conn-name">{conn["customer"]}{bic_html}</div>' +
                        f'<div class="conn-partner">{partner_str}</div>' +
                        f'</div>' +
                        f'<div style="margin-left:14px;text-align:right;flex-shrink:0">' +
                        f'<div class="conn-meta">{elapsed_str} elapsed</div>' +
                        f'<div class="conn-pred" style="color:{color}">{pred_text}</div>' +
                        f'</div></div>' +
                        f'<div class="prog-bg"><div class="prog-fill" style="width:{min(pct,100)}%;background:{bar_color}"></div></div>' +
                        f'</div>',
                        unsafe_allow_html=True
                    )

            if not any_shown:
                st.markdown('<div style="color:var(--muted);font-size:0.8rem;padding:20px 0">No connections currently in the build pipeline.</div>', unsafe_allow_html=True)

        with col_right:
            # Stalled
            st.markdown('<div class="sec-head">6 · Waiting / Stalled</div>', unsafe_allow_html=True)
            waiting_conns = {k: c for k, c in filtered.items() if c.get("status") == "6 Waiting"}
            if waiting_conns:
                for key, conn in list(waiting_conns.items())[:10]:
                    lu = conn.get("last_update","")
                    days_w = ""
                    if lu:
                        try: days_w = f"{(datetime.now() - datetime.strptime(lu[:10], '%Y-%m-%d')).days}d"
                        except: pass
                    bic = conn.get("ball_in_court","") or ""
                    bic_line = f'<div style="color:#d97706;font-size:0.65rem;margin-top:3px">waiting on: {bic}</div>' if bic and bic.lower() not in ("","nan") else ""
                    days_line = f'<div style="color:var(--muted);font-size:0.65rem">{days_w} since update</div>' if days_w else ""
                    provider_str = conn.get("provider","") or ""
                    shipper_str  = conn.get("shipper") or ""
                    partner_str  = provider_str + (f" / {shipper_str}" if shipper_str else "")
                    st.markdown(
                        f'<div class="box-warn">' +
                        f'<div style="font-weight:600;font-size:0.85rem;color:var(--text)">{conn["customer"]}</div>' +
                        f'<div style="color:var(--muted);font-size:0.68rem">{partner_str}</div>' +
                        f'{bic_line}{days_line}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown('<div style="color:var(--muted);font-size:0.78rem;padding:8px 0">None stalled.</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec-head">Pipeline</div>', unsafe_allow_html=True)
            pipeline = [
                ("2 · Ready",       total_ready,   "#58a6ff"),
                ("3 · Testing",     total_testing, "#bc8cff"),
                ("4 · Development", total_dev,     "#f0883e"),
                ("5 · Up Next",     total_up_next, "#4b5563"),
            ]
            mx = max((p[1] for p in pipeline), default=1) or 1
            for lbl, cnt, clr in pipeline:
                pct_b = int(cnt / mx * 100)
                st.markdown(
                    f'<div style="margin-bottom:10px">' +
                    f'<div style="display:flex;justify-content:space-between;font-size:0.7rem;margin-bottom:4px">' +
                    f'<span style="color:var(--muted)">{lbl}</span>' +
                    f'<span style="color:{clr};font-weight:600">{cnt}</span></div>' +
                    f'<div class="prog-bg" style="height:4px">' +
                    f'<div class="prog-fill" style="height:4px;background:{clr};width:{pct_b}%;opacity:0.8"></div>' +
                    f'</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec-head">Summary</div>', unsafe_allow_html=True)
            total_tracked = len([c for c in connections.values() if not c.get("deleted")])
            rows_data = [
                ("Total tracked",    total_tracked, "var(--text)"),
                ("Live",             total_live,    "#3fb950"),
                ("In build",         total_up_next + total_dev + total_testing + total_ready, "#58a6ff"),
                ("Stalled",          total_waiting, "#d97706"),
                ("Inactive",         total_inactive,"var(--muted)"),
            ]
            for lbl, val, clr in rows_data:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:5px 0;' +
                    f'border-bottom:1px solid var(--border);font-size:0.75rem">' +
                    f'<span style="color:var(--muted)">{lbl}</span>' +
                    f'<span style="color:{clr};font-weight:600">{val}</span></div>',
                    unsafe_allow_html=True
                )


# ══ TAB 2 — PREDICTIONS ════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Prediction Engine — Up Next → Ready to Go Live</div>', unsafe_allow_html=True)

    if not model.get("overall"):
        st.info("Not enough completed connection history yet. Upload older snapshots to train the model — the more historical files you add, the better the predictions.")
    else:
        ov = model["overall"]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Median Build", f"{ov['median']:.0f} days")
        with c2: st.metric("Best Case (P25)", f"{ov['p25']:.0f} days")
        with c3: st.metric("Likely Max (P75)", f"{ov['p75']:.0f} days")
        with c4: st.metric("Training Sample", f"{ov['n']} connections")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Active Connection Predictions</div>', unsafe_allow_html=True)

        rows = []
        for key, conn in in_progress.items():
            _, start, _ = compute_duration(conn)
            pred, basis, basis_name, pred_detail = predict(conn, model)
            if not start or not pred:
                continue
            try:
                elapsed = (datetime.now() - datetime.strptime(start, "%Y-%m-%d")).days
            except:
                elapsed = 0
            remaining = max(0, pred["median"] - elapsed)
            est_lo = (datetime.now() + timedelta(days=max(0, pred["p25"] - elapsed))).strftime("%b %d")
            est_hi = (datetime.now() + timedelta(days=max(0, pred["p75"] - elapsed))).strftime("%b %d")
            conf, _ = confidence_label(basis, pred["n"])
            prov_sig = f"{int(pred_detail['provider']['median'])}d ({int(pred_detail['provider']['n'])} jobs)" if pred_detail.get("provider") else "—"
            ship_sig = f"{int(pred_detail['shipper']['median'])}d ({int(pred_detail['shipper']['n'])} jobs)" if pred_detail.get("shipper") else "—"
            rows.append({
                "Customer": conn["customer"],
                "Vendor": conn["vendor"],
                "Status": conn.get("status", ""),
                "Elapsed (d)": elapsed,
                "Est. Total (d)": f"{int(pred['p25'])}–{int(pred['p75'])}",
                "Est. Ready by": f"{est_lo} – {est_hi}",
                "Provider Signal": prov_sig,
                "Shipper Signal": ship_sig,
                "Confidence": conf,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No in-progress connections with start dates found.")

        st.markdown('''
        <div style="font-size:0.72rem;color:var(--muted);margin-top:8px;padding:10px 14px;background:var(--bg2);border-radius:8px;border:1px solid var(--border)">
        <b>How predictions work:</b> Provider and Shipper are tracked independently.
        When both have history they are <b>blended weighted by sample size</b> — more completed jobs = more influence.
        The Provider Signal and Shipper Signal columns show each one's individual contribution.
        </div>
        ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-header">By Provider — Historical Build Times</div>', unsafe_allow_html=True)
            prov_rows = []
            for p_name, s in sorted(model["by_provider"].items(), key=lambda x: -x[1]["n"]):
                prov_rows.append({"Provider": p_name, "Median (d)": f"{s['median']:.0f}", "Best Case": f"{s['p25']:.0f}d", "Likely Max": f"{s['p75']:.0f}d", "Completed Jobs": s["n"]})
            if prov_rows:
                st.dataframe(pd.DataFrame(prov_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No completed connections yet.")

        with col_b:
            st.markdown('<div class="section-header">By Shipper — Historical Build Times</div>', unsafe_allow_html=True)
            ship_rows = []
            for s_name, v in sorted(model["by_shipper"].items(), key=lambda x: -x[1]["n"]):
                ship_rows.append({"Shipper": s_name, "Median (d)": f"{v['median']:.0f}", "Best Case": f"{v['p25']:.0f}d", "Likely Max": f"{v['p75']:.0f}d", "Completed Jobs": v["n"]})
            if ship_rows:
                st.dataframe(pd.DataFrame(ship_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No completed connections with a shipper yet.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Manual Prediction Lookup</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:var(--muted);margin-bottom:12px">Select provider, shipper, or both — signals are blended automatically based on available history.</div>', unsafe_allow_html=True)
        col_x, col_y = st.columns(2)
        with col_x:
            lp = st.selectbox("Provider", ["(any)"] + sorted(all_providers))
        with col_y:
            all_shippers = sorted(set(c.get("shipper") or "" for c in connections.values() if c.get("shipper")))
            ls = st.selectbox("Shipper", ["(any)"] + all_shippers)
        if lp != "(any)" or ls != "(any)":
            mock = {"provider": lp if lp != "(any)" else "Unknown", "shipper": ls if ls != "(any)" else None}
            pred, basis, basis_name, pred_detail = predict(mock, model)
            if pred:
                conf, conf_cls = confidence_label(basis, pred["n"])
                p_detail = f"{pred_detail['provider']['median']:.0f}d median · {int(pred_detail['provider']['n'])} jobs" if pred_detail.get("provider") else "no data yet"
                s_detail = f"{pred_detail['shipper']['median']:.0f}d median · {int(pred_detail['shipper']['n'])} jobs" if pred_detail.get("shipper") else "no data yet"
                st.markdown(f'''<div class="metric-card" style="margin-top:12px">
                    <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap">
                        <div><div class="metric-val">{pred['median']:.0f}d</div><div class="metric-label">Blended estimate</div></div>
                        <div><div class="metric-val" style="color:#4ade80">{pred['p25']:.0f}d</div><div class="metric-label">Best case</div></div>
                        <div><div class="metric-val" style="color:#f59e0b">{pred['p75']:.0f}d</div><div class="metric-label">Likely max</div></div>
                        <div><div class="metric-val {conf_cls}" style="font-size:1.2rem">{conf}</div><div class="metric-label">Confidence</div></div>
                    </div>
                    <div style="margin-top:14px;display:flex;gap:32px;font-size:0.74rem;flex-wrap:wrap">
                        <div><span style="color:var(--muted)">📦 Provider ({lp if lp != "(any)" else "—"}):</span><br>
                             <span style="color:var(--accent)">{p_detail}</span></div>
                        <div><span style="color:var(--muted)">🏭 Shipper ({ls if ls != "(any)" else "—"}):</span><br>
                             <span style="color:var(--accent2)">{s_detail}</span></div>
                    </div>
                    <div style="margin-top:8px;font-size:0.68rem;color:var(--muted)">Method: {basis_name}</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.warning("No historical data for this combination yet — complete more connections to build signal.")

# ══ TAB 3 — HISTORICAL ═════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Completed Connections</div>', unsafe_allow_html=True)
    hist_rows = []
    for conn in connections.values():
        if STAGE_ORDER.get(conn.get("status", ""), 99) not in {1, 2}:
            continue
        dur, start, end = compute_duration(conn)
        if not dur:
            continue
        hist_rows.append({
            "Customer": conn["customer"], "Vendor": conn["vendor"],
            "Provider": conn["provider"], "Shipper": conn["shipper"],
            "Started": start, "Completed": end or "~",
            "Days": dur, "Recovered": "✓" if conn.get("deleted") else "",
        })
    if hist_rows:
        hdf = pd.DataFrame(hist_rows).sort_values("Days")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Fastest", f"{hdf['Days'].min()} days")
        with c2: st.metric("Median", f"{hdf['Days'].median():.0f} days")
        with c3: st.metric("Slowest", f"{hdf['Days'].max()} days")
        st.markdown("<br>", unsafe_allow_html=True)
        st.bar_chart(hdf.set_index("Customer")[["Days"]], height=220)
        st.dataframe(hdf, use_container_width=True, hide_index=True)
    else:
        st.info("No completed connections with stage history yet. Upload multiple snapshots over time to build history.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Model Health by Provider</div>', unsafe_allow_html=True)
    health = [{"Provider": p, "Completed": s["n"],
               "Confidence": "HIGH" if s["n"] >= 5 else "MED" if s["n"] >= 2 else "LOW",
               "Median (d)": f"{s['median']:.0f}"}
              for p, s in model.get("by_provider", {}).items()]
    if health:
        st.dataframe(pd.DataFrame(health).sort_values("Completed", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No provider data yet.")

# ══ TAB 4 — ALL CONNECTIONS ════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">All Tracked Connections</div>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Customer or vendor name...")
    rows = []
    for conn in filtered.values():
        if search and search.lower() not in conn["customer"].lower() and search.lower() not in conn.get("vendor", "").lower():
            continue
        dur, start, _ = compute_duration(conn)
        pred, basis, basis_name, pred_detail = predict(conn, model)
        rows.append({
            "Customer": conn["customer"], "Vendor": conn["vendor"],
            "Provider": conn["provider"], "Shipper": conn["shipper"],
            "Status": conn.get("status", "—"),
            "Last Update": conn.get("last_update", "—"),
            "Days (completed)": dur if dur else "—",
            "Prediction": f"{int(pred['p25'])}–{int(pred['p75'])}d" if pred else "—",
            "Recovered": "✓" if conn.get("deleted") else "",
            "Snapshots": len(conn.get("snapshots", {})),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown(f'<div style="font-size:0.7rem;color:var(--muted);margin-top:8px">{len(rows)} shown</div>', unsafe_allow_html=True)
    else:
        st.info("No connections match your filters.")

# ══ TAB 5 — IMPORT LOG ════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Import History</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.78rem;color:var(--muted);margin-bottom:16px">All snapshots loaded into the system, sorted by snapshot date. Use this to verify out-of-order uploads landed correctly.</div>', unsafe_allow_html=True)

    import_log = data.get("import_log", [])
    if import_log:
        log_rows = []
        for entry in sorted(import_log, key=lambda x: x.get("label", ""), reverse=True):
            log_rows.append({
                "Snapshot Date": entry.get("label", "—"),
                "Source": entry.get("source", "—"),
                "Date Detected From": entry.get("date_detected_from", "—"),
                "Imported At": entry.get("imported_at", "—")[:16].replace("T", " "),
                "New": entry.get("new", 0),
                "Updated": entry.get("updated", 0),
                "Recovered": entry.get("recovered", 0),
                "Total Rows": entry.get("total", 0),
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Show timeline of snapshots we have
        snap_dates = sorted(set(e.get("label") for e in import_log if e.get("label")))
        if snap_dates:
            st.markdown('<div class="section-header">Snapshot Timeline</div>', unsafe_allow_html=True)
            for d in snap_dates:
                st.markdown(f'<div style="font-size:0.78rem;padding:4px 0;border-bottom:1px solid var(--border)">📅 {d}</div>', unsafe_allow_html=True)

        # Reset button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Reset All Data", type="secondary"):
            if st.session_state.get("confirm_reset"):
                data = {"connections": {}, "import_log": [], "sheet_url": sheet_url, "last_sheet_refresh": None}
                save_data(data)
                st.session_state.data = data
                st.session_state.confirm_reset = False
                st.success("All data cleared.")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("Click Reset again to confirm — this will delete all tracked connections and history.")
    else:
        st.info("No imports yet. Connect your Google Sheet or upload a CSV snapshot to get started.")

# ══ TAB 6 — EXPORT & RESTORE ══════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Prediction Model — Export & Restore</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.82rem;color:var(--muted);margin-bottom:20px;padding:12px 16px;background:var(--bg2);border-radius:8px;border:1px solid var(--border)">
    The <b>Prediction Export</b> saves what the model has actually learned — completed build times per provider and shipper.
    This is what drives predictions. Re-upload it anytime to restore full predictive power instantly,
    without re-importing all your historical snapshots.<br><br>
    The <b>Model Summary</b> is a readable sheet showing median build times per provider and shipper — useful for reviewing what the model knows.
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ──
    completed_with_dur = sum(1 for c in connections.values() if compute_duration(c)[0])
    providers_with_data = len(model.get("by_provider", {}))
    shippers_with_data  = len(model.get("by_shipper", {}))
    combined_with_data  = len(model.get("by_combined", {}))

    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#4ade80">{completed_with_dur}</div><div class="metric-label">Completed Connections</div><div style="font-size:0.6rem;color:var(--muted);margin-top:5px">with measured build times</div></div>', unsafe_allow_html=True)
    with kc2:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#00e5ff">{providers_with_data}</div><div class="metric-label">Providers Learned</div><div style="font-size:0.6rem;color:var(--muted);margin-top:5px">have historical signal</div></div>', unsafe_allow_html=True)
    with kc3:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#a78bfa">{shippers_with_data}</div><div class="metric-label">Shippers Learned</div><div style="font-size:0.6rem;color:var(--muted);margin-top:5px">have historical signal</div></div>', unsafe_allow_html=True)
    with kc4:
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#fbbf24">{combined_with_data}</div><div class="metric-label">Combos Learned</div><div style="font-size:0.6rem;color:var(--muted);margin-top:5px">provider + shipper pairs</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_exp, col_rest = st.columns(2)

    with col_exp:
        st.markdown('<div class="section-header">📤 Export</div>', unsafe_allow_html=True)
        if connections:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            export_df      = build_export_df(connections)
            summary_df     = build_model_summary_df(model)
            pred_csv       = export_df.to_csv(index=False).encode("utf-8")
            summary_csv    = summary_df.to_csv(index=False).encode("utf-8") if not summary_df.empty else b""

            st.markdown(f'''<div class="success-box">
                ✅ Ready to export<br>
                <span style="color:var(--muted);font-size:0.72rem">
                {len(export_df)} connections · {completed_with_dur} with build time data ·
                {providers_with_data} providers · {shippers_with_data} shippers
                </span>
            </div>''', unsafe_allow_html=True)

            st.download_button(
                label="⬇️ Download Prediction Data (restore this to rebuild the model)",
                data=pred_csv,
                file_name=f"edi_prediction_data_{timestamp}.csv",
                mime="text/csv",
                help="This is the file to save and re-upload to restore predictive power. Store it in Google Drive alongside your EDI sheet.",
            )

            if summary_csv:
                st.download_button(
                    label="📋 Download Model Summary (readable — what the model knows)",
                    data=summary_csv,
                    file_name=f"edi_model_summary_{timestamp}.csv",
                    mime="text/csv",
                    help="Human-readable — shows median build time per provider and shipper. Good for reviewing what the model has learned.",
                )

            st.markdown('''<div style="font-size:0.72rem;color:var(--muted);margin-top:12px;line-height:1.6">
            <b>Prediction Data</b> — save this and re-upload it to restore the model.<br>
            <b>Model Summary</b> — a readable sheet of what the model has learned. Useful for reviewing or sharing with your team.<br><br>
            <b>Recommended:</b> store the Prediction Data in Google Drive next to your EDI sheet and re-export it whenever you complete new connections.
            </div>''', unsafe_allow_html=True)
        else:
            st.info("No data to export yet. Load your Google Sheet or upload a historical snapshot first.")

    with col_rest:
        st.markdown('<div class="section-header">📥 Restore</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:var(--muted);margin-bottom:10px">Upload a previously exported Prediction Data CSV to restore the model instantly.</div>', unsafe_allow_html=True)

        restore_file = st.file_uploader(
            "Upload Prediction Data CSV",
            type=["csv"],
            key="restore_uploader",
            help="Only upload files downloaded from the Export button above — not raw EDI tracking sheets.",
        )

        if restore_file:
            try:
                restore_df = pd.read_csv(restore_file)
                # Check version
                version = str(restore_df.get("_export_version", pd.Series(["?"])).iloc[0]) if "_export_version" in restore_df.columns else "?"
                n_with_dur = restore_df["duration_days"].notna().sum() if "duration_days" in restore_df.columns else 0
                st.markdown(
                    f'<div style="font-size:0.72rem;color:var(--accent);margin-bottom:8px">'
                    f'📂 {len(restore_df)} connections found · {n_with_dur} with build time data · export version {version}</div>',
                    unsafe_allow_html=True
                )

                if st.button("🔁 Restore Prediction Model"):
                    data, restored_c, updated_c, rest_warns, rest_errs = restore_from_export(restore_df, data)
                    for e in rest_errs:
                        st.error(e)
                    for w in rest_warns:
                        st.warning(w)
                    if not rest_errs:
                        save_data(data)
                        st.session_state.data = data
                        connections = data["connections"]
                        model = build_model(connections)
                        new_prov = len(model.get("by_provider", {}))
                        new_ship = len(model.get("by_shipper", {}))
                        st.success(
                            f"✅ Restored — {restored_c} new connections added, {updated_c} updated. "
                            f"Model now has {new_prov} providers and {new_ship} shippers with signal."
                        )
                        st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")
                st.info("Make sure you are uploading a file from the Export button above, not your raw EDI tracking sheet.")

    # ── Model summary table ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">What the Model Currently Knows</div>', unsafe_allow_html=True)
    if model.get("by_provider") or model.get("by_shipper"):
        summary_df = build_model_summary_df(model)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.markdown('<div style="font-size:0.68rem;color:var(--muted);margin-top:6px">The model blends Provider and Shipper signals weighted by completed job count. More jobs = more influence on predictions.</div>', unsafe_allow_html=True)
    else:
        st.info("No completed connections with build time data yet. Upload historical snapshots or restore a prediction export to build signal.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Recommended Workflow</div>', unsafe_allow_html=True)
    st.markdown('''<div style="font-size:0.78rem;color:var(--muted);line-height:1.9">
    1. <b>Upload historical snapshots</b> (sidebar) to build up completed connection data<br>
    2. <b>Export Prediction Data</b> after each batch — this is your model backup<br>
    3. <b>Store it in Google Drive</b> next to your EDI sheet<br>
    4. <b>If you ever redeploy</b>: restore the Prediction Data first, then refresh the Google Sheet — done in 30 seconds<br>
    5. <b>Re-export periodically</b> as more connections complete and the model gets smarter
    </div>''', unsafe_allow_html=True)
