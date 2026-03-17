import os
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables
load_dotenv()

# ===============================
# 🔐 GOOGLE / GEMINI API CONFIG
# ===============================
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY missing in .env file")

# ===============================
# 🗄️ FRONTEND → BACKEND DB STATE
# ===============================
_fe_db_state: Dict[str, str] = {}

REQUIRED_DB_KEYS = {
    "db_host",
    "db_user",
    "db_password",
    "db_name"
}


def store_fe_data(data: Dict[str, str]) -> None:
    missing = REQUIRED_DB_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing DB fields: {missing}")

    global _fe_db_state
    _fe_db_state = {
        "db_host": data["db_host"],
        "db_user": data["db_user"],
        "db_password": data["db_password"],
        "db_name": data["db_name"],
    }


def get_fe_data() -> Dict[str, str]:
    if not _fe_db_state:
        raise RuntimeError("Database not connected")
    return _fe_db_state.copy()
