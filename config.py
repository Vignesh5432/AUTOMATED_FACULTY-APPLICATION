import os

# ✅ Always points to the project root safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Absolute path to SQLite DB
DB_PATH = os.path.join(BASE_DIR, "database", "exam_management.db")

# ✅ Secret Key (unchanged)
SECRET_KEY = os.getenv("SECRET_KEY", "dev_fallback_key")
