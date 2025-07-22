import backend_logic
import os
import logging
import time
import database_handler
import argparse # 追加

# ロギング設定を一時的に変更して、コンソールにも出力するようにする
# backend_logicのロギング設定が既にbasicConfigされているので、ここでは追加のハンドラを設定する
# 既存のハンドラをクリアして再設定することで、重複出力を防ぐ
for handler in logging.getLogger().handlers[:]:
    logging.getLogger().removeHandler(handler)

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, time.strftime('%Y%m%d_%H%M%S_test.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler() # コンソールにも出力
    ]
)

# コマンドライン引数のパース
parser = argparse.ArgumentParser(description="面談分析ツールのバックエンドテストスクリプト")
parser.add_argument('--mode', type=str, default='summary', choices=['summary', 'delete_list'],
                    help='実行するテストモード (summary: 要約テスト, delete_list: 削除リスト取得テスト)')
args = parser.parse_args()

# テスト対象の入力パス
input_dir = r"C:\Users\kumakura\Desktop\projects\interview_analyzer_py\dist\新しいフォルダー"

logging.info(f"--- テスト開始: {input_dir} の処理 ---")

# backend_logic.load_config() を呼び出してAI設定をロード
if not backend_logic.load_config():
    logging.error("設定の読み込みに失敗しました。テストを終了します。")
    exit()

# データベースの初期化
database_handler.initialize_database()

if args.mode == 'summary':
    logging.info("--- 要約テスト実行中 ---")
    result_message, saved_file_paths = backend_logic.process_interviews_logic(input_dir)
    logging.info(f"--- 要約テスト終了 ---")
    logging.info(f"結果メッセージ: {result_message}")
    logging.info(f"保存されたファイルパス: {saved_file_paths}")
elif args.mode == 'delete_list':
    logging.info("--- 削除対象リスト取得テスト実行中 ---")
    deletable_list, _, _ = backend_logic.run_backend_process(mode="get_delete_list")
    logging.info(f"取得された削除対象リスト: {deletable_list}")
    logging.info("--- 削除対象リスト取得テスト終了 ---")

