import json
import os

class ConfigManager:
    def __init__(self, config_file='config.json'):
        # 获取 %APPDATA% 目录并在其中创建应用配置目录
        appdata = os.getenv("APPDATA")
        config_dir = os.path.join(appdata, "GptOCR")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, config_file)
        
    def load(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        return {}

    def save(self, config):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)