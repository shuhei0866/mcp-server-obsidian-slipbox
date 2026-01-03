import os
import re
from pathlib import Path
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# あなたの環境に合わせた設定
DEFAULT_VAULT_PATH = "/path/to/your/vault"
vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
VAULT_ROOT = Path(vault_path_str)
INDEX_SAVE_DIR = Path(__file__).parent / "faiss_index"
CACHE_DIR = Path(__file__).parent / "embeddings_cache"


def extract_links(text):
    """Markdownから [[リンク名]] 形式の内部リンクをすべて抽出する"""
    links = re.findall(r"\[\[(.*?)\]\]", text)
    clean_links = [link.split("|")[0] for link in links]
    return list(set(clean_links))


def create_index():
    print("--- SCRIPT START ---", flush=True)
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ エラー: 環境変数 OPENAI_API_KEY が設定されていません。", flush=True)
        return

    print(f"📂 Vaultを読み込み中: {VAULT_ROOT}", flush=True)

    # 1. Markdownファイルを読み込む
    loader = DirectoryLoader(
        str(VAULT_ROOT),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    print(f"📄 {len(documents)} 件のメモを読み込みました。", flush=True)

    # 1.5 リンク情報の抽出とメタデータへの付与
    for doc in documents:
        links = extract_links(doc.page_content)
        doc.metadata["links"] = ", ".join(links) if links else ""

    # 2. チャンク分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "、", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)
    print(f"✂️  合計 {len(chunks)} 個のチャンクに分割しました。", flush=True)

    # 3. キャッシュ付きベクトル化の設定
    # これにより、同じテキストに対するAPIコールは一度しか発生しません
    underlying_embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", chunk_size=100
    )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    store = LocalFileStore(str(CACHE_DIR))

    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings, store, namespace=underlying_embeddings.model
    )

    # 4. ベクトル化 & インデックス作成
    print(
        "🧠 ベクトル化を実行中（変更がない箇所はキャッシュを利用します）...", flush=True
    )
    vectorstore = FAISS.from_documents(chunks, cached_embedder)

    # 5. ローカルに保存
    INDEX_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"💾 インデックスを保存中: {INDEX_SAVE_DIR}", flush=True)
    vectorstore.save_local(str(INDEX_SAVE_DIR))

    print("\n✨ 完了！インデックスが最新の状態になりました。", flush=True)


if __name__ == "__main__":
    create_index()
