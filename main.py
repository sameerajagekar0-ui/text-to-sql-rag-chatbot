from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import store_fe_data, get_fe_data
from db import test_db_connection, execute_sql_query   # 🔹 ADD execute_sql_query
from rag_sql import chat_with_db

# -------------------- APP --------------------
app = FastAPI(title="Text-to-SQL RAG Chatbot API")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- MODELS --------------------
class DBConfigRequest(BaseModel):
    db_host: str
    db_user: str
    db_password: str
    db_name: str


class QuestionRequest(BaseModel):
    question: str


# 🔹 NEW MODEL
class ExecuteSQLRequest(BaseModel):
    sql: str


# -------------------- HEALTH CHECK --------------------
@app.get("/")
def health():
    return {"status": "ok"}


# -------------------- CONNECT DATABASE --------------------
@app.post("/connect-db")
def connect_db(data: DBConfigRequest):
    cfg = data.model_dump()

    ok, err = test_db_connection(cfg)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=f"Database connection failed: {err}"
        )

    store_fe_data(cfg)

    return {
        "status": "success",
        "message": "Database connected successfully"
    }


# -------------------- ASK QUESTION --------------------
@app.post("/ask")
def ask_question(data: QuestionRequest):

    if not data.question or not data.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question must be a non-empty string"
        )

    question = data.question.strip()

    # Ensure DB connected
    try:
        get_fe_data()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Database not connected. Call /connect-db first."
        )

    try:
        result = chat_with_db(question)

        if not isinstance(result, dict):
            raise ValueError("Invalid response from chat_with_db")

        return {
            "question": question,
            "sql": result.get("sql", "N/A"),
            "answer": result.get("answer", "No answer generated")
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


# =====================================================
# 🟢 EXECUTE SQL (NEW ENDPOINT)
# =====================================================
@app.post("/execute-sql")
def execute_sql(data: ExecuteSQLRequest):

    sql = data.sql.strip()

    if not sql:
        raise HTTPException(
            status_code=400,
            detail="SQL query cannot be empty"
        )

    # 🔒 Optional safety check (recommended)
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
    if any(word in sql.lower() for word in forbidden):
        raise HTTPException(
            status_code=403,
            detail="Only SELECT queries are allowed"
        )

    try:
        columns, rows = execute_sql_query(sql)

        return {
            "columns": columns,
            "rows": rows
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"SQL execution failed: {str(e)}"
        )
