import datetime
import base64
import os
import pathlib
import shutil
import tempfile
import re
import zipfile
import hashlib
import html
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
import pandas as pd
import streamlit as st

# محاولة استيراد مكتبة الرسوم البيانية بأمان
try:
  import plotly.express as px

  HAS_PLOTLY = True
except ImportError:
  HAS_PLOTLY = False

# =====================================================
# 1. إعدادات التطبيق وتسجيل الدخول
# =====================================================
st.set_page_config(
    page_title="OneSpot Cafe - Financial System", page_icon="☕", layout="wide"
)

APP_PASSWORD = "Cofe2026"
CURRENCY_LABEL = "ج.م"
BRANCHES = ["Onespot 1", "OneSpot 2"]
LEGACY_BRANCH = BRANCHES[0]


def format_currency(amount):
  return f"{amount:,.2f} {CURRENCY_LABEL}"

DATA_FILE = Path("cafe_data.csv")
BACKUP_FILE = Path("cafe_data.csv.bak")
AUDIT_FILE = Path("cafe_audit_log.csv")

COLUMNS = ["ID", "Date", "Month_No", "Branch", "Category", "Type", "Amount", "Description"]

INCOME_CATS = [
    "Daily Sales (المبيعات اليوميه)",
    "Other Income (إيرادات أخرى)",
]

EXPENSE_CATS = [
    "Coffee Beans & Milk (مواد خام)",
    "Staff Salaries (رواتب الموظفين)",
    "Rent & Utilities (إيجار وفواتير)",
    "(valu installments) (اقساط فاليو)",
    "Packaging (أكواب ومطبوعات)",
    "Other Expense (مصروفات أخرى)",
]


def password_entered():
    entered = st.session_state.get("password", "")
    st.session_state["password_correct"] = entered == APP_PASSWORD


def apply_login_background():
  """Show a local cafe photo on the login screen, with a safe CSS fallback."""
  image_path = Path(__file__).resolve().parent / "cafe_login_bg.png"
  try:
    image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    background = (
        "linear-gradient(rgba(8, 10, 12, 0.68), rgba(8, 10, 12, 0.72)), "
        f"url('data:image/png;base64,{image_data}')"
    )
  except (OSError, ValueError):
    background = "linear-gradient(135deg, #17120e, #3b2a1d)"

  st.markdown(
      f"""
      <style>
      .stApp, [data-testid="stAppViewContainer"] {{
          background-image: {background};
          background-size: contain;
          background-position: center;
          background-repeat: no-repeat;
          background-color: #17120e;
          background-attachment: fixed;
      }}
      [data-testid="stHeader"] {{ background: rgba(0, 0, 0, 0); }}
      [data-testid="stMainBlockContainer"] {{
          background: rgba(8, 10, 12, 0.16);
          border-radius: 16px;
      }}
      [data-testid="stMainBlockContainer"] h1,
      [data-testid="stMainBlockContainer"] label {{
          color: #ffffff !important;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
      }}
      [data-testid="stMainBlockContainer"] input {{
          background-color: rgba(255, 255, 255, 0.96);
          color: #171717;
      }}
      </style>
      """,
      unsafe_allow_html=True,
  )


def check_password():
    if st.session_state.get("password_correct", False):
        return True

    apply_login_background()
    login_banner = Path(__file__).resolve().parent / "login_banner.png"
    if login_banner.is_file():
        _, banner_col, _ = st.columns([1, 2.4, 1])
        with banner_col:
            st.image(str(login_banner), use_container_width=True)
    if not login_banner.is_file():
        st.title("🔒 OneSpot Cafe System - Secure Login")

    st.text_input(
        "Enter Cafe Password:",
        type="password",
        key="password",
        on_change=password_entered,
    )

    if st.session_state.get("password_correct") is False:
        st.error("❌ Incorrect password. Please try again.")

    return False


if not check_password():
  st.stop()


# =====================================================
# 2. قراءة البيانات والتحقق منها
# =====================================================
def load_csv_data():
  if not DATA_FILE.exists():
    return pd.DataFrame(columns=COLUMNS), None

  try:
    df = pd.read_csv(DATA_FILE)
  except Exception:
    return None, (
        "تعذر قراءة ملف cafe_data.csv. تم إيقاف التعديلات لحماية بياناتك."
    )

  if df.empty and len(df.columns) == 0:
    return pd.DataFrame(columns=COLUMNS), None

  if "ID" not in df.columns:
    df.insert(0, "ID", range(1, len(df) + 1))

  for col in COLUMNS:
    if col not in df.columns:
      df[col] = LEGACY_BRANCH if col == "Branch" else pd.NA

  df["Branch"] = df["Branch"].fillna(LEGACY_BRANCH).replace("", LEGACY_BRANCH)

  df = df[COLUMNS].copy()

  df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
  df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
  parsed_dates = pd.to_datetime(df["Date"], errors="coerce")

  valid = (
      df["ID"].notna()
      & (df["ID"] > 0)
      & (df["ID"] % 1 == 0)
      & parsed_dates.notna()
      & df["Category"].notna()
      & df["Type"].isin(["Income", "Expense"])
      & df["Amount"].notna()
      & (df["Amount"] > 0)
  )

  invalid_count = int((~valid).sum())

  if invalid_count:
    return None, (
        f"تم العثور على {invalid_count} صف غير صالح في ملف البيانات. تم إيقاف"
        " التعديلات حتى مراجعة الملف الأصلي."
    )

  df["ID"] = df["ID"].astype("int64")

  if df["ID"].duplicated().any():
    return None, (
        "يوجد تكرار في أرقام ID. تم إيقاف الحذف والحفظ لتجنب تعديل القيد الخطأ."
    )

  df["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")
  df["Month_No"] = parsed_dates.dt.month
  df["Branch"] = df["Branch"].astype(str)
  df["Category"] = df["Category"].astype(str)
  df["Type"] = df["Type"].astype(str)
  df["Amount"] = df["Amount"].astype(float)
  df["Description"] = df["Description"].fillna("").astype(str)

  return df[COLUMNS].reset_index(drop=True), None


# =====================================================
# 3. حفظ البيانات والنسخة الاحتياطية
# =====================================================
def save_csv_data(df):
  df = df[COLUMNS].copy()

  df["ID"] = pd.to_numeric(df["ID"], errors="raise")
  df["Amount"] = pd.to_numeric(df["Amount"], errors="raise")
  parsed_dates = pd.to_datetime(df["Date"], errors="raise")

  if df["ID"].isna().any() or df["ID"].duplicated().any():
    raise ValueError("أرقام القيود مفقودة أو مكررة.")

  if (df["ID"] <= 0).any() or (df["ID"] % 1 != 0).any():
    raise ValueError("يوجد رقم قيد غير صالح.")

  if df["Amount"].isna().any() or (df["Amount"] <= 0).any():
    raise ValueError("يوجد مبلغ غير صالح.")

  if not df["Type"].isin(["Income", "Expense"]).all():
    raise ValueError("يوجد نوع معاملة غير صالح.")

  df["ID"] = df["ID"].astype("int64")
  df["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")
  df["Month_No"] = parsed_dates.dt.month
  df["Branch"] = df["Branch"].fillna(LEGACY_BRANCH).astype(str)

  DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

  if DATA_FILE.exists():
    shutil.copy2(DATA_FILE, BACKUP_FILE)

  temp_path = None

  try:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8-sig",
        newline="",
        suffix=".tmp",
        prefix="cafe_data_",
        dir=str(DATA_FILE.parent),
        delete=False,
    ) as temp_file:
      temp_path = Path(temp_file.name)
      df.to_csv(temp_file, index=False)
      temp_file.flush()
      os.fsync(temp_file.fileno())

    os.replace(temp_path, DATA_FILE)
    temp_path = None

  finally:
    if temp_path is not None and temp_path.exists():
      temp_path.unlink()


def read_database_url():
  try:
    direct_url = st.secrets.get("DATABASE_URL", "")
    if direct_url:
      return str(direct_url).strip()

    # Also accept the nested TOML layout some Streamlit users configure.
    connections = st.secrets.get("connections", {})
    postgresql = connections.get("postgresql", {}) if hasattr(connections, "get") else {}
    nested_url = postgresql.get("DATABASE_URL", "") or postgresql.get("url", "")
    return str(nested_url).strip()
  except Exception:
    return ""


@st.cache_resource(show_spinner=False)
def create_database_engine(database_url):
  from sqlalchemy import create_engine

  return create_engine(database_url, pool_pre_ping=True, pool_recycle=300)


def get_database_engine():
  database_url = read_database_url()
  return create_database_engine(database_url) if database_url else None


def ensure_database(engine):
  from sqlalchemy import text

  with engine.begin() as connection:
    # Serialize first-time setup so simultaneous visits cannot import the CSV twice.
    connection.execute(text("SELECT pg_advisory_xact_lock(784213905)"))
    connection.execute(text("""
      CREATE TABLE IF NOT EXISTS transactions (
        "ID" BIGINT PRIMARY KEY,
        "Date" DATE NOT NULL,
        "Month_No" INTEGER NOT NULL,
        "Branch" TEXT NOT NULL,
        "Category" TEXT NOT NULL,
        "Type" TEXT NOT NULL CHECK ("Type" IN ('Income', 'Expense')),
        "Amount" DOUBLE PRECISION NOT NULL CHECK ("Amount" > 0),
        "Description" TEXT NOT NULL DEFAULT ''
      )
    """))
    connection.execute(text("""
      CREATE TABLE IF NOT EXISTS onespot_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    """))
    connection.execute(text("""
      CREATE TABLE IF NOT EXISTS transaction_audit (
        audit_id BIGSERIAL PRIMARY KEY,
        occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        actor TEXT NOT NULL DEFAULT 'مستخدم التطبيق',
        action TEXT NOT NULL,
        transaction_id BIGINT NOT NULL,
        transaction_date DATE,
        branch TEXT,
        category TEXT,
        transaction_type TEXT,
        amount DOUBLE PRECISION,
        description TEXT
      )
    """))
    connection.execute(text("""
      CREATE TABLE IF NOT EXISTS recurring_expenses (
        id BIGSERIAL PRIMARY KEY,
        branch TEXT NOT NULL,
        category TEXT NOT NULL,
        amount DOUBLE PRECISION NOT NULL CHECK (amount > 0),
        description TEXT NOT NULL,
        due_day INTEGER NOT NULL DEFAULT 1 CHECK (due_day BETWEEN 1 AND 28),
        active BOOLEAN NOT NULL DEFAULT TRUE
      )
    """))
    connection.execute(text("""
      CREATE TABLE IF NOT EXISTS employee_attendance (
        attendance_id BIGSERIAL PRIMARY KEY,
        employee_name TEXT NOT NULL,
        attendance_date DATE NOT NULL,
        day_name TEXT,
        check_in TEXT,
        check_out TEXT,
        work_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
        salary_advance DOUBLE PRECISION NOT NULL DEFAULT 0,
        team TEXT NOT NULL DEFAULT 'OneSpot',
        imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (employee_name, attendance_date)
      )
    """))
    imported = connection.execute(
        text("SELECT value FROM onespot_metadata WHERE key = 'csv_import_v1'")
    ).scalar_one_or_none()
    if imported is None:
      legacy_df, legacy_error = load_csv_data()
      if legacy_error:
        raise ValueError(legacy_error)
      if not legacy_df.empty:
        # PostgreSQL DATE columns must receive Python date values, not CSV strings.
        legacy_df["Date"] = pd.to_datetime(legacy_df["Date"], errors="raise").dt.date
        legacy_df.to_sql("transactions", con=connection, if_exists="append", index=False)
      connection.execute(
          text("INSERT INTO onespot_metadata (key, value) VALUES ('csv_import_v1', 'done')")
      )


