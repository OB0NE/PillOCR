import os
import sys

def get_absolute_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # 打包后的情况
        base_path = sys._MEIPASS
        # 适配 PyInstaller 6.0 及以上版本的 _internal 目录
        internal_path = os.path.join(base_path, '_internal')
        if os.path.exists(os.path.join(internal_path, relative_path)):
            base_path = internal_path
    except Exception:
        # 开发环境
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)