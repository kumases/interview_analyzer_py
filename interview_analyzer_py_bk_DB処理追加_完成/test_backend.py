import backend_logic
import os
import logging
import time
import database_handler

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

# テスト対象の入力パス
input_dir = r"C:\Users\kumakura\Desktop\projects\interview_analyzer_py\dist\新しいフォルダー"

logging.info(f"--- テスト開始: {input_dir} の処理 ---")

# backend_logic.load_config() を呼び出してAI設定をロード
if not backend_logic.load_config():
    logging.error("設定の読み込みに失敗しました。テストを終了します。")
    exit()

# データベースの初期化
database_handler.initialize_database()

result_message, saved_file_paths = backend_logic.process_interviews_logic(input_dir)

logging.info(f"--- テスト終了 ---")
logging.info(f"結果メッセージ: {result_message}")
logging.info(f"保存されたファイルパス: {saved_file_paths}")

# 最新のログファイルの内容は、既にコンソールに出力されているはずなので、ここでは読み込まない