def load_data():
  engine = get_database_engine()
  if engine is None:
    return load_csv_data()
  try:
    from sqlalchemy import text

    ensure_database(engine)
    df = pd.read_sql_query(
        text('SELECT "ID", "Date", "Month_No", "Branch", "Category", "Type", "Amount", "Description" FROM transactions ORDER BY "ID"'),
        engine,
    )
    if df.empty:
      return pd.DataFrame(columns=COLUMNS), None
    parsed_dates = pd.to_datetime(df["Date"], errors="coerce")
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("int64")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").astype(float)
    df["Date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    df["Month_No"] = parsed_dates.dt.month
    df["Branch"] = df["Branch"].fillna(LEGACY_BRANCH).astype(str)
    df["Category"] = df["Category"].astype(str)
    df["Type"] = df["Type"].astype(str)
    df["Description"] = df["Description"].fillna("").astype(str)
    return df[COLUMNS].reset_index(drop=True), None
  except Exception as exc:
    return None, f"تعذر الاتصال بقاعدة Neon أو قراءة القيود منها: {exc}"


def save_data(df):
  df = df[COLUMNS].copy()
  df["ID"] = pd.to_numeric(df["ID"], errors="raise")
  df["Amount"] = pd.to_numeric(df["Amount"], errors="raise")
  parsed_dates = pd.to_datetime(df["Date"], errors="raise")
  if df["ID"].isna().any() or df["ID"].duplicated().any():
    raise ValueError("أرقام القيود مفقودة أو مكررة.")
  if (df["ID"] <= 0).any() or (df["ID"] % 1 != 0).any():
    raise ValueError("يوجد رقم قيد غير صالح.")
  if df["Amount"].isna().any() or (df["Amount"] <= 0).any():
    raise ValueError("يوجد مبلغ غير صالح.")
  if not df["Type"].isin(["Income", "Expense"]).all():
    raise ValueError("يوجد نوع معاملة غير صالح.")
  df["ID"] = df["ID"].astype("int64")
  # Bind as a PostgreSQL DATE instead of sending VARCHAR values.
  df["Date"] = parsed_dates.dt.date
  df["Month_No"] = parsed_dates.dt.month
  df["Branch"] = df["Branch"].fillna(LEGACY_BRANCH).astype(str)

  engine = get_database_engine()
  if engine is None:
    previous_df, previous_error = load_csv_data()
    if previous_error:
      raise ValueError(previous_error)
    events = build_transaction_audit_events(previous_df, df)
    save_csv_data(df)
    append_transaction_audit_csv(events)
    return
  from sqlalchemy import text

  ensure_database(engine)
  with engine.begin() as connection:
    old_rows = connection.execute(text(
        'SELECT "ID", "Date", "Month_No", "Branch", "Category", "Type", "Amount", "Description" FROM transactions'
    )).mappings().all()
    old_df = pd.DataFrame(old_rows, columns=COLUMNS)
    events = build_transaction_audit_events(old_df, df)
    connection.execute(text("DELETE FROM transactions"))
    if not df.empty:
      df.to_sql("transactions", con=connection, if_exists="append", index=False)
    if events:
      connection.execute(text("""
        INSERT INTO transaction_audit
          (actor, action, transaction_id, transaction_date, branch, category,
           transaction_type, amount, description)
        VALUES
          (:actor, :action, :transaction_id, :transaction_date, :branch, :category,
           :transaction_type, :amount, :description)
      """), events)


def build_transaction_audit_events(previous_df, current_df):
  """Return audit rows for added, changed, or removed transactions."""
  def normalize(row):
    parsed_date = pd.to_datetime(row["Date"], errors="coerce")
    return {
        "transaction_id": int(row["ID"]),
        "transaction_date": None if pd.isna(parsed_date) else parsed_date.date(),
        "branch": str(row.get("Branch", "")),
        "category": str(row.get("Category", "")),
        "transaction_type": str(row.get("Type", "")),
        "amount": float(row.get("Amount", 0) or 0),
        "description": str(row.get("Description", "") or ""),
    }

  old = {
      int(row["ID"]): normalize(row)
      for _, row in previous_df.iterrows()
  } if previous_df is not None and not previous_df.empty else {}
  new = {
      int(row["ID"]): normalize(row)
      for _, row in current_df.iterrows()
  } if current_df is not None and not current_df.empty else {}

  events = []
  for transaction_id in sorted(set(old) | set(new)):
    before = old.get(transaction_id)
    after = new.get(transaction_id)
    if before == after:
      continue
    action = "إضافة" if before is None else "حذف" if after is None else "تعديل"
    details = after or before
    events.append({
        "actor": "مستخدم التطبيق",
        "action": action,
        **details,
    })

  return events


def append_transaction_audit_csv(events):
  if not events:
    return
  timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
  audit_df = pd.DataFrame(events)
  audit_df.insert(0, "occurred_at", timestamp)
  audit_df.to_csv(
      AUDIT_FILE,
      mode="a",
      header=not AUDIT_FILE.exists(),
      index=False,
      encoding="utf-8-sig",
  )


def load_transaction_audit(limit=200):
  engine = get_database_engine()
  if engine is not None:
    from sqlalchemy import text

    ensure_database(engine)
    return pd.read_sql_query(text("""
      SELECT occurred_at, actor, action, transaction_id, transaction_date,
             branch, category, transaction_type, amount, description
      FROM transaction_audit
      ORDER BY audit_id DESC
      LIMIT :limit
    """), engine, params={"limit": int(limit)})
  if not AUDIT_FILE.exists():
    return pd.DataFrame()
  return pd.read_csv(AUDIT_FILE).tail(limit).iloc[::-1].reset_index(drop=True)


def attendance_day_mask(frame):
  """Count a day when hours exist or either attendance punch is recorded."""
  hours = pd.to_numeric(
      frame.get("ساعات العمل", pd.Series(0, index=frame.index)), errors="coerce"
  ).fillna(0)
  has_hours = hours > 0
  has_punch = pd.Series(False, index=frame.index)
  off_marker = re.compile(
      r"\boff\b|week\s*off|holiday|vacation|\bleave\b|إجاز|اجاز|راحة|عطلة|اوف",
      flags=re.IGNORECASE,
  )
  for column in ("الحضور", "الانصراف"):
    if column in frame:
      values = frame[column].fillna("").astype(str).str.strip().str.lower()
      has_punch |= ~values.isin(["", "nan", "none", "nat"]) & ~values.str.contains(
          off_marker, na=False
      )
  return has_hours | has_punch


def attendance_off_mask(frame):
  """Recognize OFF/leave markers preserved in the Excel day or punch cells."""
  markers = re.compile(
      r"\boff\b|week\s*off|holiday|vacation|\bleave\b|إجاز|اجاز|راحة|عطلة|اوف",
      flags=re.IGNORECASE,
  )
  off = pd.Series(False, index=frame.index)
  for column in ("اليوم", "الحضور", "الانصراف"):
    if column in frame:
      off |= frame[column].fillna("").astype(str).str.contains(markers, na=False)
  return off


def attendance_status_for_row(row):
  has_work = bool(attendance_day_mask(pd.DataFrame([row])).iloc[0])
  is_off = bool(attendance_off_mask(pd.DataFrame([row])).iloc[0])
  if is_off and has_work:
    return "حضور في يوم OFF"
  if has_work:
    return "حضور"
  if is_off:
    return "إجازة (OFF)"
  return "لا يوجد تسجيل"


def save_employee_attendance(attendance_df):
  """Keep one row per employee/date and refresh it when the uploaded details changed."""
  if attendance_df is None or attendance_df.empty:
    return {"inserted": 0, "updated": 0, "unchanged": 0}
  engine = get_database_engine()
  if engine is None:
    raise RuntimeError("Neon غير متصل؛ لم يتم حفظ بيانات متابعة الموظفين.")

  from sqlalchemy import text

  ensure_database(engine)

  def text_value(value):
    if value is None or pd.isna(value):
      return None
    if isinstance(value, (datetime.datetime, datetime.time)):
      return value.isoformat()
    return str(value).strip()

  records = []
  for row in attendance_df.to_dict("records"):
    parsed_date = pd.to_datetime(row.get("التاريخ"), errors="coerce")
    if pd.isna(parsed_date):
      continue
    hours = pd.to_numeric(row.get("ساعات العمل"), errors="coerce")
    advance = pd.to_numeric(row.get("السلفة (ج.م)"), errors="coerce")
    records.append({
        "employee_name": str(row.get("الموظف", "")).strip(),
        "attendance_date": parsed_date.date(),
        "day_name": text_value(row.get("اليوم")),
        "check_in": text_value(row.get("الحضور")),
        "check_out": text_value(row.get("الانصراف")),
        "work_hours": 0.0 if pd.isna(hours) else float(hours),
        "salary_advance": 0.0 if pd.isna(advance) else float(advance),
        "team": text_value(row.get("الفريق")) or "OneSpot",
    })

  inserted = updated = unchanged = 0
  with engine.begin() as connection:
    for record in records:
      existed = connection.execute(text("""
        SELECT 1 FROM employee_attendance
        WHERE employee_name = :employee_name AND attendance_date = :attendance_date
      """), record).scalar_one_or_none() is not None
      result = connection.execute(text("""
        INSERT INTO employee_attendance
          (employee_name, attendance_date, day_name, check_in, check_out,
           work_hours, salary_advance, team)
        VALUES
          (:employee_name, :attendance_date, :day_name, :check_in, :check_out,
           :work_hours, :salary_advance, :team)
        ON CONFLICT (employee_name, attendance_date) DO UPDATE SET
          day_name = EXCLUDED.day_name,
          check_in = EXCLUDED.check_in,
          check_out = EXCLUDED.check_out,
          work_hours = EXCLUDED.work_hours,
          salary_advance = EXCLUDED.salary_advance,
          team = EXCLUDED.team
        WHERE (employee_attendance.day_name, employee_attendance.check_in,
               employee_attendance.check_out, employee_attendance.work_hours,
               employee_attendance.salary_advance, employee_attendance.team)
          IS DISTINCT FROM
              (EXCLUDED.day_name, EXCLUDED.check_in, EXCLUDED.check_out,
               EXCLUDED.work_hours, EXCLUDED.salary_advance, EXCLUDED.team)
      """), record)
      if result.rowcount and result.rowcount > 0:
        if existed:
          updated += 1
        else:
          inserted += 1
      else:
        unchanged += 1
  return {"inserted": inserted, "updated": updated, "unchanged": unchanged}


def load_employee_attendance():
  engine = get_database_engine()
  if engine is None:
    return None
  from sqlalchemy import text

  ensure_database(engine)
  attendance_df = pd.read_sql_query(text("""
    SELECT employee_name AS "الموظف",
           attendance_date AS "التاريخ",
           day_name AS "اليوم",
           check_in AS "الحضور",
           check_out AS "الانصراف",
           work_hours AS "ساعات العمل",
           salary_advance AS "السلفة (ج.م)",
           team AS "الفريق"
    FROM employee_attendance
    ORDER BY attendance_date DESC, employee_name
  """), engine)
  if attendance_df.empty:
    return pd.DataFrame(columns=[
        "الموظف", "التاريخ", "اليوم", "الحضور", "الانصراف",
        "ساعات العمل", "السلفة (ج.م)", "الفريق",
    ])
  attendance_df["التاريخ"] = pd.to_datetime(attendance_df["التاريخ"], errors="coerce").dt.normalize()
  attendance_df["ساعات العمل"] = pd.to_numeric(attendance_df["ساعات العمل"], errors="coerce").fillna(0.0)
  attendance_df["السلفة (ج.م)"] = pd.to_numeric(attendance_df["السلفة (ج.م)"], errors="coerce").fillna(0.0)
  return attendance_df


def process_attendance_upload(attendance_rows, uploaded_file, ignored_sheets):
  if not attendance_rows:
    st.warning("لم أجد سجلات حضور في أوراق الموظفين.")
    return None

  raw_count = len(attendance_rows)
  attendance_df = pd.DataFrame(attendance_rows)
  attendance_df["التاريخ"] = pd.to_datetime(attendance_df["التاريخ"], errors="coerce").dt.normalize()
  attendance_df = attendance_df.dropna(subset=["التاريخ"])
  attendance_df = attendance_df.drop_duplicates(
      subset=["الموظف", "التاريخ"], keep="last"
  ).sort_values(["التاريخ", "الموظف"], ascending=[False, True])
  duplicates_in_file = raw_count - len(attendance_df)
  st.session_state["attendance_imported_df"] = attendance_df

  upload_signature = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
  if st.session_state.get("attendance_saved_upload_signature") != upload_signature:
    try:
      saved = save_employee_attendance(attendance_df)
      st.session_state["attendance_saved_upload_signature"] = upload_signature
      st.session_state["attendance_upload_result"] = {
          "signature": upload_signature,
          **saved,
          "skipped": duplicates_in_file + saved["unchanged"],
          "error": None,
      }
    except Exception as exc:
      st.session_state["attendance_upload_result"] = {
          "signature": upload_signature,
          "inserted": 0,
          "skipped": duplicates_in_file,
          "error": str(exc),
      }

  result = st.session_state.get("attendance_upload_result", {})
  if result.get("signature") == upload_signature:
    if result.get("error"):
      st.error(f"تعذر حفظ السجلات الجديدة في متابعة الموظفين: {result['error']}")
    elif result.get("inserted", 0) or result.get("updated", 0):
      st.success(
          f"تمت إضافة {result.get('inserted', 0)} سجل جديد وتحديث "
          f"{result.get('updated', 0)} سجل موجود في متابعة الموظفين."
      )
    else:
      st.info("لا توجد تغييرات جديدة؛ بيانات التواريخ الموجودة مطابقة للملف.")
    if result.get("skipped", 0):
      st.caption(f"تم تخطي {result['skipped']} سجل مكرر، والاحتفاظ بسجل واحد لكل موظف في اليوم.")
  if ignored_sheets:
    st.caption("تم تجاهل الأوراق غير الخاصة بسجلات الموظفين: " + "، ".join(ignored_sheets))
  return attendance_df


def read_attendance_with_builtin_excel(uploaded_file):
  """Read the workbook's cached cell values with Python's standard library."""
  ns = {
      "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
  }
  records = []
  ignored_sheets = []

  with zipfile.ZipFile(BytesIO(uploaded_file.getvalue())) as archive:
    names = set(archive.namelist())
    shared_strings = []
    if "xl/sharedStrings.xml" in names:
      root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
      for item in root.findall("main:si", ns):
        shared_strings.append("".join(node.text or "" for node in item.findall(".//main:t", ns)))

    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationships = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships_root.findall("pkg:Relationship", ns)
    }

    for sheet_info in workbook_root.findall("main:sheets/main:sheet", ns):
      sheet_name = sheet_info.attrib.get("name", "")
      if sheet_name.strip().lower() == "summary":
        ignored_sheets.append(sheet_name)
        continue
      target = relationships.get(sheet_info.attrib.get(f"{{{ns['rel']}}}id"))
      if not target:
        ignored_sheets.append(sheet_name)
        continue
      sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
      sheet_path = re.sub(r"^xl/\.\./", "", sheet_path)
      if sheet_path not in names:
        ignored_sheets.append(sheet_name)
        continue

      sheet_root = ET.fromstring(archive.read(sheet_path))
      grid = {}
      for row_node in sheet_root.findall(".//main:sheetData/main:row", ns):
        row_num = int(row_node.attrib.get("r", "0"))
        row_values = {}
        for cell in row_node.findall("main:c", ns):
          ref = cell.attrib.get("r", "")
          match = re.match(r"([A-Z]+)", ref)
          if not match:
            continue
          col_num = 0
          for char in match.group(1):
            col_num = col_num * 26 + ord(char) - 64
          cell_type = cell.attrib.get("t")
          value_node = cell.find("main:v", ns)
          if cell_type == "inlineStr":
            value = "".join(node.text or "" for node in cell.findall(".//main:t", ns))
          elif value_node is None:
            value = None
          elif cell_type == "s":
            try:
              value = shared_strings[int(value_node.text)]
            except (ValueError, IndexError, TypeError):
              value = None
          else:
            value = value_node.text
          row_values[col_num] = value
        if row_values:
          grid[row_num] = row_values

      header_num = None
      header = {}
      for row_num, row_values in grid.items():
        normalized = {
            col: str(value).strip().lower().replace("\n", " ") if value is not None else ""
            for col, value in row_values.items()
        }
        if "date" in normalized.values() and "hours" in normalized.values():
          header_num = row_num
          header = {value: col for col, value in normalized.items()}
          break
      if header_num is None:
        ignored_sheets.append(sheet_name)
        continue

      employee_name = sheet_name
      for row_values in grid.values():
        if str(row_values.get(1, "")).strip().lower() == "name:" and row_values.get(3):
          employee_name = str(row_values[3]).strip()
          break

      def get_cell(row_values, label):
        return row_values.get(header.get(label)) if header.get(label) else None

      def as_excel_datetime(value):
        try:
          return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(value))
        except (TypeError, ValueError, OverflowError):
          return pd.to_datetime(value, errors="coerce")

      def as_excel_time(value):
        try:
          seconds = round(float(value) * 86400) % 86400
          return datetime.time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)
        except (TypeError, ValueError, OverflowError):
          return value

      for row_num, row_values in grid.items():
        if row_num <= header_num:
          continue
        raw_date = get_cell(row_values, "date")
        if raw_date is None:
          continue
        parsed_date = as_excel_datetime(raw_date)
        if pd.isna(parsed_date):
          continue
        try:
          hours = float(get_cell(row_values, "hours") or 0)
        except (TypeError, ValueError):
          hours = 0.0
        try:
          advance = float(get_cell(row_values, "salary advance") or 0)
        except (TypeError, ValueError):
          advance = 0.0
        raw_day = get_cell(row_values, "day")
        if any(
            re.search(r"\boff\b", str(value), flags=re.IGNORECASE)
            for value in row_values.values() if value is not None
        ):
          raw_day = "OFF"
        parsed_day = as_excel_datetime(raw_day) if raw_day is not None else None
        if isinstance(raw_day, str) and parsed_day is not None and pd.isna(parsed_day):
          parsed_day = raw_day.strip()
        records.append({
            "الموظف": employee_name,
            "التاريخ": pd.Timestamp(parsed_date).normalize(),
            "اليوم": parsed_day,
            "الحضور": as_excel_time(get_cell(row_values, "start time")),
            "الانصراف": as_excel_time(get_cell(row_values, "end time")),
            "ساعات العمل": hours,
            "السلفة (ج.م)": advance,
            "الفريق": "OneSpot",
        })

  return records, ignored_sheets


