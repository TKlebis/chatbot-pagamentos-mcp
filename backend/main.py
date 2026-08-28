import os
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from ollama import AsyncClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# ==========================================
# CONFIGURAÇÕES
# ==========================================
SECRET_KEY = "chave-super-secreta-desafio"
ALGORITHM = "HS256"
DB_PATH = "data/app.db"

app = FastAPI(title="ChatPay Backend API")
security = HTTPBearer()
password_hash = PasswordHash((Argon2Hasher(),))
ollama = AsyncClient()

# Permite que o frontend React converse com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# MODELOS DE DADOS
# ==========================================
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def get_db():
    # TIMEOUT ADICIONADO PARA EVITAR "DATABASE IS LOCKED"
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

# Middleware de Autenticação JWT
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

# ==========================================
# ROTAS DA API
# ==========================================
@app.post("/login")
def login(req: LoginRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    conn.close()

    if not user or not password_hash.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    expire = datetime.now(timezone.utc) + timedelta(hours=2)
    token = jwt.encode({"sub": user["id"], "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer", "user_id": user["id"]}


@app.get("/history")
def get_history(user_id: str = Depends(verify_token)):
    conn = get_db()
    chat = conn.execute("SELECT id FROM chats WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if not chat:
        return {"messages": []}

    mensagens = conn.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? AND role IN ('user', 'assistant') ORDER BY id",
        (chat["id"],)
    ).fetchall()
    conn.close()

    return {"messages": [{"role": m["role"], "content": m["content"]} for m in mensagens if m["content"]]}


@app.post("/chat")
async def chat(req: ChatRequest, user_id: str = Depends(verify_token)):
    conn = get_db()
    agora = datetime.now(timezone.utc).isoformat()

    chat = conn.execute("SELECT id FROM chats WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if not chat:
        chat_id = f"chat_{uuid.uuid4().hex[:8]}"
        conn.execute("INSERT INTO chats (id, user_id) VALUES (?, ?)", (chat_id, user_id))
        conn.commit()
    else:
        chat_id = chat["id"]

    conn.execute(
        "INSERT INTO messages (chat_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (chat_id, user_id, "user", req.message, agora)
    )
    conn.commit()

    historico_db = conn.execute(
        "SELECT role, content, tool_calls_json, tool_name FROM messages WHERE chat_id = ? ORDER BY id",
        (chat_id,)
    ).fetchall()

    messages_for_llm = []
    for row in historico_db:
        msg = {"role": row["role"]}
        if row["content"]: msg["content"] = row["content"]
        if row["tool_calls_json"]: msg["tool_calls"] = json.loads(row["tool_calls_json"])
        if row["tool_name"]: msg["name"] = row["tool_name"]
        messages_for_llm.append(msg)

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
        env={
            **os.environ,
            "DATABASE_PATH": DB_PATH,
            "USER_ID": user_id,
            "CHAT_ID": chat_id
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            await mcp_client.initialize()

            mcp_tools = await mcp_client.list_tools()
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema
                    }
                } for tool in mcp_tools.tools
            ]

            while True:
                response = await ollama.chat(
                    model="qwen3",
                    messages=messages_for_llm,
                    tools=ollama_tools
                )

                assist_msg = response["message"]
                messages_for_llm.append(assist_msg)

                if not assist_msg.get("tool_calls"):
                    conn.execute(
                        "INSERT INTO messages (chat_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                        (chat_id, user_id, "assistant", assist_msg.get("content", ""), datetime.now(timezone.utc).isoformat())
                    )
                    conn.commit()
                    break

                tool_calls_dict = [t.model_dump() for t in assist_msg["tool_calls"]]

                conn.execute(
                    "INSERT INTO messages (chat_id, user_id, role, tool_calls_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, user_id, "assistant", json.dumps(tool_calls_dict), datetime.now(timezone.utc).isoformat())
                )

                # CORREÇÃO DO DEADLOCK - SALVA NO BANCO ANTES DA TOOL DO MCP RODAR
                conn.commit()

                for tool_call in assist_msg["tool_calls"]:
                    t_name = tool_call.function.name
                    t_args = tool_call.function.arguments

                    mcp_result = await mcp_client.call_tool(t_name, t_args)
                    result_text = "".join([item.text for item in mcp_result.content if item.type == "text"])

                    tool_msg = {
                        "role": "tool",
                        "name": t_name,
                        "content": result_text
                    }
                    messages_for_llm.append(tool_msg)

                    conn.execute(
                        "INSERT INTO messages (chat_id, user_id, role, content, tool_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (chat_id, user_id, "tool", result_text, t_name, datetime.now(timezone.utc).isoformat())
                    )
                conn.commit()

    conn.close()
    return {"response": assist_msg.get("content", "")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)