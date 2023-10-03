#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Dr.Sumアップロード
2023/09/26 S.Kanada
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import requests, json, time, threading

GETLIST_URL = "https://dsc0006sjp.drsum.com/api/v1.0/file/list"
UPDFILE_URL = "https://dsc0006sjp.drsum.com/api/v1.0/file/upload"
USERNAME = "u_rpa"
PASSWORD = "Cncgp135"
DIR_PATH = "D:/Shared/files/"
MAX_TIMEOUT = 900

# アップロード先フォルダ一覧取得
def get_dirlist():
    url = GETLIST_URL
    json_data = {'dir_path': DIR_PATH}
    auth = (USERNAME, PASSWORD)

    response = requests.post(url, json=json_data, auth=auth)

    if response.status_code == 200:
        data = response.json()
        folder_names = [item["name"] for item in data if item["type"] == "dir"]
        return folder_names
    else:
        return []

# コンボボックス選択
def select_dirlist(event):
    global dirname
    dirname = dirlist_combo.get()

# ファイル選択処理
def select_file():
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        set_entry(file_paths)
        upload_button.config(state=tk.NORMAL)

# ドロップ処理
def on_drop(event):
    file_paths = tuple(event.data.split())
    if file_paths:
        set_entry(file_paths)
        upload_button.config(state=tk.NORMAL)

# キャンセル
def cancel_window():
    root.destroy()

# クリア
def clear_file():
    global cancel_flg
    cancel_flg = True
    dirlist_combo.set("")
    tree.delete(*tree.get_children())
    upload_button.config(state=tk.DISABLED)

# 選択ファイル表示
def set_entry(file_paths):
    # ファイルパスをテーブルに追加
    for path in file_paths:
        add_path = True  # ファイルパスを追加するかどうかのフラグ

        for item in tree.get_children():
            values = tree.item(item, "values")
            if values and path == values[0]:
                # カラム1つ目の値と同じ場合
                if not values[1]:
                    # カラム2つ目の値が空でない場合はスキップ
                    add_path = False
                break

        if add_path:
            tree.insert("", "end", values=(path, ""))

# メッセージ表示
def show_popup_message(title, message):
    messagebox.showinfo(title, message)

# アップロードボタン
def loop_upd():
    file_paths = [(item, *tree.item(item, "values")) for item in tree.get_children()]
    for file_path in file_paths:
        # 未取込が対象
        if not file_path[2]:
            upload_file(file_path[1])

    global cancel_flg
    cancel_flg = False
    for file_path in file_paths:
        # 未取込が対象
        if not file_path[2]:
            if cancel_flg:
                break
            threading.Thread(target=get_filelist, args=(file_path[0],file_path[1])).start()

# アップロード処理
def upload_file(file_path):
    global dirname
    if not dirname:
        messagebox.showinfo("エラー","アップロードフォルダを選択してください。")
        return

    if file_path:
        url = UPDFILE_URL
        file_name = os.path.basename(file_path)
        dest_dir = f"{DIR_PATH}{dirname}"
        data = {'dest_dir': dest_dir, 'overwrite': 'true'}
        auth = (USERNAME, PASSWORD)

        with open(file_path, 'rb') as file:
            files = {'file': (file_name, file)}
            response = requests.post(url, data=data, auth=auth, files=files)

        if response.status_code in (200, 201):
            pass
        else:
            show_popup_message("エラー", f"アップロードエラー：{response.status_code} - {response.text}")

# ファイル一覧取得（インポート未済チェック）
def get_filelist(itemid, file_path):
    global dirname
    global cancel_flg
    start_time = time.time()

    while time.time() - start_time <= MAX_TIMEOUT:
        if cancel_flg:
            result = "ファイル監視を終了しました"
            update_result(itemid, result)
            break

        url = GETLIST_URL
        dir_path = f"{DIR_PATH}{dirname}"
        json_data = {'dir_path': dir_path}
        auth = (USERNAME, PASSWORD)

        response = requests.post(url, json=json_data, auth=auth)

        if response.status_code == 200:
            data = json.loads(response.text)
            for item in data:
                if item.get("name") == os.path.basename(file_path):
                    result = "ファイル取込中..."
                    update_result(itemid, result)
                    time.sleep(5)
                    break
            else:
                result = "ファイル取込完了しました。"
                update_result(itemid, result)
                break
        else:
            result = f"予期せぬエラー：{response.status_code} - {response.text}"
            update_result(itemid, result)
            break

    if time.time() - start_time > MAX_TIMEOUT:
        result = f"ファイル監視を終了しました\n（タイムアウト：{MAX_TIMEOUT}秒）"
        update_result(itemid, result)

# ファイルパスごとに結果を更新
def update_result(itemid, result):
    for item in tree.get_children():
        if item == itemid:
            current_values = tree.item(item, "values")
            tree.item(item, values=(current_values[0], result))
            break

# 画面設定
root = TkinterDnD.Tk()
root.title("Dr.Sum Uploader 【管理者】")
root.geometry("700x400")
font1, font2 = ("Meiryo", 10), ("Meiryo", 12)

# ウィジェット1：ファイル選択
file_group = tk.Frame(root)
file_group.pack(side=tk.TOP, padx=20, pady=20)

# フォルダ一覧コンボボックス
dirlist_combo = ttk.Combobox(file_group, state="readonly")
dirlist_combo.config(background="#FEDFE1", foreground="black", font=font2)
dirlist_combo.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
dirlist = get_dirlist()
dirlist_combo["values"] = dirlist
dirlist_combo.bind("<<ComboboxSelected>>", select_dirlist)

# ファイル選択ボタン
select_button = tk.Button(file_group, text="ファイルを選択", command=select_file)
select_button.config(bg="white", fg="black", font=font1)
select_button.pack(side=tk.LEFT, padx=10, pady=10, anchor=tk.N)

# クリアボタン
clear_button = tk.Button(file_group, text="クリア", command=clear_file, state=tk.NORMAL)
clear_button.config(bg="#D9D9D9", fg="#58B2DC", font=font1)
clear_button.pack(side=tk.RIGHT, padx=10, pady=10, anchor=tk.N)

# Treeviewウィジェットの作成
tree = ttk.Treeview(file_group, columns=("Path", "Result"), show="headings")
tree.heading("Path", text="ファイルパス")
tree.heading("Result", text="結果")
tree.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10, anchor=tk.W)  # fill=tk.BOTHを追加

# 列の幅を設定
tree.column("Path", width=290)
tree.column("Result", stretch=tk.YES)

# ウィジェットの幅に合わせて調整
tree.bind("<Configure>", lambda e: tree.column("Result", width=e.width - 300))

# ドロップターゲットの設定
file_group.drop_target_register(DND_FILES)
file_group.dnd_bind('<<Drop>>', on_drop)

# ウィジェット2: アップロード関連
upload_group = tk.Frame(root)
upload_group.pack(side=tk.BOTTOM, padx=20, pady=10, anchor=tk.E)

# キャンセルボタン
cancel_button = tk.Button(upload_group, text="キャンセル", command=cancel_window, state=tk.NORMAL)
cancel_button.config(bg="#81C7D4", fg="white", font=font2, disabledforeground="#D9D9D9")
cancel_button.pack(side=tk.RIGHT, padx=10)

# アップロードボタン
upload_button = tk.Button(upload_group, text="アップロード", command=loop_upd, state=tk.DISABLED)
upload_button.config(bg="#F596AA", fg="white", font=font2, disabledforeground="#D9D9D9")
upload_button.pack(side=tk.RIGHT, padx=5)

root.mainloop()
