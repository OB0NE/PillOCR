import os
import re
import pystray
import pyperclip
import keyboard
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageGrab, ImageDraw, ImageTk
import time
from openai import OpenAI
import httpx
from utils.path_tools import get_absolute_path
from processors.image_encoder import ImageEncoder
from processors.markdown_processor import MarkdownProcessor
from utils.config_manager import ConfigManager

class ImageToMarkdown:
    def __init__(self, log_callback, app):
        self.log_callback = log_callback
        self.app = app
        self.running = False
        self.client = None
        self.gpt_model = 'gpt-4o'
        self.image_encoder = ImageEncoder()
        self.markdown_processor = MarkdownProcessor()
        self.current_provider = 'OPENAI'  # 添加服务商标识

    def set_provider(self, provider):
        """设置当前服务商"""
        self.current_provider = provider
        # if self.log_callback:
        #     self.log_callback(f"服务商已设置为: {provider}")

    def set_api_key(self, api_key):
        os.environ['OPENAI_API_KEY'] = api_key

    def set_proxy(self, proxy):
        """根据服务商设置代理和client"""
        try:
            if self.current_provider == 'OPENAI':
                if proxy:
                    self.client = OpenAI(
                        http_client=httpx.Client(
                            transport=httpx.HTTPTransport(proxy=proxy)
                        )
                    )
                else:
                    self.client = OpenAI()
            elif self.current_provider == '火山引擎':
                if proxy:
                    self.client = OpenAI(
                        base_url="https://ark.cn-beijing.volces.com/api/v3",
                        http_client=httpx.Client(
                            transport=httpx.HTTPTransport(proxy=proxy)
                        )
                    )
                else:
                    self.client = OpenAI(
                        base_url="https://ark.cn-beijing.volces.com/api/v3"
                    )
            elif self.current_provider == '自定义':
                # 从app获取用户设置的URL
                custom_url = self.app.url_var.get().strip()
                if not custom_url:
                    raise ValueError("自定义URL不能为空")
                    
                if proxy:
                    self.client = OpenAI(
                        base_url=custom_url,
                        http_client=httpx.Client(
                            transport=httpx.HTTPTransport(proxy=proxy)
                        )
                    )
                else:
                    self.client = OpenAI(
                        base_url=custom_url
                    )
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"设置客户端时出错: {str(e)}")

    def set_gpt_model(self, model_name):
        self.gpt_model = model_name

    def process_image(self, image):
        if not self.client:
            raise Exception("请先设置 API Key 或推理接入点")
        
        base64_img = f"data:image/png;base64,{self.image_encoder.encode_image(image)}"
        
        response = self.client.chat.completions.create(
            model=self.gpt_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Convert to markdown. Use LaTeX for formulas. Return only markdown content."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"{base64_img}"}
                        }
                    ],
                }
            ],
            max_tokens=1000,
        )
        
        markdown_content = response.choices[0].message.content
        markdown_content = re.sub(r'^```markdown\s*\n(.*?)\n```\s*$', r'\1', markdown_content, flags=re.DOTALL)
        return self.markdown_processor.modify_wrappers(markdown_content)

    def process_clipboard_image(self):
        last_image = None
        while self.running:
            try:
                image = ImageGrab.grabclipboard()
                if isinstance(image, Image.Image) and image != last_image:
                    self.log_callback("检测到新的剪贴板图像。")
                    self.app.update_icon_status('processing')

                    markdown_content = self.process_image(image)
                    pyperclip.copy(markdown_content)
                    self.log_callback("识别后的内容已复制到剪贴板。")

                    self.app.update_icon_status('success')
                    last_image = image
                time.sleep(1)
            except Exception as e:
                self.log_callback(f"发生错误: {e}")
                self.app.update_icon_status('error')
                self.running = False
                break

    def start(self):
        self.running = True
        threading.Thread(target=self.process_clipboard_image, daemon=True).start()

    def stop(self):
        self.running = False

    def set_wrappers(self, inline_wrapper: str, block_wrapper: str):
        """代理到 markdown_processor 的 set_wrappers 方法"""
        self.markdown_processor.set_wrappers(inline_wrapper, block_wrapper)

class App:
    def __init__(self, root, processor):
        self.processor = processor
        self.processor.app = self
        self.processor.log_callback = self.log
        self.config_manager = ConfigManager()
        self.provider_var = tk.StringVar(value='OPENAI')  # 确保 provider_var 在 load_settings 之前定义
        self.url_var = tk.StringVar(value='')
        self.log_text = tk.Text()  # 确保 log_text 在 load_settings 之前定义
        self.root = root
        self.root.title("OCR")
        self.root.configure(bg='#ffffff')
        
        # 配置 ttk 样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 设置风格
        primary_color = '#95ec69'  # 绿色，与成功状态的胶囊图标一致
        text_color = '#000000'    # 黑色文字
        bg_color = '#ffffff'      # 白色背景

        style.configure('TButton', padding=6, relief="flat",
                       background=primary_color, foreground=text_color)
        style.map('TButton',
                  background=[('active', primary_color)],
                  foreground=[('active', text_color)])
        style.configure('TLabel', background=bg_color, foreground=text_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color, 
                       foreground=text_color, font=('Segoe UI', 9))
        style.configure('TEntry', padding=6)
        style.configure('TCombobox', padding=6)

        # 初始化变量
        self.provider_var = tk.StringVar(value='OPENAI')
        self.api_key_var = tk.StringVar()
        self.proxy_var = tk.StringVar()
        self.model_var = tk.StringVar(value='gpt-4o')
        self.inline_var = tk.StringVar(value='$ $')
        self.block_var = tk.StringVar(value='$$ $$')

        # 定义服务商配置字典
        self.provider_settings = {
            'OPENAI': {
                'api_key': '',
                'proxy': '',
                'model': 'gpt-4o'
            },
            '火山引擎': {
                'api_key': '',
                'proxy': '',
                'model': ''
            },
            '自定义': {
                'url':'',
                'api_key': '',
                'proxy': '',
                'model': ''
            }
        }

        # 主容器，采用两栏布局
        main_frame = ttk.Frame(root, padding=20, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左右两栏
        left_frame = ttk.Frame(main_frame, style='TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 20))
        
        right_frame = ttk.Frame(main_frame, style='TFrame')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 左侧设置项
        self.provider_frame = ttk.LabelFrame(left_frame, text="服务商选择", padding=10, style='TLabelframe')
        self.provider_frame.pack(fill=tk.X, pady=(0, 10))
            # 添加服务商映射
        self.PROVIDER_MAPPING = {
            'OPENAI': 'OPENAI',
            '火山引擎': '火山引擎',
            '自定义': '自定义'
        }
            # 反向映射用于保存
        self.PROVIDER_REVERSE_MAPPING = {v: k for k, v in self.PROVIDER_MAPPING.items()}
        self.provider_dropdown = ttk.Combobox(self.provider_frame, 
                                            textvariable=self.provider_var,
                                            values=list(self.PROVIDER_MAPPING.values()),
                                            state='readonly')
        self.provider_dropdown.pack(fill=tk.X)
        self.provider_dropdown.bind('<<ComboboxSelected>>', self.on_provider_change)

        # 自定义 URL 配置，先隐藏，只有选择自定义才显示
        self.custom_url_frame = ttk.LabelFrame(left_frame, text="Base_Url", padding=10, style='TLabelframe')
        self.url_entry = ttk.Entry(self.custom_url_frame, textvariable=self.url_var)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(self.custom_url_frame, text="保存", command=self.save_custom_url).pack(side=tk.RIGHT)
        
        # API Key 设置
        api_frame = ttk.LabelFrame(left_frame, text="API Key", padding=10, style='TLabelframe')
        api_frame.pack(fill=tk.X, pady=(0, 10))

        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="•")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.save_api_button = ttk.Button(api_frame, text="保存", command=self.save_api_key)
        self.save_api_button.pack(side=tk.RIGHT)

        # 代理设置
        proxy_frame = ttk.LabelFrame(left_frame, text="代理设置", padding=10, style='TLabelframe')
        proxy_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(proxy_frame, text="HTTP代理:").pack(side=tk.LEFT)
        self.proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_var)
        self.proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(proxy_frame, text="保存", command=self.save_proxy).pack(side=tk.RIGHT)

        # 模型选择
        self.model_frame = ttk.LabelFrame(left_frame, text="模型选择（请确保模型具有视觉功能）", padding=10, style='TLabelframe')
        self.model_dropdown = ttk.Combobox(self.model_frame, textvariable=self.model_var,
                                           state='readonly')
        ttk.Button(self.model_frame, text="保存", command=self.save_model_choice).pack(side=tk.RIGHT)
        self.model_dropdown.pack(fill=tk.X)
        self.model_dropdown.bind('<<ComboboxSelected>>', self.save_model_choice)

        # 模型输入框
        self.model_entry_frame= ttk.LabelFrame(left_frame, text="模型（请确保模型具有视觉功能）", padding=10, style='TLabelframe')
        self.model_entry=ttk.Entry(self.model_entry_frame, textvariable=self.model_var)
        self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(self.model_entry_frame, text="保存", command=self.save_model_choice).pack(side=tk.RIGHT)

        # 推理接入点框架
        self.endpoint_frame = ttk.LabelFrame(left_frame, text="推理接入点（请确保模型具有视觉功能）", padding=10, style='TLabelframe')
        self.endpoint_entry = ttk.Entry(self.endpoint_frame, textvariable=self.model_var)
        self.endpoint_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(self.endpoint_frame, text="保存", command=self.save_model_choice).pack(side=tk.RIGHT)

        # LaTeX 设置
        latex_frame = ttk.LabelFrame(left_frame, text="LaTeX 设置", padding=10, style='TLabelframe')
        latex_frame.pack(fill=tk.X, pady=(0, 10))

        inline_frame = ttk.Frame(latex_frame, style='TFrame')
        inline_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(inline_frame, text="行内公式包装符:").pack(side=tk.LEFT)
        inline_combo = ttk.Combobox(inline_frame, textvariable=self.inline_var,
                                    values=['$ $', '\\( \\)'])
        inline_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        block_frame = ttk.Frame(latex_frame, style='TFrame')
        block_frame.pack(fill=tk.X)
        ttk.Label(block_frame, text="行间公式包装符:").pack(side=tk.LEFT)
        block_combo = ttk.Combobox(block_frame, textvariable=self.block_var,
                                   values=['$$ $$', '\\[ \\]'])
        block_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # 热键设置
        self.hotkey_var = tk.StringVar(value='ctrl+shift+o')  # 默认热键
        hotkey_frame = ttk.LabelFrame(left_frame, text="快捷键设置", padding=10, style='TLabelframe')
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))

        hotkey_input_frame = ttk.Frame(hotkey_frame, style='TFrame')
        hotkey_input_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(hotkey_input_frame, text="启动/停止快捷键:").pack(side=tk.LEFT)
        self.hotkey_entry = ttk.Entry(hotkey_input_frame, textvariable=self.hotkey_var)
        self.hotkey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        save_hotkey_button = ttk.Button(hotkey_input_frame, text="保存", command=self.save_hotkey)
        save_hotkey_button.pack(side=tk.RIGHT)

        # 右侧日志显示
        log_frame = ttk.LabelFrame(right_frame, text="日志", padding=10, style='TLabelframe')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = tk.Text(log_frame, height=6, font=('Consolas', 9),
                                bg='#f0f0f0', relief='flat', padx=5, pady=5)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 设置窗口图标
        icon_path = get_absolute_path('ocrgui.ico')
        icon_image = Image.open(icon_path)
        self.icon_photo = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(False, self.icon_photo)

        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)

        # 初始化其他组件
        self.icon = None
        self.icon_image = None
        self.running_state = False
        self.create_tray_icon()

        # 加载设置
        self.load_settings()

        # 绑定包装符变化
            # 添加防抖计时器
        self.debounce_timer = None
        self.last_wrapper_change = time.time()

        self.inline_var.trace_add('write', self.debounced_update_wrappers)
        self.block_var.trace_add('write', self.debounced_update_wrappers)

        self.processor.set_gpt_model(self.model_var.get())  # 确保在加载配置后更新模型设置

        # 自动开始处理
        self.root.after(1000, self.auto_start)
        #self.update_client_settings()
        # 初始隐藏推理接入点
        if self.provider_var.get() == 'OPENAI':
            self.model_frame.pack_forget()
            self.model_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
        elif self.provider_var.get() == '火山引擎':
            self.model_frame.pack_forget()
            self.endpoint_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
        elif self.provider_var.get() == '自定义':
            self.model_frame.pack_forget()

    def debounced_update_wrappers(self, *args):
        """防抖包装符更新"""
        DEBOUNCE_TIME = 2.0  # 1秒防抖时间
        
        # 取消之前的定时器
        if self.debounce_timer:
            self.debounce_timer.cancel()
            
        # 创建新定时器
        self.debounce_timer = threading.Timer(DEBOUNCE_TIME, self.update_wrappers)
        self.debounce_timer.start()

    def auto_start(self):
        self.start_processing()
        self.running_state = True
        self.icon.menu = self.create_menu()

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def update_wrappers(self):
        """更新包装符并保存配置"""
        inline_wrapper = self.inline_var.get()
        block_wrapper = self.block_var.get()
        self.processor.set_wrappers(inline_wrapper, block_wrapper)
        self.save_settings()  # 自动保存配置
        self.log(f"已更新并保存LaTeX包装符设置")

    def save_hotkey(self):
        """保存快捷键设置"""
        try:
            # 先取消旧快捷键
            self.unregister_hotkey()
            # 保存新快捷键并注册
            self.register_hotkey()
            self.save_settings()
            self.log(f"启动/停止快捷键已设置为: {self.hotkey_var.get()}")
        except Exception as e:
            self.log(f"快捷键设置失败: {e}")

    def register_hotkey(self):
        """注册全局热键"""
        try:
            keyboard.add_hotkey(self.hotkey_var.get(), self.toggle_processing)
            self.log(f"已注册快捷键: {self.hotkey_var.get()}")
        except Exception as e:
            self.log(f"注册快捷键失败: {e}")

    def unregister_hotkey(self):
        """取消注册热键"""
        try:
            keyboard.remove_hotkey(self.hotkey_var.get())
        except:
            pass  # 忽略可能的错误，如热键尚未注册

    def start_processing(self):
        self.processor.start()
        self.update_icon_status('success')
        self.running_state = True
        self.icon.menu = self.create_menu()  # 更新菜单
        self.log("已开始处理")

    def stop_processing(self):
        self.processor.stop()
        if self.icon:
            self.icon.icon = self.icon_image['processing']  # 改用 'processing' 状态
        self.running_state = False
        self.icon.menu = self.create_menu()  # 更新菜单
        self.log("已停止处理")

    def create_tray_icon(self):
        width, height = 64, 32
        base_icon = self.create_capsule_icon('grey')
        self.icon_image = {
            'processing': self.create_capsule_icon('grey'),
            'success': self.create_capsule_icon('green'),
            'error': self.create_capsule_icon('red'),
        }
        self.icon = pystray.Icon(
            "name",
            base_icon,
            "PillOCR"
        )
        self.icon.menu = self.create_menu()
        threading.Thread(target=self.icon.run, daemon=True).start()

    def create_menu(self):
        """创建托盘菜单"""
        return pystray.Menu(
            pystray.MenuItem(
                "停止" if self.running_state else "启动",  # 使用 self.running_state
                self.toggle_processing
            ),
            pystray.MenuItem("设置", self.show_window),
            pystray.MenuItem("退出", self.quit_app)
        )

    def toggle_processing(self, icon=None, item=None):
        """切换启动/停止状态"""
        if self.running_state:
            self.stop_processing()
        else:
            self.start_processing()
        # 更新菜单
        self.icon.menu = self.create_menu()

    def create_capsule_icon(self, color):
        scale = 4
        base_width, base_height = 24, 24
        width, height = base_width * scale, base_height * scale

        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if (color == 'grey'):
            fill = (128, 128, 128, 255)
        elif (color == 'green'):
            fill = (0, 255, 0, 255)
        elif (color == 'red'):
            fill = (255, 0, 0, 255)
        else:
            fill = (0, 255, 0, 255)  # 默认使用绿色
        
        capsule_height = 12 * scale
        capsule_width = 24 * scale
        
        x = (width - capsule_width) // 2
        y = (height - capsule_height) // 2
        
        draw.ellipse([x, y, x + capsule_height, y + capsule_height], fill=fill, outline=None)
        draw.ellipse([x + capsule_width - capsule_height, y, x + capsule_width, y + capsule_height], fill=fill, outline=None)
        draw.rectangle([x + capsule_height//2, y, x + capsule_width - capsule_height//2, y + capsule_height], fill=fill, outline=None)
        
        image = image.resize((base_width, base_height), Image.Resampling.LANCZOS)
        
        return image

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()

    def quit_app(self):
        self.unregister_hotkey()  # 取消热键注册
        self.processor.stop()
        if self.icon:
            self.icon.stop()
        self.root.destroy()  # 修改为 destroy 以立即关闭窗口和主循环

    def update_icon_status(self, status):
        if hasattr(self, 'icon') and self.icon and self.icon._running:
            try:
                self.icon.icon = self.icon_image[status]  # 直接设置图标
            except Exception as e:
                print(f"更新图标失败: {e}")

    def update_client_settings(self):
        """更新 ImageToMarkdown 处理器的设置"""
        current_provider = self.provider_var.get()
        settings = self.provider_settings.get(current_provider, {})
        
        # 更新API Key
        self.processor.set_api_key(settings.get('api_key', ''))
        
        # 更新代理
        self.processor.set_proxy(settings.get('proxy', ''))
        
        # 更新模型
        if current_provider == 'OPENAI':
            self.processor.set_gpt_model(settings.get('model', 'gpt-4o'))
        elif current_provider == '火山引擎':
            self.processor.set_gpt_model(settings.get('model', ''))
        elif current_provider == '自定义':
            self.processor.set_gpt_model(settings.get('model', ''))

    def apply_provider_settings(self):
        """处理和切换服务商相关的 UI 界面更新和组件显示"""
        current_provider = self.provider_var.get()
        settings = self.provider_settings.get(current_provider, {})
        
        if (current_provider == 'OPENAI'):
            self.processor.set_provider('OPENAI')
        elif (current_provider == '火山引擎'):
            self.processor.set_provider('火山引擎')
        elif current_provider == '自定义':
            self.processor.set_provider('自定义')
        
        if current_provider == 'OPENAI':
            # OpenAI 特定设置
            self.api_key_var.set(settings.get('api_key', ''))
            self.proxy_var.set(settings.get('proxy', ''))
            self.model_var.set(settings.get('model', 'gpt-4o'))
            # UI更新
            self.model_entry_frame.pack_forget()
            self.endpoint_frame.pack_forget()
            self.model_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
        elif current_provider == '火山引擎':
            # 火山引擎特定设置
            self.api_key_var.set(settings.get('api_key', ''))
            self.proxy_var.set(settings.get('proxy', ''))
            self.model_var.set(settings.get('model', ''))
            # UI更新
            self.model_frame.pack_forget()
            self.model_entry_frame.pack_forget()
            self.endpoint_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
        elif current_provider == '自定义':
            # 读取自定义URL, 如果需要可以在 self.provider_settings['自定义'] 中添加 url
            self.url_var.set(settings.get('url', ''))
            self.api_key_var.set(settings.get('api_key', ''))
            self.proxy_var.set(settings.get('proxy', ''))
            self.model_var.set(settings.get('model', ''))
            # 自定义场景下可根据需求显示/隐藏 UI
            self.model_frame.pack_forget()
            self.endpoint_frame.pack_forget()
            self.custom_url_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
            self.model_entry_frame.pack(after=self.custom_url_frame, fill=tk.X, pady=(0, 10))
        
        # 确保在应用设置时更新客户端
        self.update_client_settings()

    def save_settings(self):
        """保存所有设置"""
        display_provider = self.provider_var.get()
        current_provider = self.PROVIDER_REVERSE_MAPPING[display_provider]
        
        if current_provider == 'OPENAI':
            settings = {
                'api_key': self.api_key_var.get().strip(),
                'proxy': self.proxy_var.get().strip(),
                'model': self.model_var.get().strip()
            }
        elif current_provider == '火山引擎':
            settings = {
                'api_key': self.api_key_var.get().strip(),
                'proxy': self.proxy_var.get().strip(),
                'model': self.model_var.get().strip()
            }
        elif current_provider == '自定义':
            # 保存自定义URL
            settings = {
                'url': self.url_var.get().strip(),
                'api_key': self.api_key_var.get().strip(),
                'proxy': self.proxy_var.get().strip(),
                'model': self.model_var.get().strip()
            }
            
        self.provider_settings[current_provider] = settings
        
        # 添加LaTeX包装符设置
        config = {
            'current_provider': current_provider,
            'provider_settings': self.provider_settings,
            'latex_settings': {
                'inline_wrapper': self.inline_var.get(),
                'block_wrapper': self.block_var.get()
            },
            'hotkey': self.hotkey_var.get()
        }
        
        try:
            self.config_manager.save(config)
            self.update_client_settings()
        except Exception as e:
            self.log(f"保存设置失败: {e}")

    def on_provider_change(self, event=None):
        """切换服务商"""
        display_provider = self.provider_dropdown.get()
        self.provider_var.set(display_provider)  # 直接使用显示名称
        
        # 根据供应商设置不同的模型
        if display_provider == 'OPENAI':
            self.model_dropdown['values'] = ['gpt-4o', 'gpt-4o-mini']
        else:
            self.model_dropdown['values'] = []

        # 默认选择列表中的第一个模型
        if self.model_dropdown['values']:
            self.model_var.set(self.model_dropdown['values'][0])

        # 显示/隐藏自定义 URL 框
        if display_provider == '自定义':
            # 在 provider_frame 下方插入
            self.custom_url_frame.pack(after=self.provider_frame, fill=tk.X, pady=(0, 10))
        else:
            self.custom_url_frame.pack_forget()

        # 加载新服务商配置
        self.apply_provider_settings()
        self.log(f"已切换到 {display_provider} 服务")

    def save_custom_url(self):
        """保存自定义URL并更新设置"""
        self.save_settings()
        self.log(f"已保存自定义URL: {self.url_var.get()}")

    def save_api_key(self):
        """保存 API Key"""
        self.save_settings()
        self.log("API Key已保存")

    def save_proxy(self):
        """保存代理设置"""
        self.save_settings()
        self.log("代理设置已保存")

    def save_model_choice(self, event=None):
        """保存模型选择到配置文件"""
        model_choice = self.model_var.get()  # 获取当前选择的模型
        self.save_settings()
        self.log(f"模型已设置为: {model_choice}")

    def load_settings(self):
        """从配置文件加载设置到内存"""
        try:
            config = self.config_manager.load()

            # 仅当 config 中不存在 provider_settings 时才使用默认
            if 'provider_settings' not in config:
                self.provider_settings = {
                    'OPENAI': {'api_key': '', 'proxy': '', 'model': 'gpt-4o'},
                    '火山引擎': {'api_key': '', 'proxy': '', 'model': ''},
                    '自定义': {'url': '', 'api_key': '', 'proxy': '', 'model': ''}
                }
            else:
                self.provider_settings = config['provider_settings']
                current_provider = config.get('current_provider', 'OPENAI')
                self.provider_var.set(current_provider)
            
            # 加载LaTeX包装符设置
            latex_settings = config.get('latex_settings', {
                'inline_wrapper': '$ $',
                'block_wrapper': '$$ $$'
            })
            self.inline_var.set(latex_settings['inline_wrapper'])
            self.block_var.set(latex_settings['block_wrapper'])

            # 将包装符应用到处理器
            self.processor.set_wrappers(
                self.inline_var.get(), 
                self.block_var.get()
            )
            
            # 加载热键设置
            self.hotkey_var.set(config.get('hotkey', 'ctrl+shift+o'))
            self.register_hotkey()  # 注册热键

            # 更新所有设置
            self.apply_provider_settings()
        except Exception as e:
            self.log(f"加载配置失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x700+{}+{}".format(
        root.winfo_screenwidth() // 2 - 400,  # 水平居中
        root.winfo_screenheight() // 2 - 400  # 垂直居中
    ))  # 调整窗口大小以适应新布局
    # 在创建窗口后立即隐藏
    root.withdraw()
    processor = ImageToMarkdown(None, None)
    app = App(root, processor)

    # 更新 processor 的引用
    processor.log_callback = app.log
    processor.app = app
    root.withdraw()
    app.update_icon_status('success')
    root.mainloop()