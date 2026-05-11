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

st.set_page_config(
    page_title="EDI Connection Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg: #0a0e1a;
    --bg2: #111827;
    --bg3: #1a2235;
    --accent: #00e5ff;
    --accent2: #7c3aed;
    --accent3: #10b981;
    --warn: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
    --border: #1e2d40;
}
html, body, [class*="css"] { background-color: var(--bg) !important; color: var(--text) !important; font-family: 'DM Mono', monospace !important; }
.stApp { background-color: var(--bg) !important; }
h1,h2,h3 { font-family: 'Syne', sans-serif !important; letter-spacing: -0.02em; }

.metric-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; position: relative; overflow: hidden; }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.metric-val { font-size: 2.2rem; font-weight: 800; font-family: 'Syne', sans-serif; color: var(--accent); }
.metric-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; margin-top: 4px; }

.status-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 500; letter-spacing: 0.05em; }
.s1 { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.s2 { background: #0c4a6e; color: #38bdf8; border: 1px solid #0369a1; }
.s3 { background: #1e1b4b; color: #a78bfa; border: 1px solid #4c1d95; }
.s4 { background: #1c1917; color: #fbbf24; border: 1px solid #92400e; }
.s5 { background: #1a1a2e; color: #94a3b8; border: 1px solid #334155; }
.s6 { background: #2d1b00; color: #fb923c; border: 1px solid #9a3412; }
.s9 { background: #1a0f0f; color: #f87171; border: 1px solid #7f1d1d; }

.connection-row { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; margin-bottom: 8px; }
.connection-row:hover { border-color: var(--accent); }

.prediction-bar-bg { background: var(--bg3); border-radius: 4px; height: 8px; margin-top: 6px; overflow: hidden; }
.prediction-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }

.section-header { font-family: 'Syne', sans-serif; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.2em; color: var(--muted); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.alert-box { background: #1a1200; border: 1px solid var(--warn); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; font-size: 0.82rem; }
.info-box { background: #0c1a2e; border: 1px solid var(--accent); border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; font-size: 0.82rem; }
.success-box { background: #052e16; border: 1px solid #166534; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; font-size: 0.82rem; color: #4ade80; }

.stButton > button { background: linear-gradient(135deg, var(--accent2), #6d28d9) !important; color: white !important; border: none !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 0.8rem !important; padding: 8px 20px !important; }
.stButton > button:hover { opacity: 0.85 !important; }

section[data-testid="stSidebar"] { background: var(--bg2) !important; border-right: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--bg2) !important; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-family: 'DM Mono', monospace !important; font-size: 0.78rem !important; }
.stTabs [aria-selected="true"] { background: var(--bg3) !important; color: var(--accent) !important; border-radius: 6px !important; }

.logo-text { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800; color: var(--accent); letter-spacing: -0.02em; }
.logo-sub { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.15em; }
.confidence-high { color: #4ade80; }
.confidence-med { color: #fbbf24; }
.confidence-low { color: #f87171; }

div[data-testid="metric-container"] { background: var(--bg2) !important; padding: 16px !important; border-radius: 10px !important; border: 1px solid var(--border) !important; }
thead tr th { background: var(--bg3) !important; color: var(--muted) !important; font-size: 0.7rem !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
tbody tr td { background: var(--bg2) !important; color: var(--text) !important; font-size: 0.8rem !important; }
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
    if not raw or (isinstance(raw, float) and np.isnan(raw)):
        return "Unknown", "Unknown"
    s = str(raw).strip()
    parts = re.split(r'\s*/\s*|\s+-\s+', s, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return s, s

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

# ── Core ingestion ─────────────────────────────────────────────────────────────
def ingest_dataframe(df, snapshot_label, existing_data, mark_missing_as_deleted=False):
    """
    Parse df and merge into existing_data.
    snapshot_label: YYYY-MM-DD string representing when this snapshot was taken.
    mark_missing_as_deleted: if True, connections not in this df get flagged deleted.
    """
    connections = existing_data.get("connections", {})
    new_count = updated_count = recovered_count = 0

    snap_cols = extract_snapshot_cols(df.columns)
    keys_in_this_upload = set()

    # Strip completely blank rows and find correct column names flexibly
    customer_col = next((c for c in df.columns if str(c).strip().lower() == "customer"), "Customer")
    vendor_col = next((c for c in df.columns if "vendor" in str(c).lower() and "edi" in str(c).lower()), 
                      next((c for c in df.columns if "vendor" in str(c).lower()), "Vendor EDI Provider Shipper"))
    status_col = next((c for c in df.columns if "edi connection status" in str(c).lower()), 
                      next((c for c in df.columns if "status" in str(c).lower() and "latest" not in str(c).lower()), "EDI Connection Status"))
    update_col = next((c for c in df.columns if "latest status update" in str(c).lower()), "Latest Status Update")
    bic_col = next((c for c in df.columns if "ball in court" in str(c).lower()), "Ball In Court")

    # Drop rows where both customer and status are blank
    df = df[df[customer_col].notna() | df[status_col].notna()]
    df = df[df[customer_col].notna()]
    df = df[df[customer_col].astype(str).str.strip() != ""]
    df = df[df[customer_col].astype(str).str.strip() != "nan"]

    for _, row in df.iterrows():
        customer = row.get(customer_col, "")
        vendor = row.get(vendor_col, "")
        if not customer or (isinstance(customer, float) and np.isnan(customer)):
            continue
        if str(customer).strip() == "" or str(customer).strip().lower() == "nan":
            continue

        key = connection_key(customer, vendor)
        keys_in_this_upload.add(key)

        provider, shipper = parse_provider_shipper(vendor)
        current_status = normalize_status(row.get(status_col, ""))
        last_update = parse_excel_date(row.get(update_col))
        ball_in_court = str(row.get(bic_col, "")).strip()

        is_new = key not in connections
        if is_new:
            new_count += 1
            connections[key] = {
                "customer": str(customer).strip(),
                "vendor": str(vendor).strip() if not (isinstance(vendor, float) and np.isnan(vendor)) else "",
                "provider": provider,
                "shipper": shipper,
                "snapshots": {},        # date_str → status
                "status": current_status,
                "last_update": last_update,
                "ball_in_court": ball_in_court,
                "deleted": False,
                "first_seen": snapshot_label,
            }
        else:
            updated_count += 1
            if connections[key].get("deleted"):
                recovered_count += 1
                connections[key]["deleted"] = False

        conn = connections[key]

        # Always update current status and last_update if this snapshot is newer
        existing_snaps = conn.get("snapshots", {})
        latest_known = max(existing_snaps.keys()) if existing_snaps else "0000-00-00"

        if snapshot_label >= latest_known:
            if current_status:
                conn["status"] = current_status
            if last_update:
                # Only overwrite last_update if this snapshot's update is newer
                existing_lu = conn.get("last_update") or "0000-00-00"
                if last_update > existing_lu:
                    conn["last_update"] = last_update
            conn["ball_in_court"] = ball_in_court

        # Record current status under this snapshot date
        if current_status:
            conn["snapshots"][snapshot_label] = current_status

        # Record all weekly snapshot column statuses
        for col, date_str in snap_cols:
            val = row.get(col, "")
            if val and not (isinstance(val, float) and np.isnan(val)):
                s = normalize_status(str(val))
                if s and date_str not in conn["snapshots"]:
                    conn["snapshots"][date_str] = s

    # Mark connections missing from this upload as deleted (only for live sheet refreshes)
    if mark_missing_as_deleted:
        for key, conn in connections.items():
            if key not in keys_in_this_upload and not conn.get("deleted"):
                conn["deleted"] = True

    existing_data["connections"] = connections
    return existing_data, new_count, updated_count, recovered_count, len(keys_in_this_upload)

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
            s = conn.get("shipper", "Unknown")
            by_provider[p].append(dur)
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

def predict(conn, model):
    p = conn.get("provider", "Unknown")
    s = conn.get("shipper", "Unknown")
    combined = f"{p} / {s}"
    if combined in model.get("by_combined", {}) and model["by_combined"][combined]["n"] >= 2:
        return model["by_combined"][combined], "combined", combined
    if p in model.get("by_provider", {}) and model["by_provider"][p]["n"] >= 1:
        return model["by_provider"][p], "provider", p
    if s in model.get("by_shipper", {}) and model["by_shipper"][s]["n"] >= 1:
        return model["by_shipper"][s], "shipper", s
    if model.get("overall"):
        return model["overall"], "overall", "historical average"
    return None, None, None

def confidence_label(basis, n):
    if basis == "combined" and n >= 3:
        return "HIGH", "confidence-high"
    if basis in ("combined", "provider") and n >= 2:
        return "MED", "confidence-med"
    return "LOW", "confidence-low"

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
                st.session_state.data, _, _, _, _ = ingest_dataframe(
                    _df, _snap_date, st.session_state.data, mark_missing_as_deleted=True
                )
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
    st.markdown('<div class="logo-text">⚡ EDI Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Connection Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

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
                    data, new_c, upd_c, rec_c, total = ingest_dataframe(
                        df, snap_date, data, mark_missing_as_deleted=True
                    )
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
                        st.warning(f"🔁 {rec_c} deleted connections recovered")
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

    if uploaded:
        # Auto-detect date from file first
        try:
            if uploaded.name.endswith(".csv"):
                preview_df = pd.read_csv(uploaded)
                uploaded.seek(0)
            else:
                xl = pd.ExcelFile(uploaded)
                sheet_name = next(
                    (s for s in xl.sheet_names if "connection" in s.lower() or "status" in s.lower()),
                    xl.sheet_names[0]
                )
                preview_df = pd.read_excel(uploaded, sheet_name=sheet_name)
                uploaded.seek(0)

            auto_date, auto_source = auto_detect_snapshot_date(preview_df)
            st.markdown(f'<div style="font-size:0.7rem;color:var(--accent);margin-bottom:6px">📅 Auto-detected: <b>{auto_date}</b><br><span style="color:var(--muted)">from {auto_source}</span></div>', unsafe_allow_html=True)
        except:
            auto_date = datetime.today().strftime("%Y-%m-%d")
            auto_source = "today (auto-detect failed)"

        override = st.checkbox("Override detected date", value=False)
        if override:
            snap_date_input = st.date_input("Snapshot date", value=datetime.strptime(auto_date, "%Y-%m-%d"))
            snap_label = snap_date_input.strftime("%Y-%m-%d")
        else:
            snap_label = auto_date

        if st.button("⬆️ Import Snapshot"):
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded, sheet_name=sheet_name)

                data, new_c, upd_c, rec_c, total = ingest_dataframe(df, snap_label, data)
                log_entry = {
                    "label": snap_label,
                    "source": uploaded.name,
                    "date_detected_from": auto_source,
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

                st.success(f"✅ Imported {total} rows · {snap_label}")
                if new_c: st.info(f"🆕 {new_c} new")
                if rec_c: st.warning(f"🔁 {rec_c} recovered")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

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
st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;margin-bottom:4px">EDI Connection Tracker</h1>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:0.75rem;color:var(--muted);margin-bottom:24px">Statistical prediction engine · {len(connections)} connections tracked</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🔮 Predictions", "📈 Historical", "🗄️ All Connections", "📋 Import Log"])

# ══ TAB 1 — DASHBOARD ══════════════════════════════════════════════════════════
with tab1:
    if not connections:
        st.markdown("""
        <div class="info-box">
            <b>👋 Welcome to EDI Connection Tracker</b><br><br>
            To get started:<br>
            1. Paste your Google Sheet URL in the sidebar and click <b>Refresh</b><br>
            2. Or upload a historical Excel/CSV snapshot using the uploader below the URL box<br><br>
            Upload older snapshots in any order — dates are auto-detected from the file.
        </div>
        """, unsafe_allow_html=True)
    else:
        # KPIs
        total_live = sum(1 for c in connections.values() if c.get("status") == "1 Live")
        total_ready = sum(1 for c in connections.values() if c.get("status") == "2 Ready to Go Live")
        total_testing = sum(1 for c in connections.values() if c.get("status") == "3 In Testing")
        total_dev = sum(1 for c in connections.values() if c.get("status") == "4 In Development")
        overall = model.get("overall")
        avg_days = f"{overall['median']:.0f}d" if overall else "N/A"

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(f'<div class="metric-card"><div class="metric-val">{len(active)}</div><div class="metric-label">Active</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#4ade80">{total_live}</div><div class="metric-label">Live</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#a78bfa">{total_testing}</div><div class="metric-label">In Testing</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#fbbf24">{total_dev}</div><div class="metric-label">In Development</div></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#00e5ff">{avg_days}</div><div class="metric-label">Median Build</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<div class="section-header">In-Progress Connections</div>', unsafe_allow_html=True)
            if not in_progress:
                st.info("No in-progress connections. Upload a snapshot to populate.")
            else:
                for stage in ["5 Up Next", "4 In Development", "3 In Testing", "2 Ready to Go Live"]:
                    stage_conns = {k: c for k, c in in_progress.items() if c.get("status") == stage}
                    if not stage_conns:
                        continue
                    sn = STAGE_ORDER.get(stage, 9)
                    st.markdown(f'<span class="status-badge s{min(sn,6)}">{stage}</span><div style="height:6px"></div>', unsafe_allow_html=True)
                    for key, conn in list(stage_conns.items())[:20]:
                        dur, start, _ = compute_duration(conn)
                        pred, basis, _ = predict(conn, model)
                        elapsed = days_in_progress = ""
                        pct = 0
                        if start:
                            try:
                                elapsed_days = (datetime.now() - datetime.strptime(start, "%Y-%m-%d")).days
                                days_in_progress = f"{elapsed_days}d elapsed"
                                if pred:
                                    pct = min(100, int(elapsed_days / pred["median"] * 100))
                            except: pass
                        pred_text = f"Est. {int(pred['p25'])}–{int(pred['p75'])}d" if pred else "Insufficient data"
                        st.markdown(f"""
                        <div class="connection-row">
                            <div style="display:flex;justify-content:space-between">
                                <div>
                                    <div style="font-weight:500;font-size:0.88rem">{conn['customer']}</div>
                                    <div style="color:var(--muted);font-size:0.72rem;margin-top:2px">{conn['vendor']}</div>
                                </div>
                                <div style="text-align:right">
                                    <div style="font-size:0.72rem;color:var(--muted)">{days_in_progress}</div>
                                    <div style="font-size:0.72rem;color:var(--accent)">{pred_text}</div>
                                </div>
                            </div>
                            <div class="prediction-bar-bg"><div class="prediction-bar-fill" style="width:{pct}%"></div></div>
                        </div>
                        """, unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="section-header">Stalled / Waiting</div>', unsafe_allow_html=True)
            waiting = {k: c for k, c in filtered.items() if c.get("status") == "6 Waiting"}
            if waiting:
                for key, conn in list(waiting.items())[:10]:
                    lu = conn.get("last_update", "")
                    days_w = ""
                    if lu:
                        try: days_w = f"{(datetime.now() - datetime.strptime(lu[:10], '%Y-%m-%d')).days}d"
                        except: pass
                    st.markdown(f"""<div class="alert-box">
                        <div style="font-weight:500">{conn['customer']}</div>
                        <div style="color:var(--muted);font-size:0.7rem">{conn['vendor']}</div>
                        {f'<div style="color:var(--warn);font-size:0.7rem;margin-top:4px">⏱ Waiting {days_w}</div>' if days_w else ''}
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:var(--muted);font-size:0.8rem">No connections in waiting status.</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Pipeline</div>', unsafe_allow_html=True)
            for stage, count in [("2 Ready to Go Live", total_ready), ("3 In Testing", total_testing), ("4 In Development", total_dev),
                                  ("5 Up Next", sum(1 for c in connections.values() if c.get("status") == "5 Up Next"))]:
                pct = min(100, count * 15)
                st.markdown(f"""<div style="margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:4px">
                        <span style="color:var(--muted)">{stage}</span><span>{count}</span>
                    </div>
                    <div class="prediction-bar-bg"><div class="prediction-bar-fill" style="width:{pct}%"></div></div>
                </div>""", unsafe_allow_html=True)

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
            pred, basis, basis_name = predict(conn, model)
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
            rows.append({
                "Customer": conn["customer"],
                "Vendor": conn["vendor"],
                "Status": conn.get("status", ""),
                "Elapsed (d)": elapsed,
                "Est. Total (d)": f"{int(pred['p25'])}–{int(pred['p75'])}",
                "Est. Ready by": f"{est_lo} – {est_hi}",
                "Based On": basis_name,
                "Confidence": conf,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No in-progress connections with start dates found.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-header">By Provider</div>', unsafe_allow_html=True)
            prov_rows = [{"Provider": p, "Median (d)": f"{s['median']:.0f}", "Range": f"{s['p25']:.0f}–{s['p75']:.0f}d", "n": s["n"]}
                         for p, s in sorted(model["by_provider"].items(), key=lambda x: -x[1]["n"])]
            if prov_rows: st.dataframe(pd.DataFrame(prov_rows), use_container_width=True, hide_index=True)

        with col_b:
            st.markdown('<div class="section-header">By Shipper</div>', unsafe_allow_html=True)
            ship_rows = [{"Shipper": s, "Median (d)": f"{v['median']:.0f}", "Range": f"{v['p25']:.0f}–{v['p75']:.0f}d", "n": v["n"]}
                         for s, v in sorted(model["by_shipper"].items(), key=lambda x: -x[1]["n"])]
            if ship_rows: st.dataframe(pd.DataFrame(ship_rows), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Manual Prediction Lookup</div>', unsafe_allow_html=True)
        col_x, col_y = st.columns(2)
        with col_x:
            lp = st.selectbox("Provider", ["(any)"] + sorted(all_providers))
        with col_y:
            all_shippers = sorted(set(c.get("shipper", "Unknown") for c in connections.values()))
            ls = st.selectbox("Shipper", ["(any)"] + all_shippers)
        if lp != "(any)" or ls != "(any)":
            mock = {"provider": lp if lp != "(any)" else "X", "shipper": ls if ls != "(any)" else "X"}
            pred, basis, basis_name = predict(mock, model)
            if pred:
                conf, conf_cls = confidence_label(basis, pred["n"])
                st.markdown(f"""<div class="metric-card" style="margin-top:12px">
                    <div style="display:flex;gap:32px;align-items:center">
                        <div><div class="metric-val">{pred['median']:.0f}d</div><div class="metric-label">Median</div></div>
                        <div><div class="metric-val" style="color:#4ade80">{pred['p25']:.0f}d</div><div class="metric-label">Best case</div></div>
                        <div><div class="metric-val" style="color:#f59e0b">{pred['p75']:.0f}d</div><div class="metric-label">Likely max</div></div>
                        <div><div class="metric-val {conf_cls}" style="font-size:1.2rem">{conf}</div><div class="metric-label">Confidence · {pred['n']} samples</div></div>
                    </div>
                    <div style="margin-top:8px;font-size:0.72rem;color:var(--muted)">Based on: {basis_name}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("No historical data for this combination yet.")

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
        pred, basis, _ = predict(conn, model)
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