def read_attendance_excel(uploaded_file):
  try:
    from openpyxl import load_workbook
  except ImportError:
    return read_attendance_with_builtin_excel(uploaded_file)

  attendance_book = load_workbook(
      uploaded_file, read_only=True, data_only=True, keep_vba=False
  )
  attendance_rows = []
  ignored_sheets = []
  try:
    for sheet in attendance_book.worksheets:
      if sheet.title.strip().lower() == "summary":
        ignored_sheets.append(sheet.title)
        continue
      header_row = None
      headers = []
      for row_num, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        normalized = [
            str(value).strip().lower().replace("\n", " ") if value is not None else ""
            for value in row
        ]
        if "date" in normalized and "hours" in normalized:
          header_row = row_num
          headers = normalized
          break

      if header_row is None:
        ignored_sheets.append(sheet.title)
        continue

      positions = {
          name: headers.index(name)
          for name in ["date", "day", "salary advance", "start time", "end time", "hours"]
          if name in headers
      }
      employee_name = None
      for row in sheet.iter_rows(min_row=1, max_row=min(header_row, 8), values_only=True):
        if len(row) > 2 and str(row[0]).strip().lower() == "name:" and row[2]:
          employee_name = str(row[2]).strip()
          break
      employee_name = employee_name or sheet.title

      for row in sheet.iter_rows(min_row=header_row + 1, values_only=True):
        date_value = row[positions["date"]] if positions["date"] < len(row) else None
        if date_value is None:
          continue
        date_value = pd.to_datetime(date_value, errors="coerce")
        if pd.isna(date_value):
          continue

        def cell_value(field):
          idx = positions.get(field)
          return row[idx] if idx is not None and idx < len(row) else None

        day_value = cell_value("day")
        if any(
            re.search(r"\boff\b", str(value), flags=re.IGNORECASE)
            for value in row if value is not None
        ):
          day_value = "OFF"

        hours = pd.to_numeric(cell_value("hours"), errors="coerce")
        advance = pd.to_numeric(cell_value("salary advance"), errors="coerce")
        attendance_rows.append({
            "الموظف": employee_name,
            "التاريخ": date_value.normalize(),
            "اليوم": day_value,
            "الحضور": cell_value("start time"),
            "الانصراف": cell_value("end time"),
            "ساعات العمل": 0.0 if pd.isna(hours) else float(hours),
            "السلفة (ج.م)": 0.0 if pd.isna(advance) else float(advance),
            "الفريق": "OneSpot",
        })
  finally:
    attendance_book.close()
  return attendance_rows, ignored_sheets


df_all, data_error = load_data()
data_blocked = data_error is not None

if data_error:
  st.error(data_error)
if not read_database_url():
  st.info(
      "Neon غير متصل بعد. التطبيق يعمل حاليًا بملف CSV محلي؛ أضف DATABASE_URL في Secrets "
      "على Streamlit لتخزين القيود في قاعدة البيانات."
  )


# =====================================================
# 4. واجهة OneSpot Cafe المالية
# =====================================================
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        font-family: Arial, "Segoe UI", sans-serif !important;
    }
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] button,
    [data-testid="stAppViewContainer"] input,
    [data-testid="stAppViewContainer"] textarea,
    [data-testid="stAppViewContainer"] select,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] {
        font-family: Arial, "Segoe UI", sans-serif !important;
    }
    .stApp { background: #f3f0eb; color: #2d2924; }
    [data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }
    [data-testid="stMain"] { background: #f3f0eb; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1480px;
        padding: 1.4rem 2rem 3rem;
    }
    [data-testid="stAppViewContainer"] { background: #f3f0eb; }
    .onespot-nav {
        background: #3b281b; color: #fff; border-radius: 8px 8px 0 0;
        padding: 13px 22px; display:flex; align-items:center; justify-content:flex-start;
        direction:rtl; text-align:right; margin: -1.4rem -2rem 0; min-height: 62px;
    }
    .onespot-brand { font-size: 19px; font-weight: 700; color:#fff; }
    .onespot-sub { font-size: 11px; letter-spacing:1.2px; color:#e8d2b8; margin-top:4px; }
    .onespot-links { color:#f3e9dd; font-size:13px; word-spacing:18px; }
    [data-baseweb="tab-list"] {
        direction:rtl; justify-content:flex-start; gap: 8px;
        background:#3b281b; border-bottom:0; margin: 0 -2rem 1.5rem;
        padding: 0 1.5rem 8px; border-radius:0 0 8px 8px;
    }
    [data-baseweb="tab"] {
        height: 47px; padding: 0 20px; color: #f3e9dd;
        background: transparent; border-radius: 8px;
        font-size: 16px !important; font-weight: 700 !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: #fff; background: #584333; border-bottom: 2px solid #bc8848;
        font-size: 17px !important; font-weight: 800 !important;
    }
    [data-testid="stTabs"] [role="tab"],
    [data-testid="stTabs"] [role="tab"] p,
    [data-testid="stTabs"] [role="tab"] div {
        font-size: 18px !important;
        font-weight: 700 !important;
        line-height: 1.35 !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
        font-size: 19px !important;
        font-weight: 800 !important;
    }
    h1, h2, h3 { color:#2d2119; }
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e7ddd2;
        border-radius: 12px; padding: 16px 18px; box-shadow: 0 2px 8px #3b281b0a;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e7ddd2 !important; border-radius: 12px !important; background:#fff;
    }
    [data-testid="stRadio"] [role="radiogroup"] { gap: 8px; }
    [data-testid="stRadio"] [role="radiogroup"] label {
        background:#fff; border:1px solid #e5d9cc; border-radius:9px; padding:8px 14px;
    }
    [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
        background:#f1e8dc; border-color:#94652f;
    }
    [data-testid="stWidgetLabel"] p { color:#6f5a48; }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-radius:8px !important; border-color:#e5d9cc !important; background:#fbf9f6;
    }
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stButton"] button[kind="primary"], button[kind="primary"] {
        background:#bc8848 !important; color:#fff !important; border:1px solid #bc8848 !important;
        border-radius:8px !important; font-weight:700 !important;
    }
    [data-testid="stFormSubmitButton"] button:hover { background:#94652f !important; border-color:#94652f !important; }
    [data-testid="stDataFrame"] { border:1px solid #e7ddd2; border-radius:10px; overflow:hidden; }
    hr { border-color:#ddd2c7 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="onespot-nav"><div><div class="onespot-brand">☕ OneSpot Cafe</div>'
    '<div class="onespot-sub">COFFEE &amp; MORE · FINANCIAL SYSTEM</div></div></div>',
    unsafe_allow_html=True,
)
tab_home, tab_add, tab_history, tab_admin, tab_reports, tab_attendance, tab_employee_tracking = st.tabs(
    ["🏠 الرئيسية", "➕ إضافة قيد", "📒 سجل المعاملات", "🗂️ إدارة القيود", "📊 مقارنة وتقارير", "🕒 الحضور والانصراف", "👥 متابعة الموظفين"]
)

# =====================================================
# 5. تسجيل قيد جديد
# =====================================================
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0


@st.fragment
def transaction_form_fragment():
    st.subheader("＋ إضافة قيد جديد")

    feedback = st.session_state.pop("transaction_save_feedback", None)
    if feedback:
        if feedback["duplicate"]:
            st.warning(feedback["message"])
        else:
            st.success(feedback["message"])

    if data_blocked:
        st.warning("تم إيقاف تسجيل القيود حتى إصلاح ملف البيانات.")
        return

    version = st.session_state["form_version"]

    with st.container(border=True):
        tx_type = st.radio(
            "نوع القيد:",
            ["Income", "Expense"],
            index=None,
            horizontal=True,
            format_func=lambda value: "إيراد" if value == "Income" else "مصروف",
            key=f"tp_{version}",
        )

        if tx_type is None:
            st.info("اختر إيراد أو مصروف، ثم أدخل بيانات القيد.")

        with st.form(key=f"transaction_form_{version}"):
            branch_col, date_col, category_col, amount_col, description_col = st.columns([.9, 1.05, 1.15, .9, 1.9])
            with branch_col:
                transaction_branch = st.selectbox(
                    "الفرع:",
                    [None] + BRANCHES,
                    index=0,
                    format_func=lambda value: "اختر الفرع" if value is None else value,
                    key=f"branch_{version}",
                )
            with date_col:
                tx_date = st.date_input(
                    "التاريخ:",
                    value=datetime.date.today(),
                    key=f"dt_{version}",
                )
            with category_col:
                if tx_type == "Income":
                    tx_category = st.selectbox(
                        "البند المحاسبي:",
                        INCOME_CATS,
                        key=f"cat_in_{version}",
                    )
                elif tx_type == "Expense":
                    tx_category = st.selectbox(
                        "البند المحاسبي:",
                        EXPENSE_CATS,
                        key=f"cat_ex_{version}",
                    )
                else:
                    tx_category = None
                    st.selectbox(
                        "البند المحاسبي:",
                        ["اختر نوع القيد أولاً"],
                        disabled=True,
                        key=f"cat_none_{version}",
                    )
            with amount_col:
                tx_amount = st.number_input(
                    "المبلغ (ج.م):",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f",
                    key=f"amt_{version}",
                )
            with description_col:
                tx_description = st.text_input(
                    "البيان:",
                    key=f"desc_{version}",
                )
            st.caption("اضغط Enter من خانة البيان للحفظ السريع.")

            submitted = st.form_submit_button(
                "حفظ القيد",
                type="primary",
                use_container_width=True,
            )

    if not submitted:
        return

    if tx_type not in ["Income", "Expense"]:
        st.error("اختر نوع المعاملة.")
    elif transaction_branch not in BRANCHES:
        st.error("اختر الفرع قبل الحفظ.")
    elif tx_category is None:
        st.error("اختر البند المحاسبي.")
    elif tx_amount <= 0:
        st.error("يجب أن يكون المبلغ أكبر من صفر.")
    elif not tx_description.strip():
        st.error("اكتب البيان قبل الحفظ.")
    else:
        latest_df, latest_error = load_data()
        if latest_error:
            st.error("تعذر التحقق من ملف البيانات: " + latest_error)
            return

        duplicate_found = False
        if not latest_df.empty:
            duplicate_found = bool((
                (pd.to_datetime(latest_df["Date"], errors="coerce").dt.date == tx_date)
                & (latest_df["Branch"].astype(str) == transaction_branch)
                & (pd.to_numeric(latest_df["Amount"], errors="coerce").round(2) == round(float(tx_amount), 2))
                & (latest_df["Description"].fillna("").astype(str).str.strip().str.casefold() == tx_description.strip().casefold())
            ).any())

        next_id = int(latest_df["ID"].max()) + 1 if not latest_df.empty else 1
        new_row = pd.DataFrame([{
            "ID": next_id,
            "Date": tx_date.strftime("%Y-%m-%d"),
            "Month_No": tx_date.month,
            "Branch": transaction_branch,
            "Category": tx_category,
            "Type": tx_type,
            "Amount": float(tx_amount),
            "Description": tx_description.strip(),
        }])
        updated_df = pd.concat([latest_df, new_row], ignore_index=True)

        try:
            save_data(updated_df)
            st.session_state["form_version"] += 1
            message = f"تم حفظ القيد رقم {next_id} بنجاح."
            if duplicate_found:
                message += " يوجد قيد بنفس التاريخ والفرع والمبلغ والبيان؛ تم حفظه بناءً على اختيارك."
            st.session_state["transaction_save_feedback"] = {
                "duplicate": duplicate_found,
                "message": message,
            }
            st.rerun()
        except Exception as exc:
            st.error(f"تعذر حفظ القيد والحفاظ على البيانات. التفاصيل: {exc}")


with tab_add:
    transaction_form_fragment()

st.markdown("---")

# Use an empty, schema-compatible frame when the CSV is unavailable.
data_view = df_all if df_all is not None else pd.DataFrame(columns=COLUMNS)

with tab_home:
    # =====================================================
    # 6. الملخص المالي والرسوم البيانية
    # =====================================================
    st.subheader("ملخص الأداء المالي")
    
    if not data_view.empty:
        report_df = data_view.copy()
        report_df["Amount"] = pd.to_numeric(report_df["Amount"], errors="coerce").fillna(0)
        report_df["Parsed_Date"] = pd.to_datetime(report_df["Date"], errors="coerce")
        report_df["Year_Month"] = report_df["Parsed_Date"].dt.strftime("%Y-%m")
    
        selected_branch = st.radio(
            "عرض بيانات:",
            ["إجمالي الفرعين"] + BRANCHES,
            horizontal=True,
            key="dashboard_branch_filter",
        )
        analysis_df = (
            report_df if selected_branch == "إجمالي الفرعين"
            else report_df[report_df["Branch"] == selected_branch]
        )
        total_income = analysis_df.loc[analysis_df["Type"] == "Income", "Amount"].sum()
        total_expense = analysis_df.loc[analysis_df["Type"] == "Expense", "Amount"].sum()
        net_profit = total_income - total_expense
        summary_scope = "الفرعين" if selected_branch == "إجمالي الفرعين" else selected_branch
    
        metric_income, metric_expense, metric_profit = st.columns(3)
        metric_income.metric(f"إيرادات {summary_scope}", format_currency(total_income))
        metric_expense.metric(f"مصروفات {summary_scope}", format_currency(total_expense))
        metric_profit.metric(
            f"صافي ربح {summary_scope}",
            format_currency(net_profit),
            delta=format_currency(net_profit),
        )

        st.markdown("### ملخص الأداء المالي لكل فرع")
        branch_columns = st.columns(len(BRANCHES))
        for branch_column, branch_name in zip(branch_columns, BRANCHES):
            branch_data = report_df[report_df["Branch"] == branch_name]
            branch_income = branch_data.loc[branch_data["Type"] == "Income", "Amount"].sum()
            branch_expense = branch_data.loc[branch_data["Type"] == "Expense", "Amount"].sum()
            with branch_column:
                with st.container(border=True):
                    st.markdown(f"#### {branch_name}")
                    st.metric("الإيرادات", format_currency(branch_income))
                    st.metric("المصروفات", format_currency(branch_expense))
                    st.metric("صافي الربح", format_currency(branch_income - branch_expense))
                    st.caption(f"عدد القيود المسجلة: {len(branch_data)}")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            with st.container(border=True):
                st.markdown("**توزيع المصروفات حسب البند**")
                expense_df = analysis_df[analysis_df["Type"] == "Expense"]
                if HAS_PLOTLY and not expense_df.empty:
                    fig_pie = px.pie(
                        expense_df,
                        names="Category",
                        values="Amount",
                        hole=0.48,
                        color_discrete_sequence=["#bc8848", "#557b60", "#b85045", "#847263"],
                    )
                    fig_pie.update_traces(
                        textposition="inside",
                        textinfo="percent",
                        hovertemplate="%{label}<br>%{value:,.2f} ج.م (%{percent})<extra></extra>",
                    )
                    fig_pie.update_layout(
                        height=285,
                        margin=dict(l=8, r=8, t=12, b=8),
                        showlegend=True,
                        legend=dict(orientation="h", y=-0.12),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                elif expense_df.empty:
                    st.info("ستظهر المصروفات هنا بعد تسجيل أول مصروف.")
                else:
                    st.info("ثبّت Plotly لعرض الرسم البياني.")
    
        with chart_col2:
            with st.container(border=True):
                st.markdown("**الإيرادات والمصروفات شهرياً**")
                monthly_trend = (
                    analysis_df.groupby(["Year_Month", "Type"])["Amount"]
                    .sum()
                    .reset_index()
                )
                if HAS_PLOTLY and not monthly_trend.empty:
                    fig_bar = px.bar(
                        monthly_trend,
                        x="Year_Month",
                        y="Amount",
                        color="Type",
                        barmode="group",
                        color_discrete_map={"Income": "#557b60", "Expense": "#b85045"},
                        labels={"Year_Month": "الشهر", "Amount": "المبلغ (ج.م)", "Type": "النوع"},
                    )
                    fig_bar.update_traces(hovertemplate="%{y:,.2f} ج.م<extra></extra>")
                    fig_bar.update_layout(
                        height=285,
                        margin=dict(l=8, r=8, t=12, b=8),
                        legend_title_text="",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig_bar.update_yaxes(title_text="المبلغ (ج.م)", gridcolor="#e7e1d9")
                    st.plotly_chart(fig_bar, use_container_width=True)
                elif not HAS_PLOTLY:
                    st.info("ثبّت Plotly لعرض الرسم البياني.")
                else:
                    st.info("ستظهر المقارنة بعد تسجيل المعاملات.")
    
        pivot_df = analysis_df.pivot_table(
            index="Year_Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0,
        )
        for col in ["Income", "Expense"]:
            if col not in pivot_df.columns:
                pivot_df[col] = 0.0
    
        pivot_df["Net Profit"] = pivot_df["Income"] - pivot_df["Expense"]
        pivot_df = pivot_df.sort_index(ascending=False)
        summary = pivot_df.rename(
            columns={"Income": "إجمالي الإيرادات", "Expense": "إجمالي المصروفات"}
        )[["إجمالي الإيرادات", "إجمالي المصروفات", "Net Profit"]]
        summary = summary.rename_axis("الشهر").rename(columns={"Net Profit": "صافي الربح"})
        st.dataframe(
            summary.style.format({
                "إجمالي الإيرادات": "{:,.2f} ج.م",
                "إجمالي المصروفات": "{:,.2f} ج.م",
                "صافي الربح": "{:,.2f} ج.م",
            }),
            use_container_width=True,
        )
    else:
        st.info("سجّل أول قيد لعرض ملخص الإيرادات والمصروفات والرسوم.")
    
    st.markdown("---")
    
with tab_history:
    # =====================================================
    # 7. سجل المعاملات والبحث
    # =====================================================
    st.subheader("سجل المعاملات")
    
    if data_view.empty:
        st.info("لا توجد قيود مسجلة حتى الآن.")
    else:
        with st.expander("تصفية وبحث في القيود", expanded=False):
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                min_date = pd.to_datetime(data_view["Date"]).min().date()
                max_date = pd.to_datetime(data_view["Date"]).max().date()
                start_date = st.date_input(
                    "من تاريخ:",
                    value=min_date,
                    key="start_dt_tab1",
                )
            with filter_col2:
                end_date = st.date_input(
                    "إلى تاريخ:",
                    value=max_date,
                    key="end_dt_tab1",
                )
    
            filter_col3, filter_col4, filter_col5, filter_col6 = st.columns(4)
            with filter_col3:
                filter_type = st.selectbox(
                    "نوع المعاملة:",
                    ["All", "Income", "Expense"],
                    format_func=lambda value: {
                        "All": "الكل",
                        "Income": "إيراد",
                        "Expense": "مصروف",
                    }[value],
                    key="flt_type_t1",
                )
            with filter_col4:
                all_categories = ["All"] + list(data_view["Category"].unique())
                filter_category = st.selectbox(
                    "البند:",
                    all_categories,
                    format_func=lambda value: "الكل" if value == "All" else value,
                    key="flt_cat_t1",
                )
            with filter_col5:
                search_description = st.text_input(
                    "بحث في البيان:",
                    key="search_desc_t1",
                )
            with filter_col6:
                branch_filter = st.selectbox(
                    "الفرع:",
                    ["All"] + BRANCHES,
                    format_func=lambda value: "الكل" if value == "All" else value,
                    key="flt_branch_t1",
                )
    
        filtered_df = data_view.copy()
        filtered_df["Parsed_Date_Obj"] = pd.to_datetime(
            filtered_df["Date"], errors="coerce"
        ).dt.date
        filtered_df = filtered_df[
            (filtered_df["Parsed_Date_Obj"] >= start_date)
            & (filtered_df["Parsed_Date_Obj"] <= end_date)
        ]
        if filter_type != "All":
            filtered_df = filtered_df[filtered_df["Type"] == filter_type]
        if filter_category != "All":
            filtered_df = filtered_df[filtered_df["Category"] == filter_category]
        if branch_filter != "All":
            filtered_df = filtered_df[filtered_df["Branch"] == branch_filter]
        if search_description.strip():
            filtered_df = filtered_df[
                filtered_df["Description"].str.contains(
                    search_description,
                    case=False,
                    na=False,
                )
            ]
    
        csv_data = (
            filtered_df.drop(columns=["Parsed_Date_Obj"])
            .to_csv(index=False)
            .encode("utf-8-sig")
        )
        st.download_button(
            label="تنزيل القيود المعروضة بصيغة CSV",
            data=csv_data,
            file_name=f"onespot_transactions_{start_date}_to_{end_date}.csv",
            mime="text/csv",
        )
    
        def show_branch_transactions(branch_frame, branch_name):
            st.markdown(f"#### {branch_name}")
            if branch_frame.empty:
                st.info(f"لا توجد قيود مطابقة لفرع {branch_name}.")
                return

            display_df = branch_frame.sort_values("ID", ascending=False).copy()
            display_df["Amount"] = display_df["Amount"].map(format_currency)
            display_df = display_df.rename(columns={
                "ID": "رقم القيد",
                "Date": "التاريخ",
                "Branch": "الفرع",
                "Category": "البند",
                "Type": "النوع",
                "Amount": "المبلغ",
                "Description": "البيان",
            })
            display_df["النوع"] = display_df["النوع"].map({
                "Income": "إيراد",
                "Expense": "مصروف",
            })
            display_df = display_df.drop(
                columns=["Month_No", "Parsed_Date_Obj"], errors="ignore"
            )
            st.dataframe(
                display_df.head(10),
                use_container_width=True,
                hide_index=True,
            )
            if len(display_df) > 10:
                st.caption("يعرض الجدول أحدث 10 قيود لهذا الفرع. استخدم البحث أو تنزيل CSV لبقية النتائج.")

        branches_to_show = BRANCHES if branch_filter == "All" else [branch_filter]
        for branch_name in branches_to_show:
            branch_frame = filtered_df[filtered_df["Branch"] == branch_name]
            show_branch_transactions(branch_frame, branch_name)
    
with tab_admin:
    st.subheader("نسخة احتياطية للقيود")
    if data_view.empty:
        st.info("لا توجد قيود لإنشاء نسخة احتياطية منها.")
    else:
        backup_df = data_view[COLUMNS].copy()
        backup_df["Type"] = backup_df["Type"].map({"Income": "إيراد", "Expense": "مصروف"})
        backup_df = backup_df.rename(columns={
            "ID": "رقم القيد",
            "Date": "التاريخ",
            "Month_No": "رقم الشهر",
            "Branch": "الفرع",
            "Category": "البند",
            "Type": "النوع",
            "Amount": "المبلغ (ج.م)",
            "Description": "البيان",
        })
        backup_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_csv = backup_df.to_csv(index=False).encode("utf-8-sig")
        backup_buffer = BytesIO()
        with pd.ExcelWriter(backup_buffer, engine="openpyxl") as writer:
            backup_df.to_excel(writer, index=False, sheet_name="القيود")
        backup_left, backup_right = st.columns(2)
        backup_left.download_button(
            "تنزيل نسخة احتياطية Excel",
            data=backup_buffer.getvalue(),
            file_name=f"onespot_backup_{backup_stamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        backup_right.download_button(
            "تنزيل نسخة احتياطية CSV",
            data=backup_csv,
            file_name=f"onespot_backup_{backup_stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("نزّل نسخة احتياطية قبل حذف قيد، واحتفظ بها على جهازك.")

    with st.expander("تعديل قيد", expanded=False):
        if data_view.empty:
            st.info("لا توجد قيود متاحة للتعديل.")
        else:
            edit_options = {
                int(row["ID"]): (
                    f"رقم {int(row['ID'])} | {row['Date']} | {row['Branch']} | "
                    f"{format_currency(row['Amount'])} | {str(row['Description'])[:40]}"
                )
                for _, row in data_view.sort_values("ID", ascending=False).iterrows()
            }
            edit_id = st.selectbox(
                "اختر القيد:",
                options=[None] + list(edit_options),
                format_func=lambda value: "-- اختر القيد --" if value is None else edit_options[value],
                key="edit_transaction_id",
            )
            if edit_id is not None:
                old_row = data_view.loc[data_view["ID"] == edit_id].iloc[0]
                with st.form("edit_transaction_form"):
                    edit_cols = st.columns([.9, .9, 1.1, .9, 1.7])
                    with edit_cols[0]:
                        edit_type = st.selectbox(
                            "النوع:", ["Income", "Expense"],
                            index=0 if old_row["Type"] == "Income" else 1,
                            format_func=lambda value: "إيراد" if value == "Income" else "مصروف",
                        )
                    with edit_cols[1]:
                        edit_branch = st.selectbox(
                            "الفرع:", BRANCHES,
                            index=BRANCHES.index(old_row["Branch"]) if old_row["Branch"] in BRANCHES else 0,
                        )
                    with edit_cols[2]:
                        edit_date = st.date_input("التاريخ:", value=pd.to_datetime(old_row["Date"]).date())
                    with edit_cols[3]:
                        all_categories = INCOME_CATS + EXPENSE_CATS
                        current_category = old_row["Category"]
                        category_options = list(dict.fromkeys(all_categories + [current_category]))
                        edit_category = st.selectbox(
                            "البند:", category_options,
                            index=category_options.index(current_category),
                        )
                    with edit_cols[4]:
                        edit_amount = st.number_input(
                            "المبلغ (ج.م):", min_value=0.0,
                            value=float(old_row["Amount"]), step=10.0, format="%.2f",
                        )
                    edit_description = st.text_input("البيان:", value=str(old_row["Description"]))
                    edit_submitted = st.form_submit_button("حفظ التعديل", type="primary")

                if edit_submitted:
                    if edit_amount <= 0 or not edit_description.strip():
                        st.error("أدخل مبلغًا أكبر من صفر وبيانًا للقيد.")
                    else:
                        latest_df, latest_error = load_data()
                        if latest_error:
                            st.error("تعذر تحميل القيود: " + latest_error)
                        elif edit_id not in latest_df["ID"].values:
                            st.error("القيد غير موجود. حدّث الصفحة وجرب مرة أخرى.")
                        else:
                            edited_df = latest_df.copy()
                            mask = edited_df["ID"] == edit_id
                            edited_df.loc[mask, "Date"] = edit_date.strftime("%Y-%m-%d")
                            edited_df.loc[mask, "Month_No"] = edit_date.month
                            edited_df.loc[mask, "Branch"] = edit_branch
                            edited_df.loc[mask, "Category"] = edit_category
                            edited_df.loc[mask, "Type"] = edit_type
                            edited_df.loc[mask, "Amount"] = float(edit_amount)
                            edited_df.loc[mask, "Description"] = edit_description.strip()
                            try:
                                save_data(edited_df)
                                st.success(f"تم تعديل القيد رقم {edit_id}.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"تعذر حفظ التعديل: {exc}")

    # =====================================================
    # 8. حذف القيود
    # =====================================================
    with st.expander("مسح القيد", expanded=True):
        if data_blocked:
            st.error("الحذف متوقف حتى إصلاح مشكلة ملف البيانات.")
        elif data_view.empty:
            st.info("لا توجد قيود متاحة للحذف.")
        else:
            delete_df = data_view.sort_values("ID", ascending=False).copy()
            delete_options = {
                int(row["ID"]): (
                    f"رقم {int(row['ID'])} | {row['Date']} | "
                f"{row['Branch']} | "
                    f"{'إيراد' if row['Type'] == 'Income' else 'مصروف'} | "
                    f"{format_currency(row['Amount'])} | "
                    f"{str(row['Description'])[:40]}"
                )
                for _, row in delete_df.iterrows()
            }
            selected_id = st.selectbox(
                "اختر القيد الذي تريد حذفه:",
                options=[None] + list(delete_options.keys()),
                format_func=lambda value: (
                    "-- اختر القيد --" if value is None else delete_options[value]
                ),
                key="tab_del_select",
            )
    
            if selected_id is not None:
                selected_rows = data_view.loc[data_view["ID"] == selected_id]
                if not selected_rows.empty:
                    row = selected_rows.iloc[0]
                    st.warning(
                        f"القيد المحدد: رقم {int(row['ID'])} | {row['Date']} | "
                    f"{row['Branch']} | "
                        f"{'إيراد' if row['Type'] == 'Income' else 'مصروف'} | "
                        f"{format_currency(row['Amount'])} | {row['Description']}"
                    )
                    confirm_delete = st.checkbox(
                        "أؤكد أنني أريد حذف هذا القيد نهائيًا.",
                        key=f"confirm_delete_{selected_id}",
                    )
                    if st.button(
                        "تأكيد حذف القيد",
                        type="primary",
                        disabled=not confirm_delete,
                        key=f"delete_btn_{selected_id}",
                    ):
                        latest_df, latest_error = load_data()
                        if latest_error:
                            st.error("تم إيقاف الحذف لحماية البيانات: " + latest_error)
                        elif selected_id not in latest_df["ID"].values:
                            st.error("القيد غير موجود في الملف الحالي. أعد تحميل الصفحة.")
                        else:
                            updated_df = latest_df.loc[
                                latest_df["ID"] != selected_id
                            ].copy()
                            try:
                                save_data(updated_df)
                                st.success(
                                    f"تم حذف القيد رقم {selected_id} وتحديث البيانات."
                                )
                                st.rerun()
                            except Exception as exc:
                                st.error(f"تعذر إكمال الحذف والحفظ. التفاصيل: {exc}")

    with st.expander("سجل تعديلات القيود", expanded=False):
        try:
            audit_df = load_transaction_audit()
            if audit_df.empty:
                st.info("ستظهر هنا عمليات إضافة القيود أو تعديلها أو حذفها.")
            else:
                audit_view = audit_df.rename(columns={
                    "occurred_at": "وقت العملية",
                    "actor": "المستخدم",
                    "action": "العملية",
                    "transaction_id": "رقم القيد",
                    "transaction_date": "تاريخ القيد",
                    "branch": "الفرع",
                    "category": "البند",
                    "transaction_type": "النوع",
                    "amount": "المبلغ (ج.م)",
                    "description": "البيان",
                }).copy()
                if "النوع" in audit_view.columns:
                    audit_view["النوع"] = audit_view["النوع"].map({"Income": "إيراد", "Expense": "مصروف"})
                st.dataframe(audit_view, use_container_width=True, hide_index=True)
                st.download_button(
                    "تنزيل سجل التعديلات CSV",
                    data=audit_view.to_csv(index=False).encode("utf-8-sig"),
                    file_name="onespot_transaction_audit.csv",
                    mime="text/csv",
                )
        except Exception as exc:
            st.warning(f"تعذر تحميل سجل التعديلات: {exc}")

with tab_reports:
    st.subheader("مقارنة الفروع والتقرير الشهري")
    if data_view.empty:
        st.info("سجّل قيودًا لتظهر مقارنة الفروع والتقارير هنا.")
    else:
        report_view = data_view.copy()
        report_view["Amount"] = pd.to_numeric(report_view["Amount"], errors="coerce").fillna(0)
        report_view["Parsed_Date"] = pd.to_datetime(report_view["Date"], errors="coerce")
        report_view["Year_Month"] = report_view["Parsed_Date"].dt.strftime("%Y-%m")
        report_months = sorted(report_view["Year_Month"].dropna().unique(), reverse=True)
        chosen_month = st.selectbox(
            "اختاري الشهر للتقرير:",
            ["كل الشهور"] + report_months,
            key="branch_report_month",
        )
        if chosen_month != "كل الشهور":
            report_view = report_view[report_view["Year_Month"] == chosen_month].copy()

        comparison_rows = []
        for branch_name in BRANCHES:
            branch_data = report_view[report_view["Branch"] == branch_name]
            branch_income = branch_data.loc[branch_data["Type"] == "Income", "Amount"].sum()
            branch_expense = branch_data.loc[branch_data["Type"] == "Expense", "Amount"].sum()
            comparison_rows.append({
                "الفرع": branch_name,
                "الإيرادات": branch_income,
                "المصروفات": branch_expense,
                "صافي الربح": branch_income - branch_expense,
                "عدد القيود": len(branch_data),
            })

        comparison_total = {
            "الفرع": "إجمالي الفرعين",
            "الإيرادات": sum(row["الإيرادات"] for row in comparison_rows),
            "المصروفات": sum(row["المصروفات"] for row in comparison_rows),
            "صافي الربح": sum(row["صافي الربح"] for row in comparison_rows),
            "عدد القيود": sum(row["عدد القيود"] for row in comparison_rows),
        }
        comparison_rows.append(comparison_total)
        st.dataframe(
            pd.DataFrame(comparison_rows).style.format({
                "الإيرادات": "{:,.2f} ج.م",
                "المصروفات": "{:,.2f} ج.م",
                "صافي الربح": "{:,.2f} ج.م",
                "عدد القيود": "{:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### تنبيه عند تجاوز مصروفات الفرع")
        alert_columns = st.columns(len(BRANCHES))
        for alert_column, branch_name in zip(alert_columns, BRANCHES):
            branch_expenses = next(
                row["المصروفات"] for row in comparison_rows if row["الفرع"] == branch_name
            )
            with alert_column:
                expense_limit = st.number_input(
                    f"حد المصروفات لـ {branch_name} (ج.م):",
                    min_value=0.0,
                    value=0.0,
                    step=500.0,
                    key=f"expense_alert_{branch_name}",
                )
                if expense_limit > 0 and branch_expenses > expense_limit:
                    st.warning(
                        f"مصروفات {branch_name} تجاوزت الحد المحدد لهذا الشهر."
                    )

        if HAS_PLOTLY and not report_view.empty:
            comparison_chart_data = (
                report_view.groupby(["Branch", "Type"])["Amount"].sum().reset_index()
            )
            comparison_chart = px.bar(
                comparison_chart_data,
                x="Branch",
                y="Amount",
                color="Type",
                barmode="group",
                color_discrete_map={"Income": "#557b60", "Expense": "#b85045"},
                labels={"Branch": "الفرع", "Amount": "المبلغ (ج.م)", "Type": "النوع"},
            )
            comparison_chart.update_layout(
                height=360,
                margin=dict(l=12, r=12, t=20, b=12),
                legend_title_text="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            comparison_chart.update_traces(hovertemplate="%{y:,.2f} ج.م<extra></extra>")
            st.plotly_chart(comparison_chart, use_container_width=True)

        export_df = report_view.drop(columns=["Month_No", "Parsed_Date", "Year_Month"], errors="ignore")
        export_df = export_df.rename(columns={
            "ID": "رقم القيد",
            "Date": "التاريخ",
            "Branch": "الفرع",
            "Category": "البند",
            "Type": "النوع",
            "Amount": "المبلغ بالجنيه",
            "Description": "البيان",
        })
        export_df["النوع"] = export_df["النوع"].map({"Income": "إيراد", "Expense": "مصروف"})
        st.download_button(
            "تنزيل التقرير بصيغة CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"onespot_branch_report_{chosen_month.replace(' ', '_')}.csv",
            mime="text/csv",
        )

    with st.expander("مصروفات شهرية متكررة", expanded=False):
        st.caption("أضف الإيجار أو الرواتب أو غيرها مرة واحدة؛ سيذكّرك النظام بها كل شهر. لا يُسجَّل المصروف إلا عند ضغطك على زر التسجيل.")
        recurring_engine = get_database_engine()
        if recurring_engine is None:
            st.info("المصروفات المتكررة تحتاج اتصال Neon حتى تُحفظ إعداداتها.")
        else:
            try:
                from sqlalchemy import text

                ensure_database(recurring_engine)
                with st.form("recurring_expense_form"):
                    recurring_cols = st.columns([1, 1.4, .9, .7, 1.6])
                    with recurring_cols[0]:
                        recurring_branch = st.selectbox("الفرع", BRANCHES, key="rec_branch")
                    with recurring_cols[1]:
                        recurring_category = st.selectbox("البند", EXPENSE_CATS, key="rec_category")
                    with recurring_cols[2]:
                        recurring_amount = st.number_input("المبلغ (ج.م)", min_value=0.0, step=100.0, key="rec_amount")
                    with recurring_cols[3]:
                        recurring_due_day = st.number_input("يوم الاستحقاق", min_value=1, max_value=28, value=1, step=1, key="rec_due_day")
                    with recurring_cols[4]:
                        recurring_description = st.text_input("البيان", key="rec_description")
                    recurring_submitted = st.form_submit_button("إضافة مصروف متكرر", use_container_width=True)

                if recurring_submitted:
                    if recurring_amount <= 0 or not recurring_description.strip():
                        st.error("أدخل مبلغًا أكبر من صفر وبيانًا للمصروف.")
                    else:
                        with recurring_engine.begin() as connection:
                            connection.execute(text("""
                              INSERT INTO recurring_expenses (branch, category, amount, description, due_day)
                              VALUES (:branch, :category, :amount, :description, :due_day)
                            """), {
                                "branch": recurring_branch,
                                "category": recurring_category,
                                "amount": float(recurring_amount),
                                "description": recurring_description.strip(),
                                "due_day": int(recurring_due_day),
                            })
                        st.success("تمت إضافة المصروف المتكرر.")
                        st.rerun()

                recurring_df = pd.read_sql_query(text("""
                  SELECT id, branch, category, amount, description, due_day
                  FROM recurring_expenses WHERE active = TRUE ORDER BY id
                """), recurring_engine)
                if recurring_df.empty:
                    st.info("لم تضف مصروفات متكررة بعد.")
                else:
                    current_month = datetime.date.today().strftime("%Y-%m")
                    current_month_df = data_view.copy()
                    if not current_month_df.empty:
                        current_month_df["Parsed_Date"] = pd.to_datetime(current_month_df["Date"], errors="coerce")
                        current_month_df = current_month_df[
                            current_month_df["Parsed_Date"].dt.strftime("%Y-%m") == current_month
                        ]
                    st.markdown("#### استحقاق هذا الشهر")
                    for _, recurring in recurring_df.iterrows():
                        match = current_month_df[
                            (current_month_df["Branch"].astype(str) == str(recurring["branch"]))
                            & (current_month_df["Category"].astype(str) == str(recurring["category"]))
                            & (pd.to_numeric(current_month_df["Amount"], errors="coerce").round(2) == round(float(recurring["amount"]), 2))
                            & (current_month_df["Description"].fillna("").astype(str).str.strip().str.casefold() == str(recurring["description"]).strip().casefold())
                            & (current_month_df["Type"] == "Expense")
                        ]
                        item_label = f"{recurring['branch']} · {recurring['description']} · {format_currency(recurring['amount'])} · يوم {int(recurring['due_day'])}"
                        item_cols = st.columns([3, 1])
                        with item_cols[0]:
                            if not match.empty:
                                st.success(f"تم تسجيله هذا الشهر: {item_label}")
                            else:
                                st.warning(f"لم يُسجل بعد: {item_label}")
                        with item_cols[1]:
                            if match.empty and st.button("تسجيل المصروف", key=f"recurring_post_{int(recurring['id'])}", use_container_width=True):
                                try:
                                    due_date = datetime.date.today().replace(day=int(recurring["due_day"]))
                                    latest_df, latest_error = load_data()
                                    if latest_error:
                                        st.error("تعذر تحميل القيود: " + latest_error)
                                    else:
                                        next_id = int(latest_df["ID"].max()) + 1 if not latest_df.empty else 1
                                        new_expense = pd.DataFrame([{
                                            "ID": next_id,
                                            "Date": due_date.strftime("%Y-%m-%d"),
                                            "Month_No": due_date.month,
                                            "Branch": recurring["branch"],
                                            "Category": recurring["category"],
                                            "Type": "Expense",
                                            "Amount": float(recurring["amount"]),
                                            "Description": recurring["description"],
                                        }])
                                        save_data(pd.concat([latest_df, new_expense], ignore_index=True))
                                        st.success("تم تسجيل المصروف في سجل القيود.")
                                        st.rerun()
                                except Exception as exc:
                                    st.error(f"تعذر تسجيل المصروف المتكرر: {exc}")

                    st.markdown("#### إدارة المصروفات المتكررة")
                    recurring_options = {
                        int(row["id"]): f"{row['branch']} | {row['description']} | {format_currency(row['amount'])}"
                        for _, row in recurring_df.iterrows()
                    }
                    selected_recurring_id = st.selectbox(
                        "اختار مصروفًا لإيقاف تكراره:",
                        options=[None] + list(recurring_options),
                        format_func=lambda value: "-- اختر --" if value is None else recurring_options[value],
                        key="recurring_delete_select",
                    )
                    if selected_recurring_id is not None and st.button("إيقاف هذا المصروف المتكرر", key="recurring_deactivate"):
                        from sqlalchemy import text
                        with recurring_engine.begin() as connection:
                            connection.execute(text("UPDATE recurring_expenses SET active = FALSE WHERE id = :id"), {"id": int(selected_recurring_id)})
                        st.success("تم إيقاف تكرار المصروف؛ القيود المسجلة لا تتأثر.")
                        st.rerun()
            except Exception as exc:
                st.warning(f"تعذر تحميل المصروفات المتكررة من Neon: {exc}")

with tab_attendance:
    st.subheader("الحضور والانصراف — فريق OneSpot")
    st.caption(
        "ارفع ملف الحضور بصيغة Excel لعرض ساعات العمل والسلف لكل موظف. "
        "سيتم جمع الموظفين معًا تحت OneSpot لأن مواقع عملهم متغيرة. "
        "ملف Excel نفسه لا يُحفظ. السجلات الجديدة فقط تُحفظ في Neon للمتابعة، "
        "والتاريخ المكرر للموظف نفسه يتم تخطيه."
    )

    attendance_file = st.file_uploader(
        "اختار ملف الحضور والانصراف (.xlsm أو .xlsx)",
        type=["xlsm", "xlsx"],
        key="attendance_workbook_upload",
        help="يتم قراءة أوراق الموظفين فقط، وتجاهل ورقة Summary حتى لا تتكرر البيانات.",
    )

    if attendance_file is not None:
        with st.status("جاري تجهيز ملف الحضور والانصراف...", expanded=True) as upload_status:
            try:
                upload_status.write("📂 قراءة أوراق الموظفين وبيانات الحضور...")
                attendance_rows, ignored_sheets = read_attendance_excel(attendance_file)
                upload_status.write("🔎 مراجعة التواريخ وتخطي السجلات المكررة...")
                upload_status.write("💾 حفظ السجلات الجديدة في متابعة الموظفين...")
                imported_df = process_attendance_upload(
                    attendance_rows, attendance_file, ignored_sheets
                )
                upload_result = st.session_state.get("attendance_upload_result", {})
                if imported_df is None:
                    upload_status.update(
                        label="لم يتم العثور على سجلات حضور صالحة",
                        state="error",
                        expanded=True,
                    )
                elif upload_result.get("error"):
                    upload_status.update(
                        label="تمت قراءة الملف، لكن تعذر حفظ السجلات في Neon",
                        state="error",
                        expanded=True,
                    )
                else:
                    upload_status.update(
                        label=(
                            f"اكتمل تحميل الملف — أُضيف {upload_result.get('inserted', 0)} "
                            f"وتُحدّث {upload_result.get('updated', 0)} سجل"
                        ),
                        state="complete",
                        expanded=False,
                    )
            except Exception as exc:
                upload_status.update(
                    label="تعذر قراءة الملف أو حفظ بياناته",
                    state="error",
                    expanded=True,
                )
                st.error(f"تأكد أن ملف Excel سليم ثم ارفعه مرة أخرى. التفاصيل: {exc}")

    attendance_df = st.session_state.get("attendance_imported_df")
    if attendance_df is not None and not attendance_df.empty:
        monthly_hours_target = 234.0
        month_values = sorted(attendance_df["التاريخ"].dt.strftime("%Y-%m").unique(), reverse=True)
        selected_attendance_month = st.selectbox(
            "الشهر:", ["كل الشهور"] + month_values, key="attendance_month_filter"
        )
        attendance_view = attendance_df.copy()
        if selected_attendance_month != "كل الشهور":
            attendance_view = attendance_view[
                attendance_view["التاريخ"].dt.strftime("%Y-%m") == selected_attendance_month
            ]

        total_hours = attendance_view["ساعات العمل"].sum()
        total_advances = attendance_view["السلفة (ج.م)"].sum()
        employees_count = attendance_view["الموظف"].nunique()
        attendance_view["يوم حضور"] = attendance_day_mask(attendance_view)
        worked_days = int(attendance_view["يوم حضور"].sum())
        metric_cols = st.columns(4)
        metric_cols[0].metric("عدد الموظفين", f"{employees_count}")
        metric_cols[1].metric("إجمالي ساعات العمل", f"{total_hours:,.2f} ساعة")
        metric_cols[2].metric("أيام العمل المسجلة", f"{worked_days}")
        metric_cols[3].metric("إجمالي السلف", format_currency(total_advances))

        attendance_view = attendance_view.copy()
        attendance_view["الشهر المحسوب"] = attendance_view["التاريخ"].dt.strftime("%Y-%m")
        monthly_employee_summary = attendance_view.groupby(
            ["الموظف", "الشهر المحسوب"], as_index=False
        ).agg(
            **{"أيام العمل": ("يوم حضور", "sum"),
               "إجمالي الساعات": ("ساعات العمل", "sum"),
               "إجمالي السلف (ج.م)": ("السلفة (ج.م)", "sum")}
        )
        employee_summary = monthly_employee_summary.groupby("الموظف", as_index=False).agg(
            **{"عدد الشهور": ("الشهر المحسوب", "nunique"),
               "أيام العمل": ("أيام العمل", "sum"),
               "إجمالي الساعات": ("إجمالي الساعات", "sum"),
               "إجمالي السلف (ج.م)": ("إجمالي السلف (ج.م)", "sum")}
        )
        employee_summary["الساعات المستهدفة"] = (
            employee_summary["عدد الشهور"] * monthly_hours_target
        )
        employee_summary["الفرق عن المستهدف"] = (
            employee_summary["إجمالي الساعات"] - employee_summary["الساعات المستهدفة"]
        )
        employee_summary["الحالة"] = employee_summary["الفرق عن المستهدف"].apply(
            lambda difference: "مكتمل" if abs(difference) < 0.01
            else ("أعلى من المستهدف" if difference > 0 else "أقل من المستهدف")
        )
        employee_summary = employee_summary[
            ["الموظف", "عدد الشهور", "أيام العمل", "إجمالي الساعات",
             "الساعات المستهدفة", "الفرق عن المستهدف", "الحالة", "إجمالي السلف (ج.م)"]
        ]
        st.markdown("#### ملخص الموظفين")
        st.caption(
            f"المستهدف {monthly_hours_target:,.0f} ساعة لكل موظف عن كل شهر ظاهر له في الملف. "
            "ملف الحضور للعرض المؤقت فقط ولا يُحفظ في Neon."
        )
        st.dataframe(
            employee_summary.style.format({
                "عدد الشهور": "{:,.0f}",
                "أيام العمل": "{:,.0f}",
                "إجمالي الساعات": "{:,.2f}",
                "الساعات المستهدفة": "{:,.2f}",
                "الفرق عن المستهدف": "{:+,.2f}",
                "إجمالي السلف (ج.م)": "{:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("#### تفاصيل الحضور والانصراف")
        display_df = attendance_view.rename(columns={"التاريخ": "التاريخ"}).copy()
        display_df["التاريخ"] = display_df["التاريخ"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            display_df[["الموظف", "التاريخ", "اليوم", "الحضور", "الانصراف", "ساعات العمل", "السلفة (ج.م)", "الفريق"]],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "تنزيل بيانات الحضور كملف CSV",
            data=attendance_view.assign(**{"التاريخ": attendance_view["التاريخ"].dt.strftime("%Y-%m-%d")}).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"onespot_attendance_{selected_attendance_month.replace(' ', '_')}.csv",
            mime="text/csv",
        )

with tab_employee_tracking:
    st.subheader("متابعة الموظفين — OneSpot")
    st.caption(
        "كل ما ترفعه في تبويب الحضور والانصراف يظهر هنا محفوظًا في Neon. "
        "يتم الاحتفاظ بسجل واحد لكل موظف في كل تاريخ؛ السجلات الجديدة تُضاف "
        "والتغييرات على تاريخ موجود تُحدّث السجل نفسه."
    )
    try:
        tracking_df = load_employee_attendance()
    except Exception as exc:
        tracking_df = None
        st.error(f"تعذر تحميل متابعة الموظفين من Neon: {exc}")

    if tracking_df is None:
        st.warning("متابعة الموظفين تحتاج اتصال Neon. البيانات لم تُحفظ محليًا.")
    elif tracking_df.empty:
        st.info("لا توجد سجلات محفوظة بعد. ارفع ملف Excel من تبويب الحضور والانصراف لإضافة السجلات الجديدة.")
    else:
        monthly_hours_target = 234.0
        tracking_months = sorted(
            tracking_df["التاريخ"].dt.strftime("%Y-%m").dropna().unique(), reverse=True
        )

        # Keep the two archive tables left-to-right while preserving Arabic text direction.
        st.markdown("""
        <style>
          .onespot-ltr-table { direction:ltr; width:100%; overflow-x:auto; border:1px solid #e7ddd2; border-radius:10px; background:#fffdfa; }
          .onespot-ltr-table table { direction:ltr; width:100%; border-collapse:collapse; font-family:"Segoe UI",Tahoma,Arial,sans-serif; font-size:12px; color:#2d2924; background:#fffdfa; }
          .onespot-ltr-table th { padding:11px 12px; text-align:left; white-space:nowrap; background:#f7f8fa; color:#74665b; font-size:11px; font-weight:500; border-bottom:1px solid #e7ddd2; }
          .onespot-ltr-table td { padding:10px 12px; text-align:left; white-space:nowrap; border-bottom:1px solid #eee9e3; background:#fffdfa; }
          .onespot-ltr-table tbody tr:last-child td { border-bottom:0; }
          .onespot-ltr-table tbody tr:hover td { background:#fbf8f4; }
          .onespot-status-pill { display:inline-block; border-radius:999px; padding:5px 11px; font-size:12px; font-weight:600; white-space:nowrap; }
        </style>
        """, unsafe_allow_html=True)

        # 1) Employee summary at the top.
        st.markdown("### ملخص الموظفين")
        selected_tracking_month = st.selectbox(
            "الشهر:", ["كل الشهور"] + tracking_months,
            key="employee_tracking_month_filter",
        )
        tracking_view = tracking_df.copy()
        if selected_tracking_month != "كل الشهور":
            tracking_view = tracking_view[
                tracking_view["التاريخ"].dt.strftime("%Y-%m") == selected_tracking_month
            ]

        total_tracking_hours = tracking_view["ساعات العمل"].sum()
        total_tracking_advances = tracking_view["السلفة (ج.م)"].sum()
        tracking_employee_count = tracking_view["الموظف"].nunique()
        tracking_view["يوم حضور"] = attendance_day_mask(tracking_view)
        tracking_worked_days = int(tracking_view["يوم حضور"].sum())
        tracking_metrics = st.columns(4)
        tracking_metrics[0].metric("عدد الموظفين", f"{tracking_employee_count}")
        tracking_metrics[1].metric("إجمالي ساعات العمل", f"{total_tracking_hours:,.2f} ساعة")
        tracking_metrics[2].metric("أيام العمل المسجلة", f"{tracking_worked_days}")
        tracking_metrics[3].metric("إجمالي السلف", format_currency(total_tracking_advances))

        tracking_view["الشهر المحسوب"] = tracking_view["التاريخ"].dt.strftime("%Y-%m")
        monthly_tracking_summary = tracking_view.groupby(
            ["الموظف", "الشهر المحسوب"], as_index=False
        ).agg(
            **{"أيام العمل": ("يوم حضور", "sum"),
               "إجمالي الساعات": ("ساعات العمل", "sum"),
               "إجمالي السلف (ج.م)": ("السلفة (ج.م)", "sum")}
        )
        tracking_summary = monthly_tracking_summary.groupby("الموظف", as_index=False).agg(
            **{"عدد الشهور": ("الشهر المحسوب", "nunique"),
               "أيام العمل": ("أيام العمل", "sum"),
               "إجمالي الساعات": ("إجمالي الساعات", "sum"),
               "إجمالي السلف (ج.م)": ("إجمالي السلف (ج.م)", "sum")}
        )
        tracking_summary["الساعات المستهدفة"] = (
            tracking_summary["عدد الشهور"] * monthly_hours_target
        )
        tracking_summary["الفرق عن المستهدف"] = (
            tracking_summary["إجمالي الساعات"] - tracking_summary["الساعات المستهدفة"]
        )
        tracking_summary["الحالة"] = tracking_summary["الفرق عن المستهدف"].apply(
            lambda difference: "مكتمل" if abs(difference) < 0.01
            else ("أعلى من المستهدف" if difference > 0 else "أقل من المستهدف")
        )
        tracking_summary = tracking_summary[
            ["الموظف", "عدد الشهور", "أيام العمل", "إجمالي الساعات",
             "الساعات المستهدفة", "الفرق عن المستهدف", "الحالة", "إجمالي السلف (ج.م)"]
        ]
        st.caption("المستهدف 234 ساعة لكل موظف عن كل شهر ظاهر في السجلات.")

        def render_ltr_table(frame, number_columns=()):
            headers = "".join(f"<th>{html.escape(str(column))}</th>" for column in frame.columns)
            body_rows = []
            for row in frame.to_dict("records"):
                cells = []
                for column, value in row.items():
                    if value is None or pd.isna(value):
                        shown = "—"
                    elif column in number_columns:
                        shown = f"{float(value):,.2f}"
                    else:
                        shown = str(value)
                    escaped = html.escape(shown)
                    if column == "الحالة":
                        if "OFF" in shown.upper() or "أعلى من المستهدف" in shown:
                            pill_style = "background:#f6eddc;color:#8b612e;"
                        elif "حضور" in shown or shown == "مكتمل":
                            pill_style = "background:#e7f1ea;color:#367454;"
                        else:
                            pill_style = "background:#f6e9e6;color:#a84f45;"
                        escaped = (
                            f"<span class='onespot-status-pill' style='{pill_style}'>"
                            f"{escaped}</span>"
                        )
                    cells.append(f"<td dir='auto'>{escaped}</td>")
                body_rows.append("<tr>" + "".join(cells) + "</tr>")
            return (
                "<div class='onespot-ltr-table'><table><thead><tr>" + headers
                + "</tr></thead><tbody>" + "".join(body_rows)
                + "</tbody></table></div>"
            )

        summary_display = tracking_summary.copy()
        for numeric_column in ["إجمالي الساعات", "الساعات المستهدفة", "الفرق عن المستهدف", "إجمالي السلف (ج.م)"]:
            summary_display[numeric_column] = summary_display[numeric_column].map(
                lambda value: f"{float(value):+,.2f}" if numeric_column == "الفرق عن المستهدف"
                else f"{float(value):,.2f}"
            )
        st.markdown(render_ltr_table(summary_display), unsafe_allow_html=True)

        # 2) Individual employee report.
        with st.container(key="employee_report_design"):
            st.markdown("""
            <style>
              .st-key-employee_report_design,
              .st-key-employee_report_design * {
                font-family:"Segoe UI",Tahoma,Arial,sans-serif !important;
              }
              .st-key-employee_report_design h3 {
                color:#2d2119 !important; font-size:22px !important; font-weight:700 !important;
              }
              .st-key-employee_report_design [data-testid="stSelectbox"] label {
                color:#74665b !important; font-size:12px !important; font-weight:500 !important;
              }
              .st-key-employee_report_design [data-baseweb="select"] > div {
                background:#fffdfa !important; border:1px solid #e5d9cc !important;
                border-radius:8px !important; min-height:42px !important;
              }
              .st-key-employee_report_design [data-testid="stMetric"] {
                background:#fffdfa !important; border:1px solid #e7ddd2 !important;
                border-radius:11px !important; padding:12px 14px !important; box-shadow:none !important;
              }
              .st-key-employee_report_design [data-testid="stMetricLabel"] {
                color:#74665b !important; font-size:11px !important;
              }
              .st-key-employee_report_design [data-testid="stMetricValue"] {
                color:#2d2119 !important; font-size:24px !important;
              }
            </style>
            """, unsafe_allow_html=True)
            st.markdown("### تقرير الموظف الشهري")
            st.caption("عرض الحضور والانصراف والإجازات يومًا بيوم.")
            report_cols = st.columns(2)
            report_employees = sorted(
                tracking_df["الموظف"].dropna().astype(str).str.strip().unique().tolist(),
                key=str.casefold,
            )
            selected_report_employee = report_cols[0].selectbox(
                "اختر الموظف:", report_employees, key="employee_monthly_report_employee"
            )
            month_names_ar = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
            ]
            selected_report_month = report_cols[1].selectbox(
                "اختر الشهر:", tracking_months,
                format_func=lambda value: (
                    f"{month_names_ar[int(value[5:7]) - 1]} {value[:4]}"
                ),
                key="employee_monthly_report_month",
            )

            report_rows = tracking_df[
                (tracking_df["الموظف"].astype(str).str.strip() == selected_report_employee)
                & (tracking_df["التاريخ"].dt.strftime("%Y-%m") == selected_report_month)
            ].copy()
            month_start = pd.Period(selected_report_month, freq="M").start_time.normalize()
            calendar = pd.DataFrame({
                "التاريخ": pd.date_range(month_start, periods=month_start.days_in_month, freq="D")
            })
            report_rows = calendar.merge(report_rows, on="التاريخ", how="left")
            weekday_ar = {
                0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
                4: "الجمعة", 5: "السبت", 6: "الأحد",
            }
            report_off_days = attendance_off_mask(report_rows)
            report_rows["اليوم"] = [
                "OFF" if is_off else weekday_ar[day.weekday()]
                for day, is_off in zip(report_rows["التاريخ"], report_off_days)
            ]
            report_rows["ساعات العمل"] = pd.to_numeric(
                report_rows["ساعات العمل"], errors="coerce"
            ).fillna(0.0)
            report_rows["السلفة (ج.م)"] = pd.to_numeric(
                report_rows["السلفة (ج.م)"], errors="coerce"
            ).fillna(0.0)
            report_rows["الحالة"] = report_rows.apply(attendance_status_for_row, axis=1)
            report_attended = int(report_rows["الحالة"].isin(["حضور", "حضور في يوم OFF"]).sum())
            report_off = int(report_rows["الحالة"].str.contains("OFF", case=False).sum())
            report_unrecorded = int(report_rows["الحالة"].eq("لا يوجد تسجيل").sum())
            report_hours = float(report_rows["ساعات العمل"].sum())
            report_metrics = st.columns(4)
            report_metrics[0].metric("أيام الحضور", f"{report_attended}")
            report_metrics[1].metric("أيام الإجازة (OFF)", f"{report_off}")
            report_metrics[2].metric("أيام بلا سجل", f"{report_unrecorded}")
            report_metrics[3].metric("إجمالي الساعات", f"{report_hours:,.2f}")
            report_display = report_rows[[
                "التاريخ", "اليوم", "الحالة", "الحضور", "الانصراف",
                "ساعات العمل", "السلفة (ج.م)",
            ]].copy()
            report_display["التاريخ"] = report_display["التاريخ"].dt.strftime("%Y-%m-%d")
            def safe_report_value(value):
                if value is None or pd.isna(value) or str(value).strip().lower() in {"none", "nan", "nat"}:
                    return "—"
                return html.escape(str(value))

            report_table_rows = []
            for record in report_display.to_dict("records"):
                status = str(record["الحالة"])
                if "OFF" in status.upper():
                    badge_style = "background:#f6eddc;color:#8b612e;"
                elif "حضور" in status:
                    badge_style = "background:#e7f1ea;color:#367454;"
                else:
                    badge_style = "background:#f6e9e6;color:#a84f45;"
                report_table_rows.append(
                    "<tr>"
                    f"<td>{safe_report_value(record['التاريخ'])}</td>"
                    f"<td>{safe_report_value(record['اليوم'])}</td>"
                    f"<td><span style='display:inline-block;border-radius:999px;padding:5px 11px;"
                    f"font-size:12px;font-weight:600;white-space:nowrap;{badge_style}'>"
                    f"{safe_report_value(status)}</span></td>"
                    f"<td>{safe_report_value(record['الحضور'])}</td>"
                    f"<td>{safe_report_value(record['الانصراف'])}</td>"
                    f"<td>{float(record['ساعات العمل'] or 0):,.2f}</td>"
                    f"<td>{float(record['السلفة (ج.م)'] or 0):,.2f}</td>"
                    "</tr>"
                )
            report_table_html = """
            <style>
              .onespot-monthly-report { direction:ltr; width:100%; overflow-x:auto; border:1px solid #e7ddd2; border-radius:10px; background:#fffdfa; }
              .onespot-monthly-report table { direction:ltr; width:100%; border-collapse:collapse; font-family:"Segoe UI",Tahoma,Arial,sans-serif; font-size:12px; color:#2d2924; background:#fffdfa; }
              .onespot-monthly-report th { padding:11px 12px; text-align:left; white-space:nowrap; background:#f7f8fa; color:#74665b; font-size:11px; font-weight:500; border-bottom:1px solid #e7ddd2; }
              .onespot-monthly-report td { padding:10px 12px; text-align:left; white-space:nowrap; border-bottom:1px solid #eee9e3; background:#fffdfa; }
              .onespot-monthly-report tbody tr:last-child td { border-bottom:0; }
              .onespot-monthly-report tbody tr:hover { background:#fbf8f4; }
              @media (max-width:700px) { .onespot-monthly-report table { min-width:760px; } }
            </style>
            <div class="onespot-monthly-report"><table>
              <thead><tr><th>التاريخ</th><th>اليوم</th><th>الحالة</th><th>الحضور</th><th>الانصراف</th><th>ساعات العمل</th><th>السلفة (ج.م)</th></tr></thead>
              <tbody>
            """ + "".join(report_table_rows) + """
              </tbody>
            </table></div>
            """
            st.markdown(report_table_html, unsafe_allow_html=True)
            st.markdown("""
            <div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;font-family:'Segoe UI',Tahoma,Arial,sans-serif;font-size:12px;color:#74665b;">
              <span><b style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#367454;margin-left:6px;"></b>حضور</span>
              <span><b style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#b98242;margin-left:6px;"></b>إجازة / OFF</span>
              <span><b style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#a84f45;margin-left:6px;"></b>لا يوجد تسجيل</span>
            </div>
            """, unsafe_allow_html=True)

        # 3) Full saved records at the bottom.
        with st.expander("عرض جميع السجلات المحفوظة", expanded=False):
            tracking_display = tracking_view.copy()
            tracking_display["التاريخ"] = tracking_display["التاريخ"].dt.strftime("%Y-%m-%d")
            saved_display = tracking_display[[
                "الموظف", "التاريخ", "اليوم", "الحالة", "الحضور", "الانصراف",
                "ساعات العمل", "السلفة (ج.م)", "الفريق",
            ]].copy()
            saved_display["الحالة"] = tracking_view.apply(attendance_status_for_row, axis=1).values
            for numeric_column in ["ساعات العمل", "السلفة (ج.م)"]:
                saved_display[numeric_column] = saved_display[numeric_column].map(
                    lambda value: f"{float(value):,.2f}"
                )
            st.markdown(render_ltr_table(saved_display), unsafe_allow_html=True)
            st.download_button(
                "تنزيل بيانات متابعة الموظفين كملف CSV",
                data=tracking_view.assign(
                    **{"التاريخ": tracking_view["التاريخ"].dt.strftime("%Y-%m-%d")}
                ).to_csv(index=False).encode("utf-8-sig"),
                file_name=f"onespot_employee_tracking_{selected_tracking_month.replace(' ', '_')}.csv",
                mime="text/csv",
                key="employee_tracking_download",
            )
    
