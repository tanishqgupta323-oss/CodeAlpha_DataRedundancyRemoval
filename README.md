# CodeAlpha_DataRedundancyRemoval

**Task 1 — Cloud Computing Internship @ CodeAlpha**
A cloud-based system that detects and prevents duplicate data from entering a database, ensuring only unique, verified records are stored.

## 🔗 Live Demo
https://data-dedup-system.streamlit.app/

## 📌 Problem Statement
Design a system that identifies and classifies data as redundant or unique, validates new data against existing records, and ensures only verified, non-duplicate entries are appended to a cloud database.

## 🏗️ Architecture

```
User (Browser)
      │
      ▼
Streamlit UI (Add Record / Bulk Upload / View Records)
      │
      ▼
SHA-256 Hash Generation (content fingerprint)
      │
      ▼
Duplicate Check against MongoDB Atlas
      │
      ├── Unique  → Insert into database
      └── Duplicate → Reject with alert
```

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Logic / Backend | Python (hashlib, PyMongo) |
| Frontend / UI | Streamlit |
| Database | MongoDB Atlas (Free M0 Cluster) |
| Hosting | Streamlit Community Cloud |

## ✅ Key Features
- **Content-based hashing** (SHA-256) to fingerprint each record, so duplicates are detected regardless of field order.
- **Two-layer duplicate protection**: application-level check before insert, plus a MongoDB unique index as a database-level safeguard against race conditions.
- **Bulk CSV upload** with automatic deduplication and a summary of saved vs. skipped records.
- **Live record viewer** to inspect all unique entries stored in the cloud database.

## 🖥️ Running Locally

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with:
```toml
MONGO_URI = "your-mongodb-atlas-connection-string"
```

Then run:
```bash
streamlit run app.py
```

## ☁️ Cloud Computing Concepts Applied
- **DBaaS (Database as a Service)** — MongoDB Atlas for fully managed, scalable cloud storage.
- **PaaS (Platform as a Service)** — Streamlit Community Cloud for deployment without server management.
- **Data integrity & validation** — enforced at both the application and database layer.

## 👤 Author
**Tanishq Gupta**
Cloud Computing Intern @ CodeAlpha
