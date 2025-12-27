"""
图像处理辅助函数
从 MoviePilot-Plugins 移植并适配
"""
import math
import random
import colorsys
from collections import Counter
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def crop_to_square(img: Image.Image) -> Image.Image:
    """将图片裁剪为正方形"""
    width, height = img.size
    size = min(width, height)
    
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    
    return img.crop((left, top, right, bottom))


def add_rounded_corners(img: Image.Image, radius: int = 30) -> Image.Image:
    """
    给图片添加圆角，通过超采样技术消除锯齿
    
    Args:
        img: PIL.Image对象
        radius: 圆角半径
        
    Returns:
        带圆角的图片(RGBA模式)
    """
    # 超采样倍数
    factor = 2
    
    # 获取原始尺寸
    width, height = img.size
    
    # 创建更大尺寸的空白图像（用于超采样）
    enlarged_img = img.resize((width * factor, height * factor), Image.Resampling.LANCZOS)
    enlarged_img = enlarged_img.convert("RGBA")
    
    # 创建透明蒙版，尺寸为放大后的尺寸
    mask = Image.new('L', (width * factor, height * factor), 0)
    draw = ImageDraw.Draw(mask)
    
    draw.rounded_rectangle([(0, 0), (width * factor, height * factor)], 
                            radius=radius * factor, fill=255)
    
    # 创建超采样尺寸的透明背景
    background = Image.new("RGBA", (width * factor, height * factor), (255, 255, 255, 0))
    
    # 使用蒙版合成图像（在高分辨率下）
    high_res_result = Image.composite(enlarged_img, background, mask)
    
    # 将结果缩小回原来的尺寸，应用抗锯齿
    result = high_res_result.resize((width, height), Image.Resampling.LANCZOS)
    
    return result


