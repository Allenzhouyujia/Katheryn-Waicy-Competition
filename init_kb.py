# -*- coding: utf-8 -*-
import sys
import io
# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config import Settings
import chromadb
import os
from pathlib import Path

def init_knowledge_base(documents_dir: str = None):
    """
    初始化知识库
    
    Args:
        documents_dir: 文档目录路径，如果为None则会在当前目录查找data/knowledge_base
    """
    # 确定文档目录
    if documents_dir is None:
        documents_dir = "./data/knowledge_base"
    
    if not os.path.exists(documents_dir):
        print(f"文档目录不存在: {documents_dir}")
        print("请创建该目录并放入文档文件（支持.txt和.pdf格式）")
        return
    
    # 加载所有文档
    documents = []
    supported_extensions = ['.txt', '.pdf']
    
    print(f"正在从 {documents_dir} 加载文档...")
    for file_path in Path(documents_dir).rglob('*'):
        if file_path.suffix.lower() in supported_extensions:
            try:
                print(f"  加载: {file_path}")
                if file_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                else:
                    loader = TextLoader(str(file_path), encoding='utf-8')
                
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"  错误: 无法加载 {file_path}: {e}")
    
    if not documents:
        print("未找到任何文档文件！")
        print(f"请在 {documents_dir} 目录中放置.txt或.pdf文件")
        return
    
    print(f"共加载 {len(documents)} 个文档")
    
    # 分割文档
    print("正在分割文档...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"文档分割为 {len(chunks)} 个块")
    
    # 创建向量数据库
    print("正在创建向量数据库...")
    embeddings = OpenAIEmbeddings(
        model=Settings.EMBEDDING_MODEL,
        openai_api_key=Settings.OPENAI_API_KEY
    )
    
    if Settings.USE_CHROMA_CLOUD:
        # 使用ChromaDB Cloud
        print("连接到ChromaDB Cloud...")
        chroma_client = chromadb.CloudClient(
            api_key=Settings.CHROMA_API_KEY,
            tenant=Settings.CHROMA_TENANT,
            database=Settings.CHROMA_DATABASE
        )
        
        # 检查集合是否存在，如果存在则删除
        try:
            chroma_client.delete_collection(name=Settings.COLLECTION_NAME)
            print(f"已删除现有集合: {Settings.COLLECTION_NAME}")
        except:
            print(f"集合 {Settings.COLLECTION_NAME} 不存在，将创建新集合")
        
        # 创建新的向量数据库
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=chroma_client,
            collection_name=Settings.COLLECTION_NAME
        )
        
        print(f"✅ 知识库初始化完成！")
        print(f"   数据库类型: ChromaDB Cloud")
        print(f"   数据库名称: {Settings.CHROMA_DATABASE}")
        print(f"   文档块数量: {len(chunks)}")
        print(f"   集合名称: {Settings.COLLECTION_NAME}")
    else:
        # 使用本地ChromaDB
        print("使用本地ChromaDB...")
        # 确保目录存在
        os.makedirs(Settings.VECTOR_DB_PATH, exist_ok=True)
        
        # 如果数据库已存在，先删除
        if os.path.exists(Settings.VECTOR_DB_PATH) and os.listdir(Settings.VECTOR_DB_PATH):
            print("检测到已存在的数据库，将覆盖...")
            import shutil
            shutil.rmtree(Settings.VECTOR_DB_PATH)
            os.makedirs(Settings.VECTOR_DB_PATH, exist_ok=True)
        
        # 创建新的向量数据库
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=Settings.VECTOR_DB_PATH,
            collection_name=Settings.COLLECTION_NAME
        )
        
        print(f"✅ 知识库初始化完成！")
        print(f"   向量数据库路径: {Settings.VECTOR_DB_PATH}")
        print(f"   文档块数量: {len(chunks)}")
        print(f"   集合名称: {Settings.COLLECTION_NAME}")

if __name__ == "__main__":
    import sys
    
    # 可以从命令行参数指定文档目录
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        init_knowledge_base(docs_dir)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

