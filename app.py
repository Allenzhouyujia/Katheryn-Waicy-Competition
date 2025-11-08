from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from rag_engine import RAGEngine
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化RAG引擎
rag_engine = RAGEngine()

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str
    sources: list = []
    stage: Optional[str] = None  # 对话阶段: 'empathy', 'reflection', 'support', None
    risk_level: str = 'none'  # 风险级别

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 调用RAG引擎生成回复
        result = rag_engine.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        # 确保 response 字段存在且不为空
        if not result.get("response"):
            raise ValueError("RAG engine returned empty response")
        
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            stage=result.get("stage"),  # 可以是None（高风险情况下）
            risk_level=result.get("risk_level", "none")
        )
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in /api/chat: {error_detail}")  # 打印完整错误到控制台
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import sys
    # 尝试不同端口，避免端口占用
    port = 8000
    for i in range(5):
        try:
            uvicorn.run(app, host="0.0.0.0", port=port)
            break
        except OSError as e:
            if "10048" in str(e) or "address already in use" in str(e).lower():
                print(f"Port {port} is in use, trying port {port + 1}...")
                port += 1
            else:
                raise
    else:
        print(f"Could not find available port. Please close the process using ports 8000-8004.")
        sys.exit(1)

