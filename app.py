"""
Data Redundancy Removal System
--------------------------------
Streamlit UI + MongoDB Atlas backend.
Detects duplicate records using SHA-256 content hashing
before storing them, so only unique records get saved.
"""

import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Data Dedup System", page_icon="🧹", layout="wide")

# MongoDB connection string comes from Streamlit secrets (never hardcode it)
MONGO_URI = st.secrets.get("MONGO_URI", "")
DB_NAME = "dedup_system"
COLLECTION_NAME = "records"


@st.cache_resource
def get_db_connection():
    """Create and cache a MongoDB connection across reruns."""
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # forces connection test
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        # Unique index on hash -> DB-level guarantee against duplicates
        collection.create_index("content_hash", unique=True)
        return collection
    except ConnectionFailure:
        return None


def generate_hash(data: dict) -> str:
    """
    Generate a stable SHA-256 hash from a record's content.
    Keys are sorted so {"a":1,"b":2} and {"b":2,"a":1} hash the same way.
    """
    normalized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def insert_record(collection, data: dict):
    """
    Try to insert a record. Returns (success: bool, message: str).
    Duplicate detection happens in TWO layers:
      1. App-level: we check the hash exists before inserting (fast feedback)
      2. DB-level: unique index blocks it even in race conditions
    """
    content_hash = generate_hash(data)

    existing = collection.find_one({"content_hash": content_hash})
    if existing:
        return False, "⚠️ Duplicate detected — this exact record already exists."

    doc = {
        "content_hash": content_hash,
        "data": data,
        "created_at": datetime.utcnow(),
    }
    try:
        collection.insert_one(doc)
        return True, "✅ Unique record saved successfully."
    except Exception as e:
        # Handles rare race-condition duplicates caught by the unique index
        return False, f"⚠️ Duplicate rejected at database level ({e})"


# ----------------------------
# UI
# ----------------------------
st.title("🧹 Data Redundancy Removal System")
st.caption("Duplicate records ko hash-based comparison se automatically block karta hai.")

collection = get_db_connection()

if collection is None:
    st.error(
        "❌ MongoDB se connect nahi ho paya. `.streamlit/secrets.toml` mein "
        "`MONGO_URI` set karo (local) ya Streamlit Cloud secrets mein add karo (deployed)."
    )
    st.stop()

tab1, tab2, tab3 = st.tabs(["➕ Add Record", "📤 Bulk Upload (CSV)", "📊 View Records"])

# ---- TAB 1: Manual single record entry ----
with tab1:
    st.subheader("Add a single record")
    with st.form("manual_entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            email = st.text_input("Email")
        with col2:
            phone = st.text_input("Phone")
            extra = st.text_input("Extra Field (optional)")

        submitted = st.form_submit_button("Check & Save")

        if submitted:
            if not name and not email and not phone:
                st.warning("Kam se kam ek field bharo.")
            else:
                record = {"name": name, "email": email, "phone": phone, "extra": extra}
                success, msg = insert_record(collection, record)
                if success:
                    st.success(msg)
                else:
                    st.warning(msg)

# ---- TAB 2: Bulk CSV upload with dedup ----
with tab2:
    st.subheader("Upload CSV — duplicates automatically skip ho jayenge")
    uploaded_file = st.file_uploader("CSV file choose karo", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview:", df.head())

        if st.button("Process & Deduplicate"):
            progress = st.progress(0)
            saved, skipped = 0, 0
            total = len(df)

            for i, row in enumerate(df.to_dict(orient="records")):
                success, _ = insert_record(collection, row)
                if success:
                    saved += 1
                else:
                    skipped += 1
                progress.progress((i + 1) / total)

            st.success(f"✅ {saved} unique records saved | ⚠️ {skipped} duplicates skipped")

# ---- TAB 3: View stored records ----
with tab3:
    st.subheader("Stored unique records")
    records = list(collection.find({}, {"_id": 0}).sort("created_at", -1).limit(200))
    if records:
        flat = [
            {**r["data"], "created_at": r["created_at"], "hash": r["content_hash"][:10] + "..."}
            for r in records
        ]
        st.dataframe(pd.DataFrame(flat), use_container_width=True)
        st.caption(f"Showing latest {len(records)} records")
    else:
        st.info("Abhi koi record store nahi hua hai.")
