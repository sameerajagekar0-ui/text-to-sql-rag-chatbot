from langchain.sql_database import SQLDatabase
from sqlalchemy import create_engine, text
from typing import Dict, Tuple, List

from config import get_fe_data

# --------------------------------------------------
# GLOBAL DB INSTANCE (LangChain)
# --------------------------------------------------
_db_instance: SQLDatabase | None = None


# --------------------------------------------------
# GET LANGCHAIN DATABASE INSTANCE
# --------------------------------------------------
def get_database() -> SQLDatabase:
    global _db_instance

    if _db_instance is not None:
        return _db_instance

    cfg = get_fe_data()

    uri = (
        f"mysql+pymysql://{cfg['db_user']}:{cfg['db_password']}"
        f"@{cfg['db_host']}/{cfg['db_name']}"
    )

    engine = create_engine(uri)

    _db_instance = SQLDatabase(engine)
    return _db_instance


# --------------------------------------------------
# TEST DATABASE CONNECTION
# --------------------------------------------------
def test_db_connection(cfg: Dict[str, str]) -> Tuple[bool, str | None]:
    try:
        uri = (
            f"mysql+pymysql://{cfg['db_user']}:{cfg['db_password']}"
            f"@{cfg['db_host']}/{cfg['db_name']}"
        )
        engine = create_engine(uri)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)


# ==================================================
# 🟢 EXECUTE SQL QUERY (NEW – REQUIRED)
# ==================================================
def execute_sql_query(sql: str) -> Tuple[List[str], List[list]]:
    """
    Executes a READ-ONLY SQL query and returns:
    - column names
    - rows
    """

    cfg = get_fe_data()

    uri = (
        f"mysql+pymysql://{cfg['db_user']}:{cfg['db_password']}"
        f"@{cfg['db_host']}/{cfg['db_name']}"
    )

    engine = create_engine(uri)

    with engine.connect() as conn:
        result = conn.execute(text(sql))

        # Extract column names
        columns = list(result.keys())

        # Extract rows
        rows = [list(row) for row in result.fetchall()]

    return columns, rows
