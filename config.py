import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 模型配置
    EMBEDDING_MODEL = "text-embedding-3-small"
    FINETUNED_MODEL = os.getenv("FINETUNED_MODEL", "gpt-4o-mini")  # 你的fine-tuned模型ID
    
    # 向量数据库配置 - ChromaDB Cloud
    USE_CHROMA_CLOUD = os.getenv("USE_CHROMA_CLOUD", "true").lower() == "true"
    
    # ChromaDB Cloud配置
    CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
    CHROMA_TENANT = os.getenv("CHROMA_TENANT")
    CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")
    
    # 本地ChromaDB配置（备用）
    VECTOR_DB_PATH = "./data/db/chroma"
    
    COLLECTION_NAME = "mental_health_kb"
    
    # RAG配置
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    TOP_K_RETRIEVAL = 6  # 增加检索文档数量，以便引用更多知识库内容
    SIMILARITY_THRESHOLD = 1.2  # 放宽阈值以提高召回率 (ChromaDB cosine distance: 0=perfect, 2=opposite)
    TEMPERATURE = 0.7

