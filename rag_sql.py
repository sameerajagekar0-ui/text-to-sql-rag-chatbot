from typing import Dict, Any, List
from sqlalchemy import text

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from db import get_database
from config import GOOGLE_API_KEY

# =========================================================
# 🔐 LLM CONFIGURATION
# =========================================================

sql_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

nl_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

# =========================================================
# 🧠 PROMPTS
# =========================================================

SQL_PROMPT = ChatPromptTemplate.from_template("""
You are an expert MySQL developer.

Rules:
- Use ONLY tables and columns from the schema
- Generate ONLY read-only SQL (SELECT / WITH)
- Do NOT use INSERT, UPDATE, DELETE, DROP, ALTER
- Output ONLY raw SQL (no markdown, no explanation)

Schema:
{table_info}

Question:
{input}

Limit {top_k}

SQL:
""")

NATURAL_LANG_PROMPT = ChatPromptTemplate.from_template("""
Answer the user's question using the SQL result.
Be clear, concise, and accurate.

Question:
{input}

SQL Query:
{sql}

SQL Result:
{result}

Answer:
""")

# =========================================================
# 🚫 SQL SAFETY
# =========================================================

FORBIDDEN_SQL = (
    "insert", "update", "delete", "drop",
    "alter", "truncate", "create", "replace"
)

def validate_sql(sql: str) -> None:
    sql_lower = sql.lower().strip()

    if not sql_lower.startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed")

    for keyword in FORBIDDEN_SQL:
        if keyword in sql_lower:
            raise ValueError(f"Forbidden SQL operation detected: {keyword}")

# =========================================================
# 🧠 MAIN FUNCTION
# =========================================================

def chat_with_db(user_input: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Converts natural language → SQL → executes → returns answer + table
    """
    db = get_database()

    # -------------------------
    # SQL GENERATION
    # -------------------------
    sql_chain = create_sql_query_chain(
        llm=sql_llm,
        db=db,
        prompt=SQL_PROMPT,
    )

    sql_query = sql_chain.invoke({
        "input": user_input,
        "question": user_input,  # ✅ REQUIRED BY LANGCHAIN
        "top_k": top_k,
    })

    sql_query = (
        str(sql_query)
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

    if not sql_query:
        raise ValueError("SQL generation failed")

    validate_sql(sql_query)

    # Auto LIMIT if missing
    if "limit" not in sql_query.lower():
        sql_query += f" LIMIT {top_k}"

    # -------------------------
    # SQL EXECUTION
    # -------------------------
    engine = db._engine  # safe internal access

    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()

    table = {
        "columns": list(columns),
        "rows": [list(row) for row in rows]
    }

    # -------------------------
    # NATURAL LANGUAGE ANSWER
    # -------------------------
    nl_chain = NATURAL_LANG_PROMPT | nl_llm | StrOutputParser()

    answer = nl_chain.invoke({
        "input": user_input,
        "sql": sql_query,
        "result": rows,
    })

    return {
        "sql": sql_query,
        "answer": answer.strip(),
        "table": table
    }