def add_shadow_and_rotate(canvas: Image.Image, img: Image.Image, angle: float, 
                         offset: Tuple[int, int] = (10, 10), radius: int = 10, 
                         opacity: float = 0.5, center_pos: Tuple[int, int] = None) -> Image.Image:
    """
    先创建阴影并旋转放置，然后旋转图像并放置
    
    Args:
        canvas: 目标画布
        img: 需要处理的图像
        angle: 旋转角度
        offset: 阴影偏移
        radius: 阴影模糊半径
        opacity: 阴影透明度
        center_pos: 放置中心位置 (x, y)
        
    Returns:
        更新后的画布
    """
    width, height = img.size
    
    # 计算旋转后所需的画布尺寸
    diag = int(math.sqrt(width ** 2 + height ** 2))
    temp_canvas = Image.new("RGBA", (diag * 2, diag * 2), (0, 0, 0, 0))
    
    # 创建阴影蒙版
    shadow_mask = Image.new("L", (width, height), 0)
    shadow_draw = ImageDraw.Draw(shadow_mask)
    shadow_draw.rectangle([0, 0, width, height], fill=255)
    shadow_mask = add_rounded_corners(shadow_mask, radius=width//8).convert("L")
    
    # 创建阴影图层
    shadow_layer = Image.new("RGBA", (diag * 2, diag * 2), (0, 0, 0, 0))
    shadow_x = diag + offset[0]
    shadow_y = diag + offset[1]
    shadow_layer.paste((0, 0, 0, int(255 * opacity)), 
                      (shadow_x, shadow_y, width + shadow_x, height + shadow_y), 
                      shadow_mask)
    
    # 模糊阴影
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius))
    
    # 旋转阴影
    rotated_shadow = shadow_layer.rotate(angle, Image.BICUBIC, expand=False)
    
    # 放置图像到临时画布中心
    temp_canvas.paste(img, (diag - width // 2, diag - height // 2), img)
    
    # 旋转图像
    rotated_img = temp_canvas.rotate(angle, Image.BICUBIC, expand=False)
    
    # 合成到目标画布
    if center_pos:
        paste_x = center_pos[0] - rotated_shadow.width // 2
        paste_y = center_pos[1] - rotated_shadow.height // 2
        
        # 先放置阴影
        canvas.paste(rotated_shadow, (paste_x, paste_y), rotated_shadow)
        # 再放置图像
        canvas.paste(rotated_img, (paste_x, paste_y), rotated_img)
    
    return canvas


def darken_color(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
    """将颜色加深"""
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def is_not_black_white_gray_near(color: Tuple[int, int, int], threshold: int = 20) -> bool:
    """判断颜色既不是黑、白、灰，也不是接近黑、白"""
    r, g, b = color
    if (r < threshold and g < threshold and b < threshold) or \
       (r > 255 - threshold and g > 255 - threshold and b > 255 - threshold):
        return False
    gray_diff_threshold = 10
    if abs(r - g) < gray_diff_threshold and abs(g - b) < gray_diff_threshold and abs(r - b) < gray_diff_threshold:
        return False
    return True


def rgb_to_hsv(color: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """将 RGB 颜色转换为 HSV 颜色"""
    r, g, b = [x / 255.0 for x in color]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """将 HSV 颜色转换为 RGB 颜色"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def adjust_color_macaron(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    调整颜色使其更接近马卡龙风格：
    - 如果颜色太暗，增加亮度
    - 如果颜色太亮，降低亮度
    - 调整饱和度到适当范围
    """
    h, s, v = rgb_to_hsv(color)
    
    # 马卡龙风格的理想范围
    target_saturation_range = (0.3, 0.7)  # 饱和度范围
    target_value_range = (0.6, 0.85)      # 亮度范围
    
    # 调整饱和度
    if s < target_saturation_range[0]:
        s = target_saturation_range[0]
    elif s > target_saturation_range[1]:
        s = target_saturation_range[1]
    
    # 调整亮度
    if v < target_value_range[0]:
        v = target_value_range[0]  # 太暗，加亮
    elif v > target_value_range[1]:
        v = target_value_range[1]  # 太亮，加暗
    
    return hsv_to_rgb(h, s, v)


def color_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """计算两个颜色在HSV空间中的距离"""
    h1, s1, v1 = rgb_to_hsv(color1)
    h2, s2, v2 = rgb_to_hsv(color2)
    
    # 色调在环形空间中，需要特殊处理
    h_dist = min(abs(h1 - h2), 1 - abs(h1 - h2))
    
    # 综合距离，给予色调更高的权重
    return h_dist * 5 + abs(s1 - s2) + abs(v1 - v2)


def find_dominant_macaron_colors(image: Image.Image, num_colors: int = 5) -> List[Tuple[int, int, int]]:
    """
    从图像中提取主要颜色并调整为马卡龙风格：
    1. 过滤掉黑白灰颜色
    2. 从剩余颜色中找到出现频率最高的几种
    3. 调整这些颜色使其接近马卡龙风格
    4. 确保提取的颜色之间有足够的差异
    """
    # 缩小图片以提高效率
    img = image.copy()
    img.thumbnail((150, 150))
    img = img.convert('RGB')
    pixels = list(img.getdata())
    
    # 过滤掉黑白灰颜色
    filtered_pixels = [p for p in pixels if is_not_black_white_gray_near(p)]
    if not filtered_pixels:
        return []
    
    # 统计颜色出现频率
    color_counter = Counter(filtered_pixels)
    candidate_colors = color_counter.most_common(num_colors * 5)  # 提取更多候选颜色
    
    macaron_colors = []
    min_color_distance = 0.15  # 颜色差异阈值
    
    for color, _ in candidate_colors:
        # 调整为马卡龙风格
        adjusted_color = adjust_color_macaron(color)
        
        # 检查与已选颜色的差异
        if not any(color_distance(adjusted_color, existing) < min_color_distance for existing in macaron_colors):
            macaron_colors.append(adjusted_color)
            if len(macaron_colors) >= num_colors:
                break
    
    return macaron_colors


def add_film_grain(image: Image.Image, intensity: float = 0.05) -> Image.Image:
    """添加胶片颗粒效果"""
    img_array = np.array(image)
    
    # 创建随机噪点
    noise = np.random.normal(0, intensity * 255, img_array.shape)
    
    # 应用噪点
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)
