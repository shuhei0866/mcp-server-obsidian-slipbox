import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# あなたの環境に合わせた設定
DEFAULT_VAULT_PATH = "/path/to/your/vault"
vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
VAULT_ROOT = Path(vault_path_str)
INDEX_SAVE_DIR = Path(__file__).parent / "faiss_index"

def create_index():
    with open("debug_index.log", "a") as f:
        f.write("--- SCRIPT START ---\n")
    print("--- SCRIPT START ---", flush=True)
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ エラー: 環境変数 OPENAI_API_KEY が設定されていません。", flush=True)
        return

    print(f"📂 Vaultを読み込み中: {VAULT_ROOT}", flush=True)
    
    # 1. Markdownファイルを読み込む
    # .mdファイルを再帰的に探索
    loader = DirectoryLoader(
        str(VAULT_ROOT),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    print(f"📄 {len(documents)} 件のメモを読み込みました。", flush=True)

    # 2. チャンク分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "、", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✂️  合計 {len(chunks)} 個 of チャンクに分割しました。", flush=True)

    # 3. ベクトル化 & インデックス作成
    print("🧠 ベクトル化を実行中（OpenAI APIを使用します）...", flush=True)
    # chunk_size は API に一回で送るドキュメント数。トークン制限を避けるために小さめに設定
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", chunk_size=100)
    
    # FAISSインデックスを作成
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # 4. ローカルに保存
    INDEX_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"💾 インデックスを保存中: {INDEX_SAVE_DIR}", flush=True)
    vectorstore.save_local(str(INDEX_SAVE_DIR))
    
    print("\n✨ 完了！あなたのObsidianは1,536次元の空間にマッピングされました。", flush=True)

if __name__ == "__main__":
    create_index()
