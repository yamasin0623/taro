import warnings
# Python 3.14 で発生する Pydantic V1 の警告を非表示にする
warnings.filterwarnings("ignore", category=UserWarning, module="linebot")

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import os
import json

# LINE送信用のライブラリ
try:
    from linebot.v3.messaging import (
        Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
    )
except ImportError:
    print("ライブラリ不足: pip install line-bot-sdk")

CONFIG_FILE = "line_settings.json"

def clean_text(text):
    if not text: return ""
    text = text.translate(str.maketrans(
        '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
        '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    ))
    return re.sub(r'[^a-zA-Z0-9\-\.\_\~\+\/\=\s\:\/]', '', text).strip()

class LineSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("marketEase - URL送信特化モデル")
        self.root.geometry("600x500") # 画像項目を消したので高さを少し詰めました

        self.token = ""
        self.recipients = {}
        self.load_settings()

        self.create_menu()

        main_frame = tk.Frame(root, padx=20, pady=10)
        main_frame.pack(fill="both", expand=True)

        # 宛先選択
        select_frame = tk.Frame(main_frame)
        select_frame.pack(fill="x", pady=(0, 10))
        tk.Label(select_frame, text="送信先:", font=("MS Gothic", 10, "bold")).pack(side="left")
        self.recipient_combo = ttk.Combobox(select_frame, values=list(self.recipients.keys()), state="readonly", width=30)
        self.recipient_combo.pack(side="left", padx=10)
        if self.recipients: self.recipient_combo.current(0)

        # メッセージ入力
        tk.Label(main_frame, text="メッセージ (空欄でも可):", font=("MS Gothic", 10)).pack(anchor="w")
        self.text_area = scrolledtext.ScrolledText(main_frame, height=10, font=("MS Gothic", 11))
        self.text_area.pack(fill="both", expand=True, pady=5)

        # 送信ボタン
        self.send_btn = tk.Button(
            main_frame, text="ラインに送信する", command=self.send_message,
            bg="#06C755", fg="white", font=("MS Gothic", 12, "bold"), height=2
        )
        self.send_btn.pack(fill="x", pady=30, padx=50)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        setting_menu = tk.Menu(menubar, tearoff=0)
        setting_menu.add_command(label="アクセストークン設定", command=self.open_token_setting)
        setting_menu.add_command(label="宛先リストの管理", command=self.open_recipient_management)
        setting_menu.add_separator()
        setting_menu.add_command(label="終了", command=self.root.quit)
        menubar.add_cascade(label="設定", menu=setting_menu)
        self.root.config(menu=menubar)

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.token = data.get("token", "")
                    self.recipients = data.get("recipients", {"テスト宛先": ""})
            except:
                self.recipients = {"テスト宛先": ""}
        else:
            self.recipients = {"テスト宛先": ""}

    def save_to_file(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": self.token, "recipients": self.recipients}, f, ensure_ascii=False, indent=4)
        self.recipient_combo['values'] = list(self.recipients.keys())

    def open_token_setting(self):
        win = tk.Toplevel(self.root)
        win.title("トークン設定")
        tk.Label(win, text="LINE チャネルアクセストークン:").pack(pady=5)
        ent = tk.Entry(win, width=60)
        ent.insert(0, self.token)
        ent.pack(pady=5, padx=10)
        def save():
            self.token = clean_text(ent.get())
            self.save_to_file()
            messagebox.showinfo("保存", "トークンを保存しました")
            win.destroy()
        tk.Button(win, text="保存", command=save).pack(pady=10)

    def open_recipient_management(self):
        win = tk.Toplevel(self.root)
        win.title("宛先リストの管理")
        win.geometry("500x400")
        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.listbox = tk.Listbox(list_frame)
        self.listbox.pack(side="left", fill="both", expand=True)
        for name in self.recipients.keys(): self.listbox.insert(tk.END, name)
        edit_frame = tk.Frame(win, pady=10)
        edit_frame.pack(fill="x", padx=10)
        tk.Label(edit_frame, text="名前:").grid(row=0, column=0)
        name_ent = tk.Entry(edit_frame, width=15)
        name_ent.grid(row=0, column=1, padx=5)
        tk.Label(edit_frame, text="ユーザーID:").grid(row=0, column=2)
        id_ent = tk.Entry(edit_frame, width=25)
        id_ent.grid(row=0, column=3, padx=5)
        def add_item():
            name, uid = name_ent.get().strip(), clean_text(id_ent.get())
            if name and uid:
                self.recipients[name] = uid
                self.listbox.insert(tk.END, name)
                self.save_to_file()
            else: messagebox.showwarning("警告", "名前とIDを入力してください")
        tk.Button(edit_frame, text="追加", command=add_item).grid(row=1, column=1, pady=5)

    def send_message(self):
        name = self.recipient_combo.get()
        user_id = self.recipients.get(name)
        msg_text = self.text_area.get("1.0", tk.END).strip()

        # 固定URL
        target_url = "https://yamasin0623.github.io/taro/"

        if not self.token or not user_id:
            messagebox.showwarning("警告", "設定を確認してください。")
            return

        try:
            config = Configuration(host="https://api.line.me", access_token=self.token)
            with ApiClient(config) as api_client:
                line_bot_api = MessagingApi(api_client)
                
                # 入力されたテキストがあればそれとURLを合体、なければURLのみ
                full_text = f"{msg_text}\n\n{target_url}" if msg_text else target_url
                
                messages = [TextMessage(text=full_text)]
                line_bot_api.push_message(PushMessageRequest(to=user_id, messages=messages))
                
            messagebox.showinfo("成功", "ラインに送信しました！")
        except Exception as e:
            messagebox.showerror("失敗", f"エラー:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LineSenderApp(root)
    root.mainloop()