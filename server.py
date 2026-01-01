import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Vault settings
# 自身の環境に合わせて環境変数 OBSIDIAN_VAULT_PATH を設定するか、
# 下記の DEFAULT_VAULT_PATH を直接書き換えてください。
DEFAULT_VAULT_PATH = "/path/to/your/vault"
vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
VAULT_ROOT = Path(vault_path_str)

# Vector Index settings
INDEX_PATH = Path(__file__).parent / "faiss_index"

# Create MCP server
mcp = FastMCP("ObsidianMemo")


@mcp.tool()
def search_memos(query: str, limit: int = 10) -> str:
    """ObsidianのVault内をセマンティック検索（意味ベースの検索）します。
    キーワードが一致しなくても、文脈が近いメモを見つけることができます。

    Args:
        query: 検索クエリ（例: 「AIの倫理について」）
        limit: 最大取得件数
    """
    if not VAULT_ROOT.exists() or str(VAULT_ROOT) == "/path/to/your/vault":
        return "エラー: Vaultのパスが正しく設定されていません。"

    if not INDEX_PATH.exists():
        return "エラー: インデックスが見つかりません。まず `index_vault.py` を実行してインデックスを作成してください。"

    try:
        # 1. インデックスの読み込み
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.load_local(
            str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )

        # 2. セマンティック検索の実行
        # similarity_search_with_score を使うと類似度スコアも取得可能
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=limit)

        if not docs_with_scores:
            return f"'{query}' に関連するメモは見つかりませんでした。"

        results = []
        for doc, score in docs_with_scores:
            rel_path = Path(doc.metadata["source"]).relative_to(VAULT_ROOT)
            # スコア（距離）をパーセンテージ的な類似度に変換（簡易計算）
            # FAISSのL2距離の場合、数値が小さいほど近い
            snippet = doc.page_content[:200].replace("\n", " ")
            results.append(f"- **{rel_path}** (Score: {score:.4f})\n  - {snippet}...")

        return "セマンティック検索結果:\n" + "\n".join(results)

    except Exception as e:
        return f"エラー: 検索中に問題が発生しました: {str(e)}"


@mcp.tool()
def read_memo(relative_path: str) -> str:
    """指定されたパスのメモの内容を読み込みます。

    Args:
        relative_path: Vaultルートからの相対パス（例: '000_Slipbox/memo.md'）
    """
    file_path = VAULT_ROOT / relative_path

    if not file_path.exists():
        return f"エラー: ファイルが見つかりません: {relative_path}"

    if not file_path.is_file():
        return f"エラー: 指定されたパスはファイルではありません: {relative_path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"エラー: ファイルの読み込みに失敗しました: {str(e)}"


@mcp.tool()
def write_memo(path: str, content: str) -> str:
    """Vault内の指定されたパスに、プレーンなMarkdownファイルを保存します。
    会話ログ形式（User/AI）ではなく、純粋なドキュメントの保存に使用します。

    Args:
        path: Vaultルートからの相対パス（例: '000_Slipbox/memo.md'）
        content: 書き込むMarkdownの全文
    """
    file_path = VAULT_ROOT / path

    # ディレクトリが存在しない場合は作成
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"ファイルを保存しました: {path}"
    except Exception as e:
        return f"エラー: 保存に失敗しました: {str(e)}"


@mcp.tool()
def write_dialogue(
    title: str, user_content: str, ai_content: str, folder: Optional[str] = None
) -> str:
    """チャットでの重要な洞察や議論を会話形式のメモとして保存します。
    ファイル名は 'YYYY-MM-DD-[provider]-[title].md' 形式で自動生成されます。

    Args:
        title: メモのタイトル（ファイル名の一部になります）
        user_content: ユーザーの発言内容
        ai_content: AIの回答・考察内容
        folder: 保存先フォルダ名（例: '10_chatgpt_dialogues', '11_claude_dialogues'）。未指定の場合は 'ai_dialogues' に保存されます。
    """
    # 日付の取得
    today = datetime.now().strftime("%Y-%m-%d")

    # 保存ディレクトリの決定
    if folder:
        # 数字で始まる既存フォルダなどを考慮し、000_Slipbox直下と仮定
        target_dir = VAULT_ROOT / "000_Slipbox" / folder
    else:
        target_dir = VAULT_ROOT / "000_Slipbox/ai_dialogues"

    # プロバイダー名の識別（ファイル名に使用）
    provider = "ai"
    if folder:
        if "claude" in folder.lower():
            provider = "claude"
        elif "chatgpt" in folder.lower():
            provider = "chatgpt"

    # ファイル名のクレンジング
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_")
    filename = f"{today}-{provider}-{safe_title}.md"
    file_path = target_dir / filename

    # 保存ディレクトリの確認
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    # すでに同名のファイルがある場合は枝番を付ける
    counter = 1
    while file_path.exists():
        filename = f"{today}-{provider}-{safe_title}-{counter}.md"
        file_path = target_dir / filename
        counter += 1

    # コンテンツの組み立て
    # プロバイダー名を大文字にして表示
    display_ai_name = provider.capitalize() if provider != "ai" else "AI"

    content = f"""# {title}

Date: {today}

## Conversation

### 👤 User

{user_content}

### 🤖 {display_ai_name}

{ai_content}
"""

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"会話ログを保存しました: {file_path.relative_to(VAULT_ROOT)}"
    except Exception as e:
        return f"エラー: 会話ログの保存に失敗しました: {str(e)}"


# 互換性のために save_insight も残しておく（中身は write_dialogue を呼び出す）
@mcp.tool()
def save_insight(
    title: str, user_content: str, ai_content: str, folder: Optional[str] = None
) -> str:
    """【推奨: write_dialogue】チャットでの洞察を保存します。"""
    return write_dialogue(title, user_content, ai_content, folder)


@mcp.tool()
def list_recent_memos(limit: int = 10) -> str:
    """最近更新されたメモの一覧を取得します。

    Args:
        limit: 取得件数
    """
    files = []
    for file_path in VAULT_ROOT.rglob("*.md"):
        try:
            mtime = os.path.getmtime(file_path)
            files.append((mtime, file_path))
        except Exception as e:
            print(f"Error getting modification time for {file_path}: {e}")
            continue

    # 更新日時でソート
    files.sort(key=lambda x: x[0], reverse=True)

    recent = files[:limit]
    if not recent:
        return "メモは見つかりませんでした。"

    results = []
    for mtime, path in recent:
        dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        rel_path = path.relative_to(VAULT_ROOT)
        results.append(f"- [{dt}] **{rel_path}**")

    return "最近更新されたメモ:\n" + "\n".join(results)


if __name__ == "__main__":
    mcp.run()
