import base64
import io
from PIL import Image

class ImageEncoder:
    def encode_image(self, image: Image.Image) -> str:
        """将图片编码为base64字符串"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return base64.b64encode(img_byte_arr).decode('utf-8')