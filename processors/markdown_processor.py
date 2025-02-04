import re

class MarkdownProcessor:
    def __init__(self):
        self.inline_wrapper = '$ $'
        self.block_wrapper = '$$ $$'

    def set_wrappers(self, inline_wrapper: str, block_wrapper: str):
        self.inline_wrapper = inline_wrapper
        self.block_wrapper = block_wrapper

    def modify_wrappers(self, text: str) -> str:
        # 清理多余的 $$ 序列
        text = re.sub(r'\${3,}', '', text)
        
        # 处理行间公式
        block_wrappers = self.block_wrapper.split(' ')
        if len(block_wrappers) == 2:
            left_wrapper, right_wrapper = block_wrappers
            text = re.sub(r'\\\[(.*?)\\\]', 
                        lambda m: f'{left_wrapper}{m.group(1).strip()}{right_wrapper}', 
                        text, flags=re.DOTALL)
        
        # 处理行内公式
        inline_wrappers = self.inline_wrapper.split(' ')
        if len(inline_wrappers) == 2:
            left_inline, right_inline = inline_wrappers
            text = re.sub(r'\\\((.*?)\\\)', 
                        lambda m: f'{left_inline}{m.group(1).strip()}{right_inline}', 
                        text)
            
            # 清理单个 $ 和内容之间的空格
            text = re.sub(r'\$\s+([^\$]+?)\s+\$', r'$\1$', text)
        
        return text