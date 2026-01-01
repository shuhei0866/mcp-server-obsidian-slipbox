# Obsidian MCP Server for Life Value Lab

このディレクトリは、自身の Obsidian Vault と AIモデル を連携させるための MCP (Model Context Protocol) サーバです。

## 想定しているユースケース

このツールは、以下の構成で知識管理を行っているユーザーを対象とした、やや特化型の実装になっています。

- **Zettelkasten方式**: Obsidian Vault 内で `000_Slipbox` などのディレクトリ構造を用いた知識管理を行っている。
- **AI 対話ログの集約**: AI との対話を `000_Slipbox/ai_dialogues`（または `11_claude_dialogues` 等）に集約し、自分の思考の系譜として管理している。
- **Git サブモジュール運用**: Obsidian Vault 自体をワークスペース内のサブモジュールとして配置し、プロジェクトコードと知識ベースを不可分に扱っている。

## 提供する機能 (Tools)

- `search_memos`: Vault内のMarkdownファイルを全文検索
- `read_memo`: 指定したメモの内容を読み取り
- `save_insight`: チャットでの議論を新しいメモとして保存 (デフォルトは `ai_dialogues` 、明示的に指定すれば `11_claude_dialogues` などモデル別のディレクトリへ保存)
- `list_recent_memos`: 最近更新されたメモの一覧を表示

## セットアップ手順

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Cursor への登録

Cursor の設定からこのサーバを有効にすることで、Claude があなたのメモを直接読み書きできるようになります。

1. Cursor の **Settings** (Cmd+,) を開く
2. **Features** > **MCP** セクションへ移動
3. **+ Add New MCP Server** をクリック
4. 以下の情報を入力して **Save**：

- **Name**: `ObsidianMemo`
- **Type**: `command`
- **Command**:
  ```bash
  /path/to/your/venv/bin/python /path/to/server.py
  ```

より詳細な設定（`mcp.json` 等）を行う場合は、以下の構造を参考にしてください：

```json
{
  "mcpServers": {
    "ObsidianMemo": {
      "command": "/path/to/your/venv/bin/python",
      "args": [
        "/path/to/server.py"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
      }
    }
  }
}
```

## 使い方

登録後、Claude とのチャットで以下のように指示できます：

- 「先月の共通テストに関するメモを検索して」
- 「今の議論を『MCPサーバの活用案』というタイトルでメモに残しておいて」
- 「最近更新したメモを5件教えて」

## 注意事項

- このサーバは `stdio` (標準入出力) を介して通信します。
- メモの保存先はデフォルトで `000_Slipbox/ai_dialogues/` ですが、必要に応じて `11_claude_dialogues` など既存のフォルダを指定可能です。
- Vault のルートパスは、`server.py` 内の `DEFAULT_VAULT_PATH` を書き換えるか、環境変数 `OBSIDIAN_VAULT_PATH` を設定して使用してください。
