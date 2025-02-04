import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import threading
import time
import logging
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)

class PixivDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("随机涩图下载器")
        self.root.geometry("400x400")  # 调整高度以适应更多控件
        self.dir_history = []  # 存储目录历史记录
        self.save_dir = tk.StringVar()  # 保存选择的目录
        self.create_widgets()

    def create_widgets(self):
        # 模式选择
        self.mode_label = tk.Label(self.root, text="模式:")
        self.mode_label.pack()
        self.mode = tk.StringVar()
        self.mode.set("json")  # 默认选择json模式
        self.mode_option = ttk.Combobox(self.root, textvariable=self.mode)
        self.mode_option['values'] = ('json', 'direct')
        self.mode_option.pack()

        # 关键词输入
        self.keyword_label = tk.Label(self.root, text="关键词:")
        self.keyword_label.pack()
        self.keyword_entry = tk.Entry(self.root, width=30)
        self.keyword_entry.pack()

        # R18选择
        self.r18_label = tk.Label(self.root, text="内容分级:")
        self.r18_label.pack()
        self.r18 = tk.StringVar()
        self.r18.set("2")  # 默认随机
        self.r18_option = ttk.Combobox(self.root, textvariable=self.r18)
        self.r18_option['values'] = ('0', '1', '2')
        self.r18_option.pack()

        # 下载数量
        self.num_label = tk.Label(self.root, text="下载数量:")
        self.num_label.pack()
        self.num = tk.StringVar()
        self.num.set("1")  # 默认1张
        self.num_option = ttk.Combobox(self.root, textvariable=self.num)
        self.num_option['values'] = list(range(1, 16))
        self.num_option.pack()

        # 下载目录选择
        self.dir_frame = tk.Frame(self.root)
        self.dir_frame.pack(fill=tk.X)

        self.dir_label = tk.Label(self.dir_frame, text="下载目录:")
        self.dir_label.pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(self.dir_frame, textvariable=self.save_dir, width=25)
        self.dir_entry.pack(side=tk.LEFT, expand=True)

        self.dir_button = tk.Button(self.dir_frame, text="浏览", command=self.browse_directory)
        self.dir_button.pack(side=tk.LEFT)

        # 代理设置
        self.proxy_frame = tk.Frame(self.root)
        self.proxy_frame.pack()

        self.proxy_label = tk.Label(self.proxy_frame, text="代理地址:")
        self.proxy_label.pack(side=tk.LEFT)
        self.proxy_entry = tk.Entry(self.proxy_frame, width=20)
        self.proxy_entry.insert(0, "i.pixiv.re")  # 默认代理
        self.proxy_entry.pack(side=tk.LEFT)

        # 是否使用代理
        self.use_proxy = tk.BooleanVar()
        self.use_proxy.set(True)  # 默认使用代理
        self.use_proxy_checkbox = tk.Checkbutton(self.proxy_frame, text="使用代理", variable=self.use_proxy)
        self.use_proxy_checkbox.pack(side=tk.LEFT)

        # 下载按钮
        self.download_button = tk.Button(self.root, text="下载", command=self.start_download)
        self.download_button.pack()

        # 状态显示
        self.status = tk.Label(self.root, text="准备就绪", wraplength=300)
        self.status.pack()

    def browse_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.save_dir.set(dir_path)
            # 更新目录历史
            if dir_path not in self.dir_history:
                self.dir_history.insert(0, dir_path)
            # 如果有需要，可以在Entry中显示历史记录
            # 这里可以添加自动完成功能，但为了简化，暂时不实现

    def start_download(self):
        try:
            num = int(self.num.get())
            if num < 1 or num > 15:
                messagebox.showerror("错误", "下载数量必须在1到15之间")
                return
        except ValueError:
            messagebox.showerror("错误", "下载数量必须是整数")
            return

        self.status['text'] = "正在获取图片..."
        self.download_button['state'] = 'disabled'
        threading.Thread(target=self.download_task).start()

    def download_task(self):
        try:
            base_url = "https://image.anosu.top/pixiv"
            if self.mode.get() == "json":
                endpoint = "/json"
            else:
                endpoint = "/direct"
                # 在direct模式下，num仅设置为1
                num = 1
            full_url = base_url + endpoint

            params = {
                "num": int(self.num.get()),
                "r18": self.r18.get(),
                "keyword": self.keyword_entry.get(),
                "proxy": self.proxy_entry.get() if self.use_proxy.get() else ""
            }

            if self.mode.get() == "direct":
                # 在direct模式下，num强制为1
                params["num"] = 1

            response = requests.get(full_url, params=params, timeout=10)
            if response.status_code == 200:
                if self.mode.get() == "json":
                    data = response.json()
                    if not data:
                        self.status['text'] = "没有找到符合条件的图片"
                        self.download_button['state'] = 'normal'
                        return

                    # 保存JSON数据到文件
                    if self.save_dir.get():
                        save_dir = self.save_dir.get()
                    else:
                        save_dir = filedialog.askdirectory()
                        if not save_dir:
                            self.status['text'] = "取消下载"
                            self.download_button['state'] = 'normal'
                            return
                        self.save_dir.set(save_dir)

                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                        logging.info(f"创建保存目录: {save_dir}")

                    # 生成JSON文件名
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = f"pixiv_data_{current_time}.json"
                    json_filepath = os.path.join(save_dir, json_filename)

                    try:
                        with open(json_filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        logging.info(f"成功保存JSON数据到文件: {json_filepath}")
                        self.status['text'] = f"成功保存JSON数据到文件: {json_filename}"
                    except Exception as e:
                        logging.error(f"保存JSON文件失败: {str(e)}")
                        self.status['text'] = f"保存JSON文件失败: {str(e)}"
                        self.download_button['state'] = 'normal'
                        return

                    # 分批次下载，避免速率限制
                    batch_size = 5  # 根据API限制调整
                    num_batches = (len(data) + batch_size - 1) // batch_size

                    for batch in range(num_batches):
                        start = batch * batch_size
                        end = min((batch + 1) * batch_size, len(data))
                        batch_data = data[start:end]

                        for i, item in enumerate(batch_data):
                            # 验证图片数据完整性
                            pid = item.get('pid', '')
                            p = item.get('p', '')
                            url = item.get('url', '')

                            if not pid or not p or not url:
                                logging.error(f"无效的图片数据: {item}")
                                self.status['text'] = f"无效的图片数据: {pid}_{p}"
                                continue

                            # 验证URL格式
                            if not url.startswith('http'):
                                logging.error(f"无效的图片URL: {url}")
                                self.status['text'] = f"无效的图片URL: {url}"
                                continue

                            # 替换代理
                            if self.use_proxy.get() and self.proxy_entry.get():
                                url = url.replace("i.pixiv.re", self.proxy_entry.get())
                                logging.info(f"使用代理后的URL: {url}")

                            # 定义文件名，去除非法字符
                            invalid_chars = '<>:"/\\|?*'
                            pid = pid.strip()
                            p = p.strip()
                            filename = f"{pid}_{p}.{url.split('.')[-1]}"
                            for char in invalid_chars:
                                filename = filename.replace(char, '')
                            filepath = os.path.join(save_dir, filename)

                            # 检查文件是否已存在
                            if os.path.exists(filepath):
                                logging.warning(f"文件已存在: {filepath}")
                                self.status['text'] = f"文件已存在: {filename}"
                                continue

                            # 处理API速率限制
                            retry = 0
                            max_retries = 3
                            downloaded = False
                            while retry < max_retries and not downloaded:
                                try:
                                    img_response = requests.get(url, timeout=10)
                                    img_response.raise_for_status()  # 抛出HTTP错误

                                    # 检查速率限制
                                    if 'x-ratelimit-remaining-tokens' in img_response.headers:
                                        remaining_tokens = int(img_response.headers['x-ratelimit-remaining-tokens'])
                                        if remaining_tokens < 100:
                                            # 如果剩余token少，增加延迟
                                            delay = int(img_response.headers.get('retry-after', 1))
                                            time.sleep(delay)
                                            logging.info(f"检测到速率限制，暂停{delay}秒...")
                                            self.status['text'] = f"检测到速率限制，暂停{delay}秒..."

                                    with open(filepath, 'wb') as f:
                                        f.write(img_response.content)
                                    logging.info(f"成功下载图片: {filename}")
                                    self.status['text'] = f"正在下载... ({start + i + 1}/{len(data)})"
                                    downloaded = True
                                except requests.exceptions.RequestException as e:
                                    # 检查是否是速率限制错误
                                    if isinstance(e, requests.exceptions.HTTPError):
                                        error_response = e.response
                                        if error_response.status_code == 413:
                                            error_data = json.loads(error_response.text)
                                            logging.error(f"API速率限制错误: {error_data.get('error', {}).get('message', '')}")
                                            self.status['text'] = f"API速率限制错误: {error_data.get('error', {}).get('message', '')}"
                                            # 根据提示调整延迟
                                            retry_after = int(error_data.get('error', {}).get('retry_after', 1))
                                            time.sleep(retry_after)
                                            logging.info(f"等待{retry_after}秒后重试...")
                                            self.status['text'] = f"等待{retry_after}秒后重试..."
                                            continue  # 不增加重试次数，直接继续

                                    logging.error(f"下载失败（第{retry + 1}次重试）: {str(e)}")
                                    self.status['text'] = f"下载失败（第{retry + 1}次重试）: {filename}"
                                    retry += 1
                                    time.sleep(1)  # 等待1秒后重试
                                except Exception as e:
                                    logging.error(f"保存失败: {str(e)}")
                                    self.status['text'] = f"保存失败: {filename}"
                                    retry += 1

                            if not downloaded:
                                logging.error(f"下载失败（已尝试{max_retries}次）: {filename}")
                                self.status['text'] = f"下载失败（已尝试{max_retries}次）: {filename}"

                            # 检查速率限制，添加延迟
                            if batch < num_batches - 1:
                                time.sleep(1)  # 根据API限制调整延迟时间

                    self.status['text'] = "下载完成！"
                else:
                    # 处理direct模式的响应
                    # 假设direct模式返回的是图片数据
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type:
                        # 生成文件名
                        filename = f"direct_download.{content_type.split('/')[-1]}"
                        # 使用自定义目录或默认目录
                        save_dir = self.save_dir.get() if self.save_dir.get() else os.getcwd()
                        filepath = os.path.join(save_dir, filename)
                      
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        self.status['text'] = f"成功下载图片: {filename}"
                    else:
                        self.status['text'] = "direct模式下未获取到图片数据"
            else:
                self.status['text'] = f"API请求失败: {response.status_code}"
          
            self.download_button['state'] = 'normal'
        except Exception as e:
            logging.error(f"下载任务失败: {str(e)}")
            self.status['text'] = f"错误: {str(e)}"
            self.download_button['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = PixivDownloader(root)
    root.mainloop()
