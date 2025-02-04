import json
import requests
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import threading

class PixivDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pixiv图片下载工具")
        self.json_file_path = tk.StringVar()
        self.download_dir_path = tk.StringVar()
        self.log_text = tk.Text(self.root)
        self.setup_ui()

    def setup_ui(self):
        # 创建GUI组件
        # JSON文件路径
        tk.Label(self.root, text="JSON文件路径：").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.json_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.root, text="选择JSON文件", command=self.select_json_file).grid(row=0, column=2, padx=5, pady=5)

        # 保存目录路径
        tk.Label(self.root, text="保存目录：").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.download_dir_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.root, text="选择保存目录", command=self.select_download_dir).grid(row=1, column=2, padx=5, pady=5)

        # 开始下载按钮
        tk.Button(self.root, text="开始下载", command=self.start_download).grid(row=2, column=1, padx=5, pady=5)

        # 日志文本框
        self.log_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
        self.log_text.config(state="disabled")

    def select_json_file(self):
        # 选择JSON文件
        path = filedialog.askopenfilename(
            title="选择JSON文件",
            filetypes=[("JSON文件", "*.json")]
        )
        if path:
            self.json_file_path.set(path)

    def select_download_dir(self):
        # 选择保存目录
        dir_path = filedialog.askdirectory(
            title="选择保存目录",
            initialdir=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        if dir_path:
            self.download_dir_path.set(dir_path)

    def start_download(self):
        # 启动下载线程
        json_path = self.json_file_path.get()
        download_dir = self.download_dir_path.get()

        if not json_path:
            messagebox.showerror("错误", "请先选择JSON文件")
            return
        if not download_dir:
            if not os.path.exists("pixiv_downloads"):
                os.makedirs("pixiv_downloads")
            download_dir = "pixiv_downloads"
            self.download_dir_path.set(download_dir)
        
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        thread = threading.Thread(target=self.download_images, args=(json_path, download_dir))
        thread.start()

    def download_images(self, json_file_path, download_dir):
        # 下载图片的主逻辑
        try:
            self.update_log("加载JSON文件...")
            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                self.update_log(f"创建保存目录：{download_dir}")

            for item in json_data:
                url = item.get("url")
                title = item.get("title")

                if not url or not title:
                    self.update_log(f"缺少URL或title，跳过：{item}")
                    continue

                try:
                    self.update_log(f"开始下载：{url}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    file_ext = os.path.splitext(url)[1]
                    if not file_ext:
                        file_ext = ".png"

                    safe_title = re.sub(r'[\/\?<>\\:\*\|"]', '_', title)
                    safe_title = safe_title.replace(" ", "_")

                    filename = f"{download_dir}/{safe_title}{file_ext}"

                    if os.path.exists(filename):
                        base, ext = os.path.splitext(filename)
                        i = 1
                        while os.path.exists(filename):
                            filename = f"{base}_{i}{ext}"
                            i += 1

                    with open(filename, 'wb') as file:
                        file.write(response.content)

                    self.update_log(f"已下载并保存为：{filename}")

                except requests.exceptions.RequestException as e:
                    self.update_log(f"下载失败：{url}, 错误信息：{str(e)}")
                except Exception as e:
                    self.update_log(f"保存失败：{url}, 错误信息：{str(e)}")

        except json.JSONDecodeError as e:
            self.update_log(f"JSON解析失败：{str(e)}")
        except Exception as e:
            self.update_log(f"发生错误：{str(e)}")

    def update_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{self.get_current_time()}] {message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)
        self.root.update()

    def get_current_time(self):
        import time
        return time.strftime("%H:%M:%S")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    downloader = PixivDownloader()
    downloader.run()
