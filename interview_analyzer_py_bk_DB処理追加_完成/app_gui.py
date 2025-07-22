import customtkinter
from tkinter import filedialog
import threading
import backend_logic # backend_logic.pyをインポート
from tkinterdnd2 import DND_FILES, TkinterDnD as tkdnd # tkinterdnd2をインポート
import itertools # for spinner animation
import os # これを追加！
import logging # これを追加！

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        print("DEBUG: App.__init__ started.")
        self.TkdndVersion = tkdnd._require(self) # tkinterdnd2を有効化

        self.title("Interview Analyzer")
        self.geometry("800x600")

        # --- レイアウト設定 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # ログエリアの行を拡張可能に

        # --- ウィジェットの作成と配置 ---

        # 1. モード選択フレーム
        self.mode_frame = customtkinter.CTkFrame(self)
        self.mode_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.mode_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.mode_variable = customtkinter.StringVar(value="interview")
        self.interview_radio = customtkinter.CTkRadioButton(self.mode_frame, text="面談分析", variable=self.mode_variable, value="interview", command=self.on_mode_change)
        self.interview_radio.grid(row=0, column=0, padx=10, pady=10)
        self.daily_report_radio = customtkinter.CTkRadioButton(self.mode_frame, text="日報分析", variable=self.mode_variable, value="daily_report", command=self.on_mode_change)
        self.daily_report_radio.grid(row=0, column=1, padx=10, pady=10)
        self.qa_radio = customtkinter.CTkRadioButton(self.mode_frame, text="AI対話", variable=self.mode_variable, value="qa", command=self.on_mode_change)
        self.qa_radio.grid(row=0, column=2, padx=10, pady=10)

        # 2. 説明ラベル
        self.description_label = customtkinter.CTkLabel(self, text="「面談分析」: CSVファイルまたはフォルダを選択 | 「日報分析」: Excelファイルを選択 | 「AI対話」: 事前に分析が必要です", text_color="gray")
        self.description_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        # 3. ファイル/フォルダ選択フレーム (通常モード用)
        self.path_frame = customtkinter.CTkFrame(self)
        self.path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = customtkinter.CTkEntry(self.path_frame, placeholder_text="分析対象のファイルまたはフォルダのパス")
        self.path_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.path_entry.drop_target_register(DND_FILES)
        self.path_entry.dnd_bind('<<Drop>>', self.handle_drop)

        self.select_button_frame = customtkinter.CTkFrame(self.path_frame)
        self.select_button_frame.grid(row=0, column=1, padx=10, pady=10)

        self.file_button = customtkinter.CTkButton(self.select_button_frame, text="ファイル選択", command=self.select_file)
        self.file_button.pack(side="left", padx=5)
        self.folder_button = customtkinter.CTkButton(self.select_button_frame, text="フォルダ選択", command=self.select_folder)
        self.folder_button.pack(side="left", padx=5)

        # 4. 実行ボタンとステータスラベルのフレーム
        self.run_status_frame = customtkinter.CTkFrame(self)
        self.run_status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.run_status_frame.grid_columnconfigure(0, weight=1) # ボタンが中央に来るように

        self.run_button = customtkinter.CTkButton(self.run_status_frame, text="分析実行", command=self.start_analysis)
        self.run_button.grid(row=0, column=0, padx=10, pady=5)

        self.status_label = customtkinter.CTkLabel(self.run_status_frame, text="", text_color="yellow")
        self.status_label.grid(row=1, column=0, padx=10, pady=5)

        # 結果ファイル表示ボタン
        self.result_file_button = customtkinter.CTkButton(self.run_status_frame, text="", command=self.open_result_file)
        self.result_file_button.grid(row=2, column=0, padx=10, pady=5)
        self.result_file_button.grid_remove() # 最初は非表示
        self.result_file_path = None # 結果ファイルのパスを保持する変数

        # 結果フォルダ表示ボタン
        self.result_folder_button = customtkinter.CTkButton(self.run_status_frame, text="", command=self.open_result_folder)
        self.result_folder_button.grid(row=3, column=0, padx=10, pady=5)
        self.result_folder_button.grid_remove() # 最初は非表示
        self.result_folder_path = None # 結果フォルダのパスを保持する変数

        # AI対話モード用UI
        self.qa_chat_frame = customtkinter.CTkFrame(self)
        self.qa_chat_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew") # ログエリアの下に配置
        self.qa_chat_frame.grid_columnconfigure(0, weight=1) # 入力フィールドが広がるように
        self.qa_chat_frame.grid_columnconfigure(1, weight=0) # 送信ボタンは固定幅

        self.qa_input_entry = customtkinter.CTkEntry(self.qa_chat_frame, placeholder_text="AIへの質問を入力してください", state="disabled")
        self.qa_input_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.qa_send_button = customtkinter.CTkButton(self.qa_chat_frame, text="送信", command=self.send_qa_message, state="disabled")
        self.qa_send_button.grid(row=0, column=1, padx=10, pady=10)
        self.qa_end_button = customtkinter.CTkButton(self.qa_chat_frame, text="対話終了", command=self.end_qa_session, state="disabled")
        self.qa_end_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # スピナー関連の変数
        self.spinner_chars = itertools.cycle(['-', '\\', '|', '/'])
        self.spinner_id = None

        # 5. ログ表示エリア
        self.log_textbox = customtkinter.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")

        # AI対話のコンテキストを保持する変数
        self.qa_context = None

        # 初期UI設定
        self.on_mode_change() 

        # DB初期化
        print("DEBUG: About to import database_handler.")
        import database_handler
        print("DEBUG: Calling database_handler.initialize_database()...")
        database_handler.initialize_database()
        print("DEBUG: database_handler.initialize_database() finished.")

    # --- UIの表示/非表示を切り替える関数 ---
    def on_mode_change(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == "qa":
            # AI対話モード
            self.path_frame.grid_forget() # ファイル選択フレームを非表示
            self.file_button.configure(state="disabled") # ファイル選択ボタンを無効化
            self.folder_button.configure(state="disabled") # フォルダ選択ボタンを無効化
            self.run_button.configure(text="AI対話開始", command=self.start_qa_session_flow) # ボタンのテキストとコマンドを変更
            self.qa_chat_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew") # チャットフレームを表示
            self.run_status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew") # run_status_frameは常に表示

        else:
            # 通常モード (面談分析、日報分析)
            self.qa_chat_frame.grid_forget() # チャットフレームを非表示
            self.path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew") # ファイル選択フレームを表示
            self.file_button.configure(state="normal") # ファイル選択ボタンを有効化
            self.folder_button.configure(state="normal") # フォルダ選択ボタンを有効化
            self.run_button.configure(text="分析実行", command=self.start_analysis) # ボタンのテキストとコマンドを元に戻す
            self.run_status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew") # run_status_frameは常に表示

        # ログエリアをクリア
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    # --- ボタンのコールバック関数 ---

    def select_file(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == "interview":
            filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        else:
            filepath = filedialog.askopenfilename()
        if filepath:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, filepath)

    def select_folder(self):
        folderpath = filedialog.askdirectory()
        if folderpath:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folderpath)

    def start_analysis(self):
        print("DEBUG: start_analysis called.")
        mode = self.mode_variable.get()
        path = os.path.normpath(self.path_entry.get())
        
        # 実行ボタンとモード選択、ファイル選択ボタンを無効化
        self.run_button.configure(state="disabled")
        self.interview_radio.configure(state="disabled")
        self.daily_report_radio.configure(state="disabled")
        self.qa_radio.configure(state="disabled")
        self.file_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")
        
        self.start_spinner() # スピナー開始

        # ログエリアをクリア
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        # 結果ファイル表示ボタンを非表示に
        self.result_file_button.grid_remove()
        self.result_file_path = None

        # 結果フォルダ表示ボタンを非表示に
        self.result_folder_button.grid_remove()
        self.result_folder_path = None

        # その他のモードは既存の処理
        thread = threading.Thread(target=self.run_backend, args=(mode, path, None, None)) # context is not needed for other modes
        thread.start()

    def start_qa_session_flow(self):
        print("DEBUG: start_qa_session_flow called.")
        # 実行ボタンとモード選択、ファイル選択ボタンを無効化
        self.run_button.configure(state="disabled")
        self.interview_radio.configure(state="disabled")
        self.daily_report_radio.configure(state="disabled")
        self.qa_radio.configure(state="disabled")
        self.file_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")
        
        self.start_spinner()
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        # 結果フォルダ表示ボタンを非表示に
        self.result_folder_button.grid_remove() # これを追加！
        self.result_folder_path = None # パスもクリア

        thread = threading.Thread(target=self._prepare_qa_session)
        thread.start()

    def _prepare_qa_session(self):
        print("DEBUG: _prepare_qa_session called.")
        self.log("AI対話モードの準備を開始します...")
        
        # backend_logicからデータを読み込み、件数とチャットセッションを取得
        initial_context, interview_count, daily_report_count, message, chat_session = backend_logic.prepare_qa_data()
        
        if initial_context is None:
            self.log(f"エラー: {message}")
            self.stop_spinner()
            self.run_button.configure(state="normal")
            return

        self.qa_context = initial_context # 初期コンテキストをインスタンス変数に保存
        self.chat_session = chat_session # チャットセッションをインスタンス変数に保存

        # 読み込み件数をログに表示
        self.log(f"面談要約データ {interview_count}件、日報分析データ {daily_report_count}件を読み込みました。")
        self.log("質問を入力して「送信」ボタンを押してください。")
        
        self.stop_spinner()
        # AI対話用のUIのみを有効化
        self.run_button.configure(state="normal") # 「AI対話開始」ボタンは再度有効にしておく
        
        self.qa_input_entry.configure(state="normal") # 入力フィールドを有効化
        self.qa_send_button.configure(state="normal") # 送信ボタンを有効化
        self.qa_end_button.configure(state="normal") # 対話終了ボタンを有効化
        self.qa_input_entry.focus_set() # 入力フィールドにフォーカス

    def send_qa_message(self):
        question = self.qa_input_entry.get()
        if not question:
            self.log("質問が入力されていません。")
            return
        
        self.qa_input_entry.delete(0, "end") # 入力フィールドをクリア
        self.log("----------------------------------------") # 区切り線
        self.log(f"あなたの質問: {question}")
        
        self.start_spinner()

        thread = threading.Thread(target=self._send_qa_message_backend, args=(question, self.qa_context, self.chat_session))
        thread.start()

    def _send_qa_message_backend(self, question, initial_context, chat_session):
        ai_response = backend_logic.run_backend_process(mode="qa", question=question, context=initial_context, chat_session=chat_session)
        self.log(ai_response)
        self.stop_spinner()
        # 処理完了後、入力フィールドと送信ボタンを再度有効化
        self.qa_input_entry.configure(state="normal")
        self.qa_send_button.configure(state="normal")
        self.run_button.configure(state="normal") # 送信後ボタンを有効化

    def end_qa_session(self):
        # 処理中のスレッドがあれば停止を試みる（スレッドセーフな停止は難しいので、フラグなどで制御するのが理想的ですが、ここでは簡易的に）
        self.stop_spinner() # スピナーを停止
        self.qa_input_entry.configure(state="disabled") # 入力フィールドを無効化
        self.qa_send_button.configure(state="disabled") # 送信ボタンを無効化
        self.qa_end_button.configure(state="disabled") # 対話終了ボタンを無効化

        self.qa_context = None # コンテキストをクリア
        self.chat_session = None # チャットセッションをクリア
        self.log("AI対話セッションを終了します。")
        
        # UIを初期状態に戻す
        self.interview_radio.configure(state="normal")
        self.daily_report_radio.configure(state="normal")
        self.qa_radio.configure(state="normal")
        self.on_mode_change() # UIを通常モードに戻す

    def run_backend(self, mode, path, question, context):
        print(f"DEBUG: run_backend called with mode={mode}, path={path}.")
        self.log(f"[{mode.upper()}] モードで処理を開始します...")
        if mode == "interview":
            output_directory_path = os.path.abspath("面談要約結果")
            result_message, saved_file_paths = backend_logic.run_backend_process(mode=mode, input_path=path, question=question, context=context)
        elif mode == "daily_report":
            output_directory_path = os.path.abspath("日報分析結果")
            result_message, saved_file_paths = backend_logic.run_backend_process(mode=mode, input_path=path, question=question, context=context)
        elif mode == "qa":
            result_message, saved_file_paths = backend_logic.run_backend_process(mode=mode, question=question, context=context, chat_session=chat_session)
            output_directory_path = None # QAモードではフォルダは開かない
        else:
            result_message = f"無効なモードが指定されました: {mode}"
            saved_file_paths = []
            output_directory_path = None

        self.log(f"DEBUG: Backend returned: message='{result_message}', files={saved_file_paths}, folder='{output_directory_path}'") # 追加
        self.log(f"DEBUG: output_directory_path value: {output_directory_path}") # Added log
        self.log(f"DEBUG: input path (path variable): {path}") # Added log
        self.log(f"DEBUG: os.path.isdir(path) result: {os.path.isdir(path)}") # Added log
        self.log(result_message)
        
        # 結果ファイルボタンの処理 (単一ファイル選択時のみ表示)
        # フォルダ指定の場合はファイルを開くボタンは不要
        self.after(0, lambda: self.result_file_button.grid_remove()) # 常に非表示にする
        self.result_file_path = None

        # 結果フォルダボタンの処理
        # input_pathがディレクトリの場合のみフォルダボタンを表示
        if output_directory_path: # これに変更
            self.result_folder_path = output_directory_path
            self.log(f"DEBUG: self.result_folder_path set to: {self.result_folder_path}") # Added log
            self.after(0, lambda: self.result_folder_button.configure(text=f"結果フォルダを開く: {os.path.basename(self.result_folder_path)}"))
            self.after(0, lambda: self.result_folder_button.grid())
        else:
            self.log(f"DEBUG: Folder button not shown. output_directory_path: {output_directory_path}, os.path.isdir(path): {os.path.isdir(path)}") # Added log
            self.after(0, lambda: self.result_folder_button.grid_remove())
            self.result_folder_path = None
        self.log("処理が完了しました。")
        
        self.stop_spinner() # スピナー停止
        # 実行ボタンとモード選択、ファイル選択ボタンを再度有効化
        self.run_button.configure(state="normal")
        self.interview_radio.configure(state="normal")
        self.daily_report_radio.configure(state="normal")
        self.qa_radio.configure(state="normal")
        self.file_button.configure(state="normal")
        self.folder_button.configure(state="normal")

    def log(self, message):
        logging.info(message) # Added to output to file log
        # メインスレッドでGUIを更新
        self.after(0, self._update_log, message)

    def _update_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end") # 自動スクロール

    def start_spinner(self):
        self.status_label.configure(text="処理中...")
        self._animate_spinner()

    def _animate_spinner(self):
        self.status_label.configure(text=f"処理中... {next(self.spinner_chars)}")
        self.spinner_id = self.after(100, self._animate_spinner);

    def stop_spinner(self):
        if self.spinner_id:
            self.after_cancel(self.spinner_id)
            self.spinner_id = None
        self.status_label.configure(text="") # ラベルをクリア

    def handle_drop(self, event):
        # ドロップされたファイルのパスを取得
        # Windowsの場合、パスが "{パス}" の形式で渡されるため、{}を削除
        filepath = event.data.strip('{}')
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, filepath)

    def open_result_file(self):
        if self.result_file_path:
            try:
                import os
                os.startfile(self.result_file_path)
                self.log(f"ファイルを開きました: {self.result_file_path}")
            except Exception as e:
                self.log(f"ファイルのオープンに失敗しました: {e}")

    def open_result_folder(self):
        self.log(f"DEBUG: open_result_folder called. Path: {self.result_folder_path}") # Added log
        if self.result_folder_path:
            try:
                import os
                os.startfile(self.result_folder_path)
                self.log(f"フォルダを開きました: {self.result_folder_path}")
            except Exception as e:
                self.log(f"ファイルのオープンに失敗しました: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()