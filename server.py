import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Vault settings
# 自身の環境に合わせて環境変数 OBSIDIAN_VAULT_PATH を設定するか、
# 下記の DEFAULT_VAULT_PATH を直接書き換えてください。
DEFAULT_VAULT_PATH = "/path/to/your/vault"
vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
VAULT_ROOT = Path(vault_path_str)

# Create MCP server
mcp = FastMCP("ObsidianMemo")


@mcp.tool()
def search_memos(query: str, limit: int = 10) -> str:
    """ObsidianのVault内のMarkdownファイルから検索クエリに一致するものを探します。

    Args:
        query: 検索キーワード
        limit: 最大取得件数
    """
    if not VAULT_ROOT.exists() or str(VAULT_ROOT) == "/path/to/your/vault":
        return "エラー: Vaultのパスが正しく設定されていません。server.pyのDEFAULT_VAULT_PATHを確認するか、環境変数 OBSIDIAN_VAULT_PATH を設定してください。"

    results = []
    count = 0

    # Vault内を再帰的に検索
    for file_path in VAULT_ROOT.rglob("*.md"):
        if count >= limit:
            break

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if (
                    query.lower() in content.lower() or query.lower() in file_path.name.lower()
                ):
                    rel_path = file_path.relative_to(VAULT_ROOT)
                    # マッチした周辺のテキストを少し抽出
                    snippet = ""
                    pos = content.lower().find(query.lower())
                    if pos != -1:
                        start = max(0, pos - 50)
                        end = min(len(content), pos + 100)
                        snippet = content[start:end].replace("\n", " ")
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."

                    results.append(f"- **{rel_path}**\n  - {snippet}")
                    count += 1
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

    if not results:
        return f"'{query}' に一致するメモは見つかりませんでした。"

    return "検索結果:\n" + "\n".join(results)


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
def save_insight(
    title: str, user_content: str, ai_content: str, folder: Optional[str] = None
) -> str:
    """チャットでの重要な洞察や議論を新しいメモとして保存します。
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
    content = f"""# {title}

Date: {today}

## Conversation

### 👤 User

{user_content}

### 🤖 Claude

{ai_content}
"""

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"メモを保存しました: {file_path.relative_to(VAULT_ROOT)}"
    except Exception as e:
        return f"エラー: メモの保存に失敗しました: {str(e)}"


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
