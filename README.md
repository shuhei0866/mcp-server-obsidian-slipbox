# Obsidian Zettelkasten MCP Server

This is an MCP (Model Context Protocol) server designed to connect your Obsidian Vault with AI models (like Claude in Cursor).

## Intended Use Case

This tool is specifically designed for users who manage their knowledge with the following setup:

- **Zettelkasten Method**: Organizing notes using a directory structure like `000_Slipbox` in an Obsidian Vault.
- **AI Dialogue Aggregation**: Consolidating AI conversations into specific directories like `000_Slipbox/ai_dialogues` (or `11_claude_dialogues`, etc.) to track the evolution of your thoughts.
- **Git Submodule Workflow**: Managing the Obsidian Vault as a Git submodule within a project workspace to treat code and knowledge as an integrated system.

## Tools Provided

- `search_memos`: Semantic search across your Vault. Finds relevant notes even if keywords don't match exactly.
- `read_memo`: Read the content of a specific note.
- `write_memo`: Save a plain Markdown file to a specific path (for drafts or documents).
- `write_dialogue`: Save a conversation as a formatted dialogue note (with date and provider).
- `list_recent_memos`: List recently updated notes.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Register in Cursor

You can enable this server in Cursor settings to allow Claude to read and write your notes directly.

1. Open Cursor **Settings** (Cmd+,).
2. Navigate to **Features** > **MCP**.
3. Click **+ Add New MCP Server**.
4. Enter the following information and click **Save**:

- **Name**: `ObsidianMemo`
- **Type**: `command`
- **Command**:
  ```bash
  /path/to/your/venv/bin/python /path/to/server.py
  ```

For more advanced configuration (e.g., in `mcp.json`), use the following structure:

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

## Usage Examples

Once registered, you can prompt Claude like this:

- "Search for notes about 'LLM architecture' from last month."
- "Save this discussion as a new note titled 'MCP Integration Ideas' in the ai_dialogues folder."
- "What are the 5 most recently updated notes?"

## Important Notes

- This server communicates via `stdio` (standard input/output).
- Note saving defaults to `000_Slipbox/ai_dialogues/`, but you can specify existing folders like `11_claude_dialogues`.
- Set the root path of your Vault by either editing `DEFAULT_VAULT_PATH` in `server.py` or setting the `OBSIDIAN_VAULT_PATH` environment variable.
