import time
import os
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from index_vault import create_index

# Vault settings
DEFAULT_VAULT_PATH = "/path/to/your/vault"
vault_path_str = os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)
VAULT_ROOT = Path(vault_path_str)


class VaultChangeHandler(FileSystemEventHandler):
    """Obsidian Vault の変更を検知してインデックスを更新するハンドラ"""

    def __init__(self):
        self.last_sync_time = 0
        self.debounce_seconds = 2  # 短時間の連続変更を無視する時間（秒）

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._trigger_sync(f"変更検知: {Path(event.src_path).name}")

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._trigger_sync(f"新規作成検知: {Path(event.src_path).name}")

    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        self._trigger_sync(f"削除検知: {Path(event.src_path).name}")

    def _trigger_sync(self, message):
        current_time = time.time()
        # デバウンス処理（保存時の複数回イベント発生を抑える）
        if current_time - self.last_sync_time > self.debounce_seconds:
            print(f"\n🔄 {message}")
            try:
                create_index()
                self.last_sync_time = time.time()
                print("✅ インデックスの自動更新が完了しました。")
            except Exception as e:
                print(f"❌ インデックス更新中にエラーが発生しました: {e}")


def start_sync():
    if not VAULT_ROOT.exists() or str(VAULT_ROOT) == "/path/to/your/vault":
        print("❌ エラー: Vaultのパスが正しく設定されていません。")
        print("環境変数 OBSIDIAN_VAULT_PATH を設定してください。")
        sys.exit(1)

    print(f"🚀 Obsidian Sync Server を起動しました")
    print(f"📂 監視対象: {VAULT_ROOT}")

    # 1. 起動時に初回スキャンを実行
    print("\n🔍 初回スキャンを開始します...")
    try:
        create_index()
        print("✅ 初回インデックス作成が完了しました。")
    except Exception as e:
        print(f"⚠️ 初回インデックス作成に失敗しましたが、監視は継続します: {e}")

    # 2. Watchdog による監視を開始
    event_handler = VaultChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, str(VAULT_ROOT), recursive=True)
    observer.start()

    print("\n✨ リアルタイム監視中... (メモを編集すると自動でインデックスが更新されます)")
    print("💡 終了するには Ctrl+C を押してください。")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 監視を終了しました。")

    observer.join()


if __name__ == "__main__":
    start_sync()
