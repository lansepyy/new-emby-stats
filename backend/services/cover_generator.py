"""
媒体库封面生成服务
整合 jellyfin-library-poster 和 MoviePilot-Plugins 的封面生成功能
"""
import os
import io
import math
import random
import colorsys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from datetime import datetime

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import numpy as np

from config import settings
from services.emby import EmbyService
from services.image_utils import (
    crop_to_square, add_rounded_corners, add_shadow_and_rotate,
    darken_color, find_dominant_macaron_colors, add_film_grain,
    align_image_right, create_diagonal_mask, create_shadow_mask
)

logger = logging.getLogger(__name__)


# ==================== 通用工具函数 ====================

def is_not_black_white_gray_near(color, threshold=20):
    """判断颜色既不是黑、白、灰，也不是接近黑、白。"""
    r, g, b = color
    if (r < threshold and g < threshold and b < threshold) or \
       (r > 255 - threshold and g > 255 - threshold and b > 255 - threshold):
        return False
    gray_diff_threshold = 10
    if abs(r - g) < gray_diff_threshold and abs(g - b) < gray_diff_threshold and abs(r - b) < gray_diff_threshold:
        return False
    return True


def rgb_to_hsv(color):
    """将 RGB 颜色转换为 HSV 颜色。"""
    r, g, b = [x / 255.0 for x in color]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(h, s, v):
    """将 HSV 颜色转换为 RGB 颜色。"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def adjust_color_macaron(color):
    """调整颜色使其更接近马卡龙风格"""
    h, s, v = rgb_to_hsv(color)
    
    target_saturation_range = (0.3, 0.7)
    target_value_range = (0.6, 0.85)
    
    if s < target_saturation_range[0]:
        s = target_saturation_range[0]
    elif s > target_saturation_range[1]:
        s = target_saturation_range[1]
    
    if v < target_value_range[0]:
        v = target_value_range[0]
    elif v > target_value_range[1]:
        v = target_value_range[1]
    
    return hsv_to_rgb(h, s, v)


def find_dominant_macaron_colors(image, num_colors=5):
    """从图像中提取主要颜色并调整为马卡龙风格"""
    img = image.copy()
    img.thumbnail((150, 150))
    img = img.convert('RGB')
    pixels = list(img.getdata())
    
    filtered_pixels = [p for p in pixels if is_not_black_white_gray_near(p)]
    if not filtered_pixels:
        return []
    
    color_counter = Counter(filtered_pixels)
    candidate_colors = color_counter.most_common(num_colors * 5)
    
    macaron_colors = []
    min_color_distance = 0.15
    
    def color_distance(color1, color2):
        h1, s1, v1 = rgb_to_hsv(color1)
        h2, s2, v2 = rgb_to_hsv(color2)
        h_dist = min(abs(h1 - h2), 1 - abs(h1 - h2))
        return h_dist * 5 + abs(s1 - s2) + abs(v1 - v2)
    
    for color, _ in candidate_colors:
        adjusted_color = adjust_color_macaron(color)
        if not any(color_distance(adjusted_color, existing) < min_color_distance for existing in macaron_colors):
            macaron_colors.append(adjusted_color)
            if len(macaron_colors) >= num_colors:
                break
    
    return macaron_colors


def add_film_grain(image, intensity=0.05):
    """添加胶片颗粒效果"""
    img_array = np.array(image)
    noise = np.random.normal(0, intensity * 255, img_array.shape)
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array)


def add_shadow(img, offset=(5, 5), shadow_color=(0, 0, 0, 100), blur_radius=3):
    """给图片添加阴影效果"""
    shadow_width = img.width + offset[0] + blur_radius * 2
    shadow_height = img.height + offset[1] + blur_radius * 2
    
    shadow = Image.new("RGBA", (shadow_width, shadow_height), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", img.size, shadow_color)
    shadow.paste(shadow_layer, (blur_radius + offset[0], blur_radius + offset[1]))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    
    result = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    result.paste(img, (blur_radius, blur_radius), img if img.mode == "RGBA" else None)
    shadow_img = Image.alpha_composite(shadow, result)
    
    return shadow_img


def create_gradient_background(width, height, color=None):
    """创建渐变背景"""
    def is_mid_bright_hsl(input_rgb, min_l=0.3, max_l=0.7):
        r, g, b = input_rgb[:3] if len(input_rgb) >= 3 else (128, 128, 128)
        r1, g1, b1 = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(r1, g1, b1)
        return min_l <= l <= max_l
    
    selected_color = None
    
    if isinstance(color, list) and len(color) > 0:
        for c in color[:10]:
            if is_mid_bright_hsl(c):
                selected_color = c[:3] if len(c) >= 3 else c
                break
    
    if selected_color is None:
        h = random.uniform(0, 1)
        s = random.uniform(0.4, 0.7)
        l = random.uniform(0.45, 0.65)
        selected_color = tuple(int(x * 255) for x in colorsys.hls_to_rgb(h, l, s))
    
    base_color = selected_color
    left_color = tuple(max(0, int(c * 0.7)) for c in base_color)
    right_color = base_color
    
    gradient = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(gradient)
    
    for x in range(width):
        ratio = x / width
        r = int(left_color[0] * (1 - ratio) + right_color[0] * ratio)
        g = int(left_color[1] * (1 - ratio) + right_color[1] * ratio)
        b = int(left_color[2] * (1 - ratio) + right_color[2] * ratio)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return gradient


# ==================== 封面生成器类 ====================

class CoverGeneratorService:
    """封面生成服务 - 整合多种风格"""
    
    # 海报生成配置
    POSTER_CONFIG = {
        "ROWS": 3,
        "COLS": 3,
        "MARGIN": 22,
        "CORNER_RADIUS": 46,
        "ROTATION_ANGLE": -15.8,
        "START_X": 835,
        "START_Y": -362,
        "COLUMN_SPACING": 100,
        "CELL_WIDTH": 410,
        "CELL_HEIGHT": 610,
        "CANVAS_WIDTH": 1920,
        "CANVAS_HEIGHT": 1080,
    }
    
    def __init__(self):
        self.emby_service = EmbyService()
        self.cache_dir = Path("/tmp/cover_cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # 字体路径 - 在Docker容器中使用绝对路径
        self.font_dir = Path("/app/res/fonts")
        if not self.font_dir.exists():
            # 如果容器路径不存在，尝试相对路径（用于本地开发）
            self.font_dir = Path(__file__).parent.parent.parent / "res" / "fonts"
            self.font_dir.mkdir(exist_ok=True, parents=True)
        
        # 记录字体目录和文件状态
        logger.info(f"字体目录: {self.font_dir}")
        logger.info(f"字体目录是否存在: {self.font_dir.exists()}")
        if self.font_dir.exists():
            font_files = list(self.font_dir.glob("*"))
            logger.info(f"字体目录中的文件: {[f.name for f in font_files]}")

    
    async def get_library_list(self) -> List[Dict[str, Any]]:
        """获取媒体库列表"""
        try:
            api_key = await self.emby_service.get_api_key()
            if not api_key:
                logger.error("无法获取API密钥")
                return []
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{settings.EMBY_URL}/Library/MediaFolders",
                    headers={"Authorization": f'MediaBrowser Token="{api_key}"'}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    libraries = []
                    if "Items" in data:
                        for item in data["Items"]:
                            if "Id" in item and "Name" in item:
                                libraries.append({
                                    "id": item["Id"],
                                    "name": item["Name"],
                                    "type": item.get("CollectionType", "unknown")
                                })
                    return libraries
        except Exception as e:
            logger.error(f"获取媒体库列表失败: {e}")
        
        return []
    
    async def get_library_items(self, library_id: str, limit: int = 50, sort_by: str = "DateCreated", start_index: int = 0) -> List[Dict[str, Any]]:
        """获取媒体库中的项目,支持分页"""
        try:
            api_key = await self.emby_service.get_api_key()
            user_id = await self.emby_service.get_user_id()
            
            if not api_key or not user_id:
                return []
            
            url = f"{settings.EMBY_URL}/Users/{user_id}/Items"
            params = {
                "ParentId": library_id,
                "Recursive": "true",
                "SortBy": sort_by,
                "SortOrder": "Descending",
                "IncludeItemTypes": "Movie,Series,Audio,Music,Game,Book,MusicVideo,BoxSet",
                "Limit": limit,
                "StartIndex": start_index,
                "Fields": "PrimaryImageAspectRatio,ImageTags,BackdropImageTags,ParentBackdropImageTags",
                "api_key": api_key
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("Items", [])
        except Exception as e:
            logger.error(f"获取媒体库项目失败: {e}")
        
        return []
    
    async def download_poster(self, item_id: str, item_name: str) -> Optional[bytes]:
        """下载单个海报"""
        try:
            api_key = await self.emby_service.get_api_key()
            if not api_key:
                return None
            
            # 尝试获取主图
            url = f"{settings.EMBY_URL}/Items/{item_id}/Images/Primary"
            params = {"api_key": api_key, "maxWidth": 500}
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.error(f"下载海报失败 {item_name}: {e}")
        
        return None
    
    def _get_font_path(self) -> Path:
        """获取字体文件路径"""
        # 优先使用项目字体
        font_candidates = [
            self.font_dir / "SourceHanSansSC-Bold.otf",
            self.font_dir / "SourceHanSansSC-Regular.otf",
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("C:\\Windows\\Fonts\\msyh.ttc"),
        ]
        
        for font_path in font_candidates:
            if font_path.exists():
                return font_path
        
        # 返回默认字体路径（即使不存在，PIL会使用默认字体）
        return self.font_dir / "default.ttf"
    
    def _add_title_overlay(
        self,
        canvas: Image.Image,
        title: str,
        subtitle: str = "",
        color: tuple = (100, 150, 200, 255)
    ) -> Image.Image:
        """在画布左侧添加标题叠加层
        
        Args:
            canvas: 原始画布图像
            title: 主标题(中文)
            subtitle: 副标题(英文)  
            color: 色块颜色 RGBA
            
        Returns:
            添加了标题的画布
        """
        draw = ImageDraw.Draw(canvas)
        
        # 加载字体（使用MoviePilot-Plugins的字体）
        zh_font_path = self.font_dir / "multi_1_zh.ttf"
        en_font_path = self.font_dir / "multi_1_en.otf"
        
        logger.info(f"动图标题字体路径: 中文={zh_font_path}, 英文={en_font_path}")
        
        # 中文标题字体 163px
        if zh_font_path.exists():
            title_font = ImageFont.truetype(str(zh_font_path), 163)
            logger.info(f"动图中文字体加载成功")
        else:
            logger.warning(f"中文字体不存在: {zh_font_path}, 使用默认字体")
            title_font = ImageFont.load_default()
        
        # 英文副标题字体 50px
        if en_font_path.exists():
            subtitle_font = ImageFont.truetype(str(en_font_path), 50)
            logger.info(f"动图英文字体加载成功")
        else:
            logger.warning(f"英文字体不存在: {en_font_path}, 使用默认字体")
            subtitle_font = ImageFont.load_default()
        
        # 色块位置和大小 (84, 620, 22x65)
        block_x, block_y = 84, 620
        block_width, block_height = 22, 65
        draw.rectangle(
            [(block_x, block_y), (block_x + block_width, block_y + block_height)],
            fill=color
        )
        
        # 中文标题位置 (73, 427)
        title_x, title_y = 73, 427
        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=(255, 255, 255, 255)
        )
        
        # 英文副标题位置 (125, 625)
        if subtitle:
            subtitle_x, subtitle_y = 125, 625
            draw.text(
                (subtitle_x, subtitle_y),
                subtitle,
                font=subtitle_font,
                fill=(255, 255, 255, 255)
            )
        
        return canvas
    
    async def _fetch_posters(self, library_id: str, count: int = 9) -> List[Image.Image]:
        """获取海报图片列表"""
        items = await self.get_library_items(library_id, limit=count * 2)
        if not items:
            logger.warning(f"未获取到媒体库 {library_id} 的项目")
            return []
        
        posters = []
        for item in items[:count]:
            poster_data = await self.download_poster(item["Id"], item["Name"])
            if poster_data:
                try:
                    img = Image.open(io.BytesIO(poster_data))
                    posters.append(img)
                    if len(posters) >= count:
                        break
                except Exception as e:
                    logger.error(f"打开海报失败: {e}")
        
        return posters
    
    def draw_text_with_shadow(
        self,
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
        shadow_offset: Tuple[int, int] = (2, 2)
    ) -> Image.Image:
        """在图像上绘制带阴影的文字"""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # 绘制阴影
        shadow_pos = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
        draw.text(shadow_pos, text, font=font, fill=shadow_color)
        
        # 绘制文字
        draw.text(position, text, font=font, fill=fill_color)
        
        return img_copy
    
    def _draw_text_on_image(
        self,
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        shadow: bool = False,
        shadow_color: Optional[Tuple[int, int, int]] = None,
        shadow_offset: int = 10,
        shadow_alpha: int = 75
    ) -> Image.Image:
        """在图像上绘制文字，可选择添加阴影效果（参考MoviePilot）"""
        img_copy = image.copy()
        text_layer = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
        shadow_layer = Image.new('RGBA', img_copy.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        shadow_draw = ImageDraw.Draw(shadow_layer)
        
        # 如果需要添加阴影
        if shadow:
            fill_color = (fill_color[0], fill_color[1], fill_color[2], 229)
            if shadow_color is None:
                if len(fill_color) >= 3:
                    r = max(0, int(fill_color[0] * 0.7))
                    g = max(0, int(fill_color[1] * 0.7))
                    b = max(0, int(fill_color[2] * 0.7))
                    shadow_color_with_alpha = (r, g, b, shadow_alpha)
                else:
                    shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
            else:
                if len(shadow_color) == 3:
                    shadow_color_with_alpha = shadow_color + (shadow_alpha,)
                elif len(shadow_color) == 4:
                    shadow_color_with_alpha = shadow_color[:3] + (shadow_alpha,)
                else:
                    shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
            
            for offset in range(3, shadow_offset + 1, 2):
                shadow_draw.text(
                    (position[0] + offset, position[1] + offset),
                    text,
                    font=font,
                    fill=shadow_color_with_alpha
                )
        
        # 绘制主文字
        draw.text(position, text, font=font, fill=fill_color)
        blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_offset))
        combined = Image.alpha_composite(img_copy, blurred_shadow)
        img_copy = Image.alpha_composite(combined, text_layer)
        
        return img_copy
    
    def _draw_multiline_text_on_image(
        self,
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        line_spacing: int = 10,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        shadow: bool = False,
        shadow_color: Optional[Tuple[int, int, int]] = None,
        shadow_offset: int = 4,
        shadow_alpha: int = 100
    ) -> Tuple[Image.Image, int]:
        """在图像上绘制多行文字，根据空格自动换行（参考MoviePilot）"""
        img_copy = image.copy()
        text_layer = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # 按空格分割文本
        lines = text.split(" ")
        
        # 如果未指定阴影颜色，则根据填充颜色生成
        if shadow:
            fill_color = (fill_color[0], fill_color[1], fill_color[2], 229)
            if shadow_color is None:
                if len(fill_color) >= 3:
                    r = max(0, int(fill_color[0] * 0.7))
                    g = max(0, int(fill_color[1] * 0.7))
                    b = max(0, int(fill_color[2] * 0.7))
                    shadow_color_with_alpha = (r, g, b, shadow_alpha)
                else:
                    shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
            else:
                if len(shadow_color) == 3:
                    shadow_color_with_alpha = shadow_color + (shadow_alpha,)
                elif len(shadow_color) == 4:
                    shadow_color_with_alpha = shadow_color[:3] + (shadow_alpha,)
                else:
                    shadow_color_with_alpha = (50, 50, 50, shadow_alpha)
        
        # 如果只有一行，直接绘制并返回
        if len(lines) <= 1:
            if shadow:
                for offset in range(3, shadow_offset + 1, 2):
                    draw.text(
                        (position[0] + offset, position[1] + offset),
                        text,
                        font=font,
                        fill=shadow_color_with_alpha
                    )
            draw.text(position, text, font=font, fill=fill_color)
            img_copy = Image.alpha_composite(img_copy, text_layer)
            return img_copy, 1
        
        # 绘制多行文本
        x, y = position
        font_size = font.size if hasattr(font, 'size') else 50
        for i, line in enumerate(lines):
            current_y = y + i * (font_size + line_spacing)
            
            if shadow:
                for offset in range(3, shadow_offset + 1, 2):
                    draw.text(
                        (x + offset, current_y + offset),
                        line,
                        font=font,
                        fill=shadow_color_with_alpha
                    )
            draw.text((x, current_y), line, font=font, fill=fill_color)
        
        img_copy = Image.alpha_composite(img_copy, text_layer)
        return img_copy, len(lines)
    
    def _draw_color_block(
        self,
        image: Image.Image,
        position: Tuple[int, int],
        size: Tuple[int, int],
        color: Tuple[int, int, int, int]
    ) -> Image.Image:
        """在图像上绘制色块（参考MoviePilot）"""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # 绘制矩形色块
        draw.rectangle(
            [position, (position[0] + size[0], position[1] + size[1])],
            fill=color
        )
        
        return img_copy
    
    async def generate_style_multi(
        self,
        library_id: str,
        library_name: str,
        title: str = "",
        subtitle: str = "",
        poster_count: int = 9,
        use_blur: bool = True,
        blur_size: int = 50,
        color_ratio: float = 0.8
    ) -> Optional[bytes]:
        """
        生成多图拼贴风格封面（静态版本，3x3网格）
        参考 MoviePilot-Plugins style_multi_1
        
        Args:
            library_id: 媒体库ID
            library_name: 媒体库名称
            title: 中文标题
            subtitle: 英文副标题
            poster_count: 海报数量（默认9张）
            use_blur: 是否使用模糊背景
            blur_size: 模糊半径
            color_ratio: 颜色混合比例
        """
        logger.info(f"开始生成多图封面: {library_name}")
        
        # 获取海报
        items = await self.get_library_items(library_id, limit=poster_count * 2)
        if not items:
            logger.error("未获取到任何项目")
            return None
        
        # 下载海报
        posters = []
        for item in items[:poster_count]:
            poster_data = await self.download_poster(item["Id"], item["Name"])
            if poster_data:
                try:
                    img = Image.open(io.BytesIO(poster_data))
                    posters.append(img)
                except Exception as e:
                    logger.error(f"打开海报失败: {e}")
        
        if len(posters) < 3:
            logger.error("海报数量不足")
            return None
        
        # 配置
        cfg = self.POSTER_CONFIG
        canvas_width = cfg["CANVAS_WIDTH"]
        canvas_height = cfg["CANVAS_HEIGHT"]
        rows = cfg["ROWS"]
        cols = cfg["COLS"]
        cell_width = cfg["CELL_WIDTH"]
        cell_height = cfg["CELL_HEIGHT"]
        margin = cfg["MARGIN"]
        corner_radius = cfg["CORNER_RADIUS"]
        rotation_angle = cfg["ROTATION_ANGLE"]
        start_x = cfg["START_X"]
        start_y = cfg["START_Y"]
        column_spacing = cfg["COLUMN_SPACING"]
        
        # 提取马卡龙风格主色调
        vibrant_colors = find_dominant_macaron_colors(posters[0], num_colors=6)
        
        # 柔和的颜色备选
        soft_colors = [
            (237, 159, 77),
            (255, 183, 197),
            (186, 225, 255),
            (255, 223, 186),
            (202, 231, 200),
            (245, 203, 255),
        ]
        
        # 选择背景色
        if vibrant_colors:
            bg_color = vibrant_colors[0]
        else:
            bg_color = random.choice(soft_colors)
        
        # 创建模糊背景
        if use_blur and posters:
            # 使用第一张海报创建模糊背景
            bg_img = posters[0].copy()
            bg_img = ImageOps.fit(bg_img, (canvas_width, canvas_height), method=Image.LANCZOS)
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=blur_size))
            
            # 与背景色混合
            bg_color_darkened = darken_color(bg_color, 0.85)
            bg_img_array = np.array(bg_img, dtype=float)
            bg_color_array = np.array([[bg_color_darkened]], dtype=float)
            
            # 混合背景图和颜色
            blended_bg = bg_img_array * (1 - color_ratio) + bg_color_array * color_ratio
            blended_bg = np.clip(blended_bg, 0, 255).astype(np.uint8)
            colored_bg_img = Image.fromarray(blended_bg)
            
            # 添加胶片颗粒效果
            colored_bg_img = add_film_grain(colored_bg_img, intensity=0.05)
        else:
            # 纯色背景
            colored_bg_img = Image.new("RGB", (canvas_width, canvas_height), bg_color)
        
        # 创建画布
        result = colored_bg_img.convert("RGBA")
        
        # 使用MoviePilot的自定义顺序重新排列海报
        # custom_order = "315426987"
        # 这个顺序是优先把最开始的两张图1.jpg和2.jpg放在最显眼的位置(1,2)和(2,2)，而最后一个9.jpg放在看不见的位置(3,1)
        # 九宫格位置: (row, col) = (1,1),(1,2),(1,3), (2,1),(2,2),(2,3), (3,1),(3,2),(3,3)
        # 索引映射:    0,     1,     2,      3,     4,     5,      6,     7,     8
        # custom_order: 3,     1,     5,      4,     2,     6,      9,     8,     7
        # 意味着: 位置0放第3张图, 位置1放第1张图, 位置2放第5张图, 等等
        custom_order = "315426987"  # MoviePilot使用的顺序
        reordered_posters = []
        for order_char in custom_order:
            idx = int(order_char) - 1  # 转换为0索引
            if idx < len(posters):
                reordered_posters.append(posters[idx])
            else:
                # 如果海报不够，循环使用
                reordered_posters.append(posters[idx % len(posters)])
        
        # 将重排后的海报分组（每组3张为一列）
        grouped_posters = []
        for i in range(0, len(reordered_posters), rows):
            grouped_posters.append(reordered_posters[i:i+rows])
        
        # 处理每一列
        for col_index, column_posters in enumerate(grouped_posters):
            if col_index >= cols:
                break
            
            # 计算当前列的 x 坐标
            column_x = start_x + col_index * column_spacing
            
            # 计算当前列所有图片组合后的高度
            column_height = rows * cell_height + (rows - 1) * margin
            
            # 创建透明画布用于当前列的所有图片
            shadow_extra_width = 40
            shadow_extra_height = 40
            column_image = Image.new(
                "RGBA",
                (cell_width + shadow_extra_width, column_height + shadow_extra_height),
                (0, 0, 0, 0)
            )
            
            # 在列画布上放置每张图片
            for row_index, poster in enumerate(column_posters):
                try:
                    # 调整海报大小
                    resized_poster = ImageOps.fit(poster, (cell_width, cell_height), method=Image.LANCZOS)
                    
                    # 创建圆角遮罩
                    if corner_radius > 0:
                        mask = Image.new("L", (cell_width, cell_height), 0)
                        draw = ImageDraw.Draw(mask)
                        draw.rounded_rectangle(
                            [(0, 0), (cell_width, cell_height)],
                            radius=int(corner_radius),
                            fill=255
                        )
                        
                        poster_with_corners = Image.new("RGBA", resized_poster.size, (0, 0, 0, 0))
                        poster_with_corners.paste(resized_poster, (0, 0), mask)
                        resized_poster = poster_with_corners
                    
                    # 添加阴影效果
                    resized_poster_with_shadow = add_shadow(
                        resized_poster,
                        offset=(20, 20),
                        shadow_color=(0, 0, 0, 216),
                        blur_radius=20
                    )
                    
                    # 计算在列画布上的位置
                    y_position = row_index * (cell_height + margin)
                    column_image.paste(
                        resized_poster_with_shadow,
                        (0, y_position),
                        resized_poster_with_shadow
                    )
                
                except Exception as e:
                    logger.error(f"处理海报时出错: {e}")
                    continue
            
            # 创建旋转画布
            import math
            rotation_canvas_size = int(
                math.sqrt((cell_width + shadow_extra_width) ** 2 + (column_height + shadow_extra_height) ** 2) * 1.5
            )
            rotation_canvas = Image.new(
                "RGBA",
                (rotation_canvas_size, rotation_canvas_size),
                (0, 0, 0, 0)
            )
            
            # 将列图片放在旋转画布的中央
            paste_x = (rotation_canvas_size - cell_width) // 2
            paste_y = (rotation_canvas_size - column_height) // 2
            rotation_canvas.paste(column_image, (paste_x, paste_y), column_image)
            
            # 旋转整个列
            rotated_column = rotation_canvas.rotate(
                rotation_angle,
                Image.BICUBIC,
                expand=True
            )
            
            # 计算列在模板上的位置（不同的列有不同的y起点）- 按照MoviePilot的逻辑
            column_center_y = start_y + column_height // 2
            column_center_x = column_x
            
            # 根据列索引调整位置 - 与MoviePilot完全一致
            if col_index == 1:  # 中间列
                column_center_x += cell_width - 50
            elif col_index == 2:  # 右侧列
                column_center_y += -155
                column_center_x += (cell_width) * 2 - 40
            
            # 计算最终放置位置
            final_x = column_center_x - rotated_column.width // 2 + cell_width // 2
            final_y = column_center_y - rotated_column.height // 2
            
            # 粘贴旋转后的列到结果图像
            result.paste(rotated_column, (final_x, final_y), rotated_column)
        
        # ===== 添加标题（按照MoviePilot的方式）=====
        # 获取随机颜色用于色块（从第一张海报）
        def get_random_color_from_poster(poster_img):
            """从海报图片随机位置获取颜色"""
            try:
                width, height = poster_img.size
                random_x = random.randint(int(width * 0.5), int(width * 0.8))
                random_y = random.randint(int(height * 0.5), int(height * 0.8))
                
                if poster_img.mode == "RGBA":
                    r, g, b, a = poster_img.getpixel((random_x, random_y))
                    return (r, g, b, a)
                elif poster_img.mode == "RGB":
                    r, g, b = poster_img.getpixel((random_x, random_y))
                    return (r + 100, g + 50, b, 255)
                else:
                    poster_rgb = poster_img.convert("RGBA")
                    r, g, b, a = poster_rgb.getpixel((random_x, random_y))
                    return (r, g, b, a)
            except Exception:
                return (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200), 255)
        
        random_color = get_random_color_from_poster(posters[0]) if posters else (237, 159, 77, 255)
        
        # 按照MoviePilot的方式绘制文字和色块
        if title:  # 中文标题
            zh_font_path = self.font_dir / "multi_1_zh.ttf"
            zh_font_size = 163  # 固定字体大小，与MoviePilot一致
            
            if zh_font_path.exists():
                zh_font = ImageFont.truetype(str(zh_font_path), zh_font_size)
            else:
                logger.warning(f"中文字体不存在: {zh_font_path}，使用默认字体")
                zh_font = ImageFont.load_default()
            
            # 绘制中文标题 - 使用MoviePilot的函数
            text_shadow_color = darken_color(bg_color, 0.8)
            result = self._draw_text_on_image(
                result, title, (73, 427), zh_font,
                shadow=use_blur, shadow_color=text_shadow_color
            )
        
        # 如果有英文副标题，才添加英文名文字和色块
        if subtitle:
            en_font_path = self.font_dir / "multi_1_en.otf"
            base_font_size = 50  # 默认字体大小
            line_spacing = base_font_size * 0.1
            
            # 根据单词数量或最长单词长度调整字体大小
            word_count = len(subtitle.split())
            max_chars_per_line = max([len(word) for word in subtitle.split()]) if subtitle.split() else 0
            
            if max_chars_per_line > 10 or word_count > 3:
                font_size = base_font_size * (10 / max(max_chars_per_line, word_count * 3)) ** 0.8
                font_size = max(font_size, 30)  # 最小字体大小
            else:
                font_size = base_font_size
            
            if en_font_path.exists():
                en_font = ImageFont.truetype(str(en_font_path), int(font_size))
            else:
                logger.warning(f"英文字体不存在: {en_font_path}，使用默认字体")
                en_font = ImageFont.load_default()
            
            # 使用多行文本绘制
            text_shadow_color = darken_color(bg_color, 0.8)
            result, line_count = self._draw_multiline_text_on_image(
                result, subtitle, (125, 625), en_font,
                line_spacing=line_spacing,
                shadow=use_blur, shadow_color=text_shadow_color
            )
            
            # 根据行数调整色块高度
            color_block_position = (84, 620)
            color_block_height = base_font_size + line_spacing + (line_count - 1) * (int(font_size) + line_spacing)
            color_block_size = (22, color_block_height)
            
            # 绘制色块
            result = self._draw_color_block(result, color_block_position, color_block_size, random_color)
        
        # 转换为字节
        output = io.BytesIO()
        result.convert("RGB").save(output, format="PNG", quality=95)
        output.seek(0)
        
        logger.info(f"多图封面生成完成: {library_name}")
        return output.getvalue()
    
    def _create_column_image(self, posters: List[Image.Image], cfg: Dict) -> Image.Image:
        """创建列图片"""
        cell_width = cfg["CELL_WIDTH"]
        cell_height = cfg["CELL_HEIGHT"]
        margin = cfg["MARGIN"]
        corner_radius = cfg["CORNER_RADIUS"]
        
        rows = len(posters)
        col_height = rows * cell_height + (rows - 1) * margin
        
        shadow_extra = 40
        col_image = Image.new(
            "RGBA",
            (cell_width + shadow_extra, col_height + shadow_extra),
            (0, 0, 0, 0)
        )
        
        for idx, poster in enumerate(posters):
            # 调整大小
            resized = poster.resize((cell_width, cell_height), Image.LANCZOS)
            
            # 圆角
            if corner_radius > 0:
                mask = Image.new("L", (cell_width, cell_height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle(
                    [(0, 0), (cell_width, cell_height)],
                    radius=corner_radius,
                    fill=255
                )
                rounded = Image.new("RGBA", resized.size, (0, 0, 0, 0))
                rounded.paste(resized, (0, 0), mask)
                resized = rounded
            
            # 添加阴影
            with_shadow = add_shadow(
                resized,
                offset=(20, 20),
                shadow_color=(0, 0, 0, 255),
                blur_radius=20
            )
            
            # 计算位置
            y_pos = idx * (cell_height + margin)
            col_image.paste(with_shadow, (0, y_pos), with_shadow)
        
        return col_image
    
    def _add_title_to_canvas(
        self,
        canvas: Image.Image,
        title: str,
        subtitle: str = ""
    ) -> Image.Image:
        """在画布上添加标题"""
        draw = ImageDraw.Draw(canvas)
        
        try:
            # 尝试加载自定义字体
            title_font = ImageFont.truetype(str(self.font_dir / "title.ttf"), 80)
            subtitle_font = ImageFont.truetype(str(self.font_dir / "subtitle.ttf"), 50)
        except:
            # 使用默认字体
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # 绘制标题
        title_pos = (100, 100)
        
        # 阴影
        shadow_offset = (4, 4)
        draw.text(
            (title_pos[0] + shadow_offset[0], title_pos[1] + shadow_offset[1]),
            title,
            font=title_font,
            fill=(0, 0, 0, 180)
        )
        # 文字
        draw.text(title_pos, title, font=title_font, fill=(255, 255, 255, 255))
        
        # 副标题
        if subtitle:
            subtitle_pos = (100, 200)
            draw.text(
                (subtitle_pos[0] + shadow_offset[0], subtitle_pos[1] + shadow_offset[1]),
                subtitle,
                font=subtitle_font,
                fill=(0, 0, 0, 180)
            )
            draw.text(subtitle_pos, subtitle, font=subtitle_font, fill=(200, 200, 200, 255))
        
        return canvas
    
    async def generate_style_single(
        self,
        library_id: str,
        library_name: str,
        title: str = "",
        subtitle: str = "",
        use_film_grain: bool = True,
        blur_size: int = 50,
        color_ratio: float = 0.8
    ) -> Optional[bytes]:
        """
        生成单图马卡龙风格封面 - Style Single 1
        参考 MoviePilot-Plugins 的实现
        """
        logger.info(f"开始生成单图封面: {library_name}")
        
        # 获取一个随机项目作为主图
        items = await self.get_library_items(library_id, limit=1, sort_by="Random")
        if not items:
            logger.warning(f"未获取到媒体库项目: {library_name}")
            return None
        
        poster_data = await self.download_poster(items[0]["Id"], items[0]["Name"])
        if not poster_data:
            logger.warning(f"下载海报失败: {library_name}")
            return None
        
        try:
            original_img = Image.open(io.BytesIO(poster_data)).convert("RGB")
        except Exception as e:
            logger.error(f"打开海报失败: {e}")
            return None
        
        # 画布尺寸
        canvas_size = (1920, 1080)
        
        # 提取马卡龙风格的颜色
        macaron_colors = find_dominant_macaron_colors(original_img, num_colors=6)
        if len(macaron_colors) < 3:
            # 备选颜色
            macaron_colors = [
                (237, 159, 77),    # 杏色
                (186, 225, 255),   # 淡蓝色
                (255, 223, 186),   # 浅橘色
                (202, 231, 200),   # 淡绿色
            ]
        
        # 处理颜色
        bg_color = darken_color(macaron_colors[0], 0.85)  # 背景色
        card_colors = [macaron_colors[1] if len(macaron_colors) > 1 else macaron_colors[0], 
                      macaron_colors[2] if len(macaron_colors) > 2 else macaron_colors[0]]  # 卡片颜色
        
        # 1. 创建背景
        bg_img = original_img.copy()
        bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.LANCZOS)
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=int(blur_size)))
        
        # 将背景图片与背景色混合
        bg_img_array = np.array(bg_img, dtype=float)
        bg_color_array = np.array([[bg_color]], dtype=float)
        blended_bg = bg_img_array * (1 - float(color_ratio)) + bg_color_array * float(color_ratio)
        blended_bg = np.clip(blended_bg, 0, 255).astype(np.uint8)
        blended_bg_img = Image.fromarray(blended_bg)
        
        # 添加胶片颗粒
        if use_film_grain:
            blended_bg_img = add_film_grain(blended_bg_img, intensity=0.03)
        
        # 创建画布
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        canvas.paste(blended_bg_img)
        
        # 2. 创建卡片效果
        square_img = crop_to_square(original_img)
        card_size = int(canvas_size[1] * 0.7)  # 卡片尺寸为画布高度的70%
        square_img = square_img.resize((card_size, card_size), Image.LANCZOS)
        
        # 主卡片
        main_card = add_rounded_corners(square_img, radius=card_size//8)
        main_card = main_card.convert("RGBA")
        
        # 辅助卡片1 (中间层)
        aux_card1 = square_img.copy().filter(ImageFilter.GaussianBlur(radius=8))
        aux_card1_array = np.array(aux_card1, dtype=float)
        card_color1_array = np.array([[card_colors[0]]], dtype=float)
        blended_card1 = aux_card1_array * 0.5 + card_color1_array * 0.5
        blended_card1 = np.clip(blended_card1, 0, 255).astype(np.uint8)
        aux_card1 = Image.fromarray(blended_card1)
        aux_card1 = add_rounded_corners(aux_card1, radius=card_size//8)
        aux_card1 = aux_card1.convert("RGBA")
        
        # 辅助卡片2 (底层)
        aux_card2 = square_img.copy().filter(ImageFilter.GaussianBlur(radius=16))
        aux_card2_array = np.array(aux_card2, dtype=float)
        card_color2_array = np.array([[card_colors[1]]], dtype=float)
        blended_card2 = aux_card2_array * 0.4 + card_color2_array * 0.6
        blended_card2 = np.clip(blended_card2, 0, 255).astype(np.uint8)
        aux_card2 = Image.fromarray(blended_card2)
        aux_card2 = add_rounded_corners(aux_card2, radius=card_size//8)
        aux_card2 = aux_card2.convert("RGBA")
        
        # 3. 添加阴影和旋转，放置卡片
        center_x = int(canvas_size[0] - canvas_size[1] * 0.5)
        center_y = int(canvas_size[1] * 0.5)
        center_pos = (center_x, center_y)
        
        rotation_angles = [36, 18, 0]  # 底层、中间层、顶层
        shadow_configs = [
            {'offset': (10, 16), 'radius': 12, 'opacity': 0.4},
            {'offset': (15, 22), 'radius': 15, 'opacity': 0.5},
            {'offset': (20, 26), 'radius': 18, 'opacity': 0.6},
        ]
        
        cards_canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        cards = [aux_card2, aux_card1, main_card]
        
        for card, angle, shadow_config in zip(cards, rotation_angles, shadow_configs):
            cards_canvas = add_shadow_and_rotate(
                cards_canvas, card, angle,
                offset=shadow_config['offset'],
                radius=shadow_config['radius'],
                opacity=shadow_config['opacity'],
                center_pos=center_pos
            )
        
        canvas = Image.alpha_composite(canvas.convert("RGBA"), cards_canvas)
        
        # 4. 添加文字
        text_layer = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
        shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        shadow_draw = ImageDraw.Draw(shadow_layer)
        
        # 左侧区域中心
        left_center_x = int(canvas_size[0] * 0.25)
        left_center_y = canvas_size[1] // 2
        
        # 加载字体
        zh_font_size = int(canvas_size[1] * 0.17)  # 1080 * 0.17 = 183px
        en_font_size = int(canvas_size[1] * 0.07)  # 1080 * 0.07 = 75px
        
        # 中英文字体路径（使用MoviePilot-Plugins的字体）
        zh_font_path = self.font_dir / "multi_1_zh.ttf"
        en_font_path = self.font_dir / "multi_1_en.otf"
        
        logger.info(f"字体路径: 中文={zh_font_path}, 英文={en_font_path}")
        
        # 加载中文字体
        if zh_font_path.exists():
            zh_font = ImageFont.truetype(str(zh_font_path), zh_font_size)
            logger.info(f"中文字体加载成功: {zh_font_path.name}")
        else:
            logger.warning(f"中文字体不存在: {zh_font_path}，使用默认字体")
            zh_font = ImageFont.load_default()
        
        # 加载英文字体
        if en_font_path.exists():
            en_font = ImageFont.truetype(str(en_font_path), en_font_size)
            logger.info(f"英文字体加载成功: {en_font_path.name}")
        else:
            logger.warning(f"英文字体不存在: {en_font_path}，使用默认字体")
            en_font = ImageFont.load_default()
        
        logger.info(f"准备添加标题: title='{title}' (len={len(title) if title else 0}), subtitle='{subtitle}' (len={len(subtitle) if subtitle else 0})")
        
        text_color = (255, 255, 255, 229)
        shadow_color = darken_color(bg_color, 0.8) + (75,)
        shadow_offset = 12
        
        # 中文标题
        if title:
            zh_bbox = draw.textbbox((0, 0), title, font=zh_font)
            zh_w = zh_bbox[2] - zh_bbox[0]
            zh_h = zh_bbox[3] - zh_bbox[1]
            zh_x = left_center_x - zh_w // 2
            zh_y = left_center_y - zh_h - int(canvas_size[1] * 0.035) - 5
            
            # 阴影
            for offset in range(3, shadow_offset + 1, 2):
                shadow_draw.text((zh_x + offset, zh_y + offset), title, font=zh_font, fill=shadow_color)
            draw.text((zh_x, zh_y), title, font=zh_font, fill=text_color)
        
        # 英文副标题
        if subtitle:
            en_bbox = draw.textbbox((0, 0), subtitle, font=en_font)
            en_w = en_bbox[2] - en_bbox[0]
            en_h = en_bbox[3] - en_bbox[1]
            en_x = left_center_x - en_w // 2
            en_y = left_center_y + int(canvas_size[1] * 0.035)
            
            for offset in range(2, shadow_offset // 2 + 1):
                shadow_draw.text((en_x + offset, en_y + offset), subtitle, font=en_font, fill=shadow_color)
            draw.text((en_x, en_y), subtitle, font=en_font, fill=text_color)
        
        # 合成阴影和文字
        blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_offset))
        canvas = Image.alpha_composite(canvas, blurred_shadow)
        canvas = Image.alpha_composite(canvas, text_layer)
        
        # 转换为字节
        output = io.BytesIO()
        canvas.convert("RGB").save(output, format="PNG", quality=95)
        output.seek(0)
        
        logger.info(f"单图封面生成完成: {library_name}")
        return output.getvalue()
    
    async def generate_style_single_2(
        self, 
        library_id: str,
        library_name: str,
        title: str = "",
        subtitle: str = ""
    ) -> Optional[bytes]:
        """
        生成单图样式2封面 - 斜线分割设计
        左侧：模糊背景 + 彩色混合 + 居中文字
        右侧：右对齐裁剪的原图
        
        Args:
            library_id: 媒体库ID
            library_name: 媒体库名称
            title: 中文标题
            subtitle: 英文副标题
            
        Returns:
            PNG图片字节数据
        """
        logger.info(f"开始生成单图样式2封面: {library_name}")
        
        # 获取一个随机项目作为主图
        items = await self.get_library_items(library_id, limit=1, sort_by="Random")
        if not items:
            logger.warning(f"未获取到媒体库项目: {library_name}")
            return None
        
        poster_data = await self.download_poster(items[0]["Id"], items[0]["Name"])
        if not poster_data:
            logger.warning(f"下载海报失败: {library_name}")
            return None
        
        try:
            fg_img_original = Image.open(io.BytesIO(poster_data)).convert("RGB")
        except Exception as e:
            logger.error(f"打开海报失败: {e}")
            return None
        
        # 画布尺寸
        canvas_size = (1920, 1080)
        
        # 斜线分割位置
        split_top = 0.55    # 顶部分割点在55%
        split_bottom = 0.4  # 底部分割点在40%
        
        # 加载并处理前景图片（右对齐）
        fg_img = align_image_right(fg_img_original, canvas_size)
        
        # 提取马卡龙风格主色调
        vibrant_colors = find_dominant_macaron_colors(fg_img, num_colors=6)
        
        # 柔和的颜色备选（马卡龙风格）
        soft_colors = [
            (237, 159, 77),    # 原默认色
            (255, 183, 197),   # 淡粉色
            (186, 225, 255),   # 淡蓝色
            (255, 223, 186),   # 浅橘色
            (202, 231, 200),   # 淡绿色
            (245, 203, 255),   # 淡紫色
        ]
        
        # 选择背景色
        if vibrant_colors:
            bg_color = vibrant_colors[0]
        else:
            bg_color = random.choice(soft_colors)
        
        shadow_color = darken_color(bg_color, 0.5)  # 阴影颜色加深到50%
        
        # 加载背景图片（使用同一张海报）
        bg_img = ImageOps.fit(fg_img_original.copy(), canvas_size, method=Image.LANCZOS)
        
        # 强烈模糊化背景图
        blur_size = 50
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=blur_size))
        
        # 将背景图片与背景色混合
        bg_color_darkened = darken_color(bg_color, 0.85)
        bg_img_array = np.array(bg_img, dtype=float)
        bg_color_array = np.array([[bg_color_darkened]], dtype=float)
        
        # 混合背景图和颜色 (20% 背景图 + 80% 颜色)
        color_ratio = 0.8
        blended_bg = bg_img_array * (1 - color_ratio) + bg_color_array * color_ratio
        blended_bg = np.clip(blended_bg, 0, 255).astype(np.uint8)
        blended_bg_img = Image.fromarray(blended_bg)
        
        # 添加胶片颗粒效果
        blended_bg_img = add_film_grain(blended_bg_img, intensity=0.05)
        
        # 创建斜线分割的蒙版
        diagonal_mask = create_diagonal_mask(canvas_size, split_top, split_bottom)
        
        # 创建基础画布 - 前景图
        canvas = fg_img.copy()
        
        # 创建阴影蒙版
        shadow_mask = create_shadow_mask(canvas_size, split_top, split_bottom, feather_size=30)
        
        # 创建阴影层 - 使用加深的背景色
        shadow_layer = Image.new('RGB', canvas_size, shadow_color)
        
        # 创建临时画布用于组合
        temp_canvas = Image.new('RGB', canvas_size)
        
        # 应用阴影到前景图
        temp_canvas.paste(canvas)
        temp_canvas.paste(shadow_layer, mask=shadow_mask)
        
        # 使用蒙版将背景图应用到画布上
        canvas = Image.composite(blended_bg_img, temp_canvas, diagonal_mask)
        
        # ===== 标题绘制 =====
        canvas_rgba = canvas.convert('RGBA')
        text_layer = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
        shadow_layer_text = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        
        shadow_draw = ImageDraw.Draw(shadow_layer_text)
        draw = ImageDraw.Draw(text_layer)
        
        # 计算左侧区域的中心 X 位置 (画布宽度的四分之一处)
        left_area_center_x = int(canvas_size[0] * 0.25)
        left_area_center_y = canvas_size[1] // 2
        
        # 字体大小
        zh_font_size = int(canvas_size[1] * 0.17)
        en_font_size = int(canvas_size[1] * 0.07)
        
        # 加载字体（使用MoviePilot-Plugins的字体）
        zh_font_path = self.font_dir / "multi_1_zh.ttf"
        en_font_path = self.font_dir / "multi_1_en.otf"
        
        logger.info(f"single_2 字体路径: 中文={zh_font_path}, 英文={en_font_path}")
        
        if zh_font_path.exists():
            zh_font = ImageFont.truetype(str(zh_font_path), zh_font_size)
            logger.info(f"中文字体加载成功")
        else:
            logger.warning(f"中文字体不存在: {zh_font_path}，使用默认字体")
            zh_font = ImageFont.load_default()
        
        if en_font_path.exists():
            en_font = ImageFont.truetype(str(en_font_path), en_font_size)
            logger.info(f"英文字体加载成功")
        else:
            logger.warning(f"英文字体不存在: {en_font_path}，使用默认字体")
            en_font = ImageFont.load_default()
        
        # 设置文字颜色和阴影
        text_color = (255, 255, 255, 229)  # 90%不透明度
        shadow_color_text = darken_color(bg_color, 0.8) + (75,)  # 阴影颜色
        shadow_offset = 12
        shadow_alpha = 75
        
        # 计算中文标题的位置
        if title:
            zh_bbox = draw.textbbox((0, 0), title, font=zh_font)
            zh_text_w = zh_bbox[2] - zh_bbox[0]
            zh_text_h = zh_bbox[3] - zh_bbox[1]
            zh_x = left_area_center_x - zh_text_w // 2
            zh_y = left_area_center_y - zh_text_h - en_font_size // 2 - 5
            
            # 绘制中文标题阴影
            for offset in range(3, shadow_offset + 1, 2):
                current_shadow_color = shadow_color_text[:3] + (shadow_alpha,)
                shadow_draw.text((zh_x + offset, zh_y + offset), title, font=zh_font, fill=current_shadow_color)
            
            # 绘制中文标题
            draw.text((zh_x, zh_y), title, font=zh_font, fill=text_color)
        
        # 计算英文副标题的位置
        if subtitle:
            en_bbox = draw.textbbox((0, 0), subtitle, font=en_font)
            en_text_w = en_bbox[2] - en_bbox[0]
            en_text_h = en_bbox[3] - en_bbox[1]
            en_x = left_area_center_x - en_text_w // 2
            
            if title:
                # 如果有中文标题，则在其下方显示英文
                en_y = zh_y + zh_text_h + en_font_size
            else:
                # 如果没有中文标题，则居中显示英文
                en_y = left_area_center_y - en_text_h // 2
            
            # 绘制英文副标题阴影
            for offset in range(2, shadow_offset // 2 + 1):
                current_shadow_color = shadow_color_text[:3] + (shadow_alpha,)
                shadow_draw.text((en_x + offset, en_y + offset), subtitle, font=en_font, fill=current_shadow_color)
            
            # 绘制英文副标题
            draw.text((en_x, en_y), subtitle, font=en_font, fill=text_color)
        
        # 合成所有层
        shadow_layer_text = shadow_layer_text.filter(ImageFilter.GaussianBlur(radius=12))
        canvas_rgba = Image.alpha_composite(canvas_rgba, shadow_layer_text)
        canvas_rgba = Image.alpha_composite(canvas_rgba, text_layer)
        
        # 转换回RGB
        canvas = canvas_rgba.convert("RGB")
        
        # 转换为字节
        output = io.BytesIO()
        canvas.save(output, format="PNG", quality=95)
        output.seek(0)
        
        logger.info(f"单图样式2封面生成完成: {library_name}")
        return output.getvalue()
    
    def create_extended_column(self, images: List[Image.Image], column_index: int) -> Image.Image:
        """
        创建扩展列用于动画循环
        将海报列表垂直排列两次，形成无缝循环效果
        
        Args:
            images: 海报图片列表
            column_index: 列索引(0-2)
            
        Returns:
            扩展后的列图像
        """
        if not images:
            return Image.new('RGBA', (410 + 60, 1874 + 60), (0, 0, 0, 0))
        
        # 每列包含的海报数量
        posters_per_column = 3
        
        # 计算该列需要的海报
        start_idx = column_index * posters_per_column
        column_posters = []
        
        for i in range(posters_per_column):
            idx = (start_idx + i) % len(images)
            column_posters.append(images[idx])
        
        # 统一海报尺寸 - 使用标准尺寸 (与原项目一致)
        target_width = 410
        target_height = 610
        margin = 22  # 海报间距
        corner_radius = 46  # 圆角半径
        
        resized_posters = []
        for poster in column_posters:
            resized = poster.copy()
            resized.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            
            # 创建固定大小的画布并居中粘贴
            canvas = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 255))
            x_offset = (target_width - resized.width) // 2
            y_offset = (target_height - resized.height) // 2
            
            # 转换为RGBA
            if resized.mode != 'RGBA':
                resized = resized.convert('RGBA')
            canvas.paste(resized, (x_offset, y_offset))
            
            # 添加圆角
            if corner_radius > 0:
                mask = Image.new('L', (target_width, target_height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle(
                    [(0, 0), (target_width, target_height)],
                    radius=corner_radius,
                    fill=255
                )
                rounded = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
                rounded.paste(canvas, (0, 0), mask)
                canvas = rounded
            
            # 添加阴影
            shadow_offset = (20, 20)
            shadow_blur = 20
            shadow_size = (target_width + shadow_offset[0] + shadow_blur * 2,
                          target_height + shadow_offset[1] + shadow_blur * 2)
            shadow_img = Image.new('RGBA', shadow_size, (0, 0, 0, 0))
            
            # 创建阴影层
            shadow_layer = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 255))
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
            shadow_img.paste(shadow_layer, shadow_offset, shadow_layer)
            
            # 粘贴原图
            shadow_img.paste(canvas, (0, 0), canvas)
            resized_posters.append(shadow_img)
        
        # 创建扩展列：垂直重复两次以实现无缝循环
        # 包含间距的单列高度
        single_column_height = posters_per_column * target_height + (posters_per_column - 1) * margin
        extended_height = single_column_height * 2 + margin
        
        # 加上阴影额外空间
        shadow_extra_width = 20 + 20 * 2
        shadow_extra_height = 20 + 20 * 2
        extended_column = Image.new('RGBA', 
                                   (target_width + shadow_extra_width, 
                                    extended_height + shadow_extra_height),
                                   (0, 0, 0, 0))
        
        # 第一遍：正常排列
        for i, poster in enumerate(resized_posters):
            y_pos = i * (target_height + margin)
            extended_column.paste(poster, (0, y_pos), poster)
        
        # 第二遍：重复排列
        for i, poster in enumerate(resized_posters):
            y_pos = single_column_height + margin + i * (target_height + margin)
            extended_column.paste(poster, (0, y_pos), poster)
        
        return extended_column
    
    def generate_animation_frame(
        self, 
        extended_columns: List[Image.Image], 
        frame_index: int, 
        total_frames: int,
        canvas_size: Tuple[int, int],
        background_color: Tuple[int, int, int],
        library_name: str = "",
        use_macaron: bool = True
    ) -> Image.Image:
        """
        生成单帧动画
        
        Args:
            extended_columns: 扩展后的列图像列表
            frame_index: 当前帧索引
            total_frames: 总帧数
            canvas_size: 画布尺寸
            background_color: 背景颜色
            library_name: 媒体库名称
            use_macaron: 是否使用马卡龙配色
            
        Returns:
            单帧图像
        """
        # 创建画布 - 使用RGBA支持透明度
        frame = Image.new('RGBA', canvas_size, background_color + (255,))
        
        # 计算滚动进度 (0.0 到 1.0)
        progress = frame_index / total_frames
        
        # 每列的滚动偏移量（一个循环周期）- 包含间距
        margin = 22
        target_height = 610
        single_column_height = 3 * target_height + 2 * margin  # 1874
        move_distance = single_column_height + margin
        base_offset = int(progress * move_distance)
        
        # 列布局参数
        column_width = 410
        column_spacing = 100
        start_x = 835
        start_y = -362
        rotation_angle = -15.8  # 原项目的旋转角度
        
        # 绘制三列
        for col_idx, extended_col in enumerate(extended_columns):
            # 根据列索引确定移动方向：第1列向上，第2列向下，第3列向上
            if col_idx == 1:
                offset = base_offset  # 向下移动（正偏移）
            else:
                offset = -base_offset  # 向上移动（负偏移）
            
            # 从扩展列中裁剪当前帧需要的部分
            shadow_extra = 20 + 20 * 2
            crop_y_start = single_column_height // 2 + offset
            crop_y_start = crop_y_start % (single_column_height + margin)
            
            try:
                # 裁剪出需要的部分
                cropped = extended_col.crop((
                    0,
                    crop_y_start,
                    extended_col.width,
                    crop_y_start + single_column_height + shadow_extra
                ))
                
                # 创建旋转画布
                rotation_canvas_size = int(
                    math.sqrt(cropped.width ** 2 + cropped.height ** 2) * 1.5
                )
                rotation_canvas = Image.new(
                    'RGBA', (rotation_canvas_size, rotation_canvas_size), (0, 0, 0, 0)
                )
                
                paste_x = (rotation_canvas_size - cropped.width) // 2
                paste_y = (rotation_canvas_size - cropped.height) // 2
                rotation_canvas.paste(cropped, (paste_x, paste_y), cropped)
                
                # 旋转整列
                rotated_column = rotation_canvas.rotate(
                    rotation_angle, Image.BICUBIC, expand=True
                )
                
                # 计算列在画布上的位置
                column_x = start_x + col_idx * column_spacing
                column_center_y = start_y + single_column_height // 2
                column_center_x = column_x
                
                # 根据列索引微调位置
                if col_idx == 1:
                    column_center_x += column_width - 50
                elif col_idx == 2:
                    column_center_y += -155
                    column_center_x += column_width * 2 - 40
                
                # 计算最终放置位置
                final_x = column_center_x - rotated_column.width // 2 + column_width // 2
                final_y = column_center_y - rotated_column.height // 2
                
                # 粘贴旋转后的列
                frame.paste(rotated_column, (final_x, final_y), rotated_column)
            except Exception as e:
                logger.warning(f"处理列 {col_idx} 失败: {e}")
                continue
        
        # 添加标题
        if library_name:
            draw = ImageDraw.Draw(frame)
            try:
                font_size = int(canvas_size[1] * 0.08)
                font_path = self._get_font_path()
                font = ImageFont.truetype(str(font_path), font_size)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), library_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (canvas_size[0] - text_width) // 2
            text_y = canvas_size[1] - 150
            
            # 阴影
            draw.text((text_x + 3, text_y + 3), library_name, font=font, fill=(0, 0, 0, 180))
            # 文字
            draw.text((text_x, text_y), library_name, font=font, fill=(255, 255, 255, 255))
        
        return frame
    
    async def generate_animated_cover(
        self,
        library_id: str,
        library_name: str,
        title: str = "",
        subtitle: str = "",
        style: str = "multi_1",
        frame_count: int = 30,
        frame_duration: int = 50,
        output_format: str = "gif",
        use_title: bool = True,
        use_macaron: bool = True,
        use_film_grain: bool = True,
        poster_count: int = 9,
        **kwargs
    ) -> bytes:
        """
        生成动画封面 (GIF 或 WebP)
        
        Args:
            library_id: 媒体库ID
            library_name: 媒体库名称
            style: 风格（目前仅支持 multi_1）
            frame_count: 帧数
            frame_duration: 帧间隔（毫秒）
            output_format: 输出格式 (gif/webp)
            use_title: 是否显示标题
            use_macaron: 是否使用马卡龙配色
            use_film_grain: 是否添加胶片颗粒
            poster_count: 海报数量
            
        Returns:
            动画文件的字节数据
        """
        logger.info(f"开始生成动画封面: {library_name}, 帧数: {frame_count}")
        
        # 获取海报图片
        posters = await self._fetch_posters(library_id, count=poster_count)
        if not posters:
            raise ValueError(f"未能获取媒体库 {library_name} 的海报")
        
        logger.info(f"成功获取 {len(posters)} 张海报")
        
        # 提取主色调
        macaron_colors = []
        if use_macaron:
            for poster in posters[:5]:
                colors = find_dominant_macaron_colors(poster, num_colors=2)
                macaron_colors.extend(colors)
        
        # 选择背景色
        bg_color = macaron_colors[0] if macaron_colors else (180, 200, 220)
        
        # 创建渐变背景 - 增加到高清尺寸
        canvas_size = (1920, 1080)  # 提升到 1080P
        gradient_bg = create_gradient_background(canvas_size[0], canvas_size[1], macaron_colors)
        
        # 创建扩展列
        extended_columns = []
        for col_idx in range(3):
            extended_col = self.create_extended_column(posters, col_idx)
            extended_columns.append(extended_col)
        
        logger.info("扩展列创建完成")
        
        # 生成所有帧
        frames = []
        for frame_idx in range(frame_count):
            frame = self.generate_animation_frame(
                extended_columns=extended_columns,
                frame_index=frame_idx,
                total_frames=frame_count,
                canvas_size=canvas_size,
                background_color=bg_color,
                library_name=library_name if use_title else "",
                use_macaron=use_macaron
            )
            
            # 合成渐变背景
            frame_with_bg = gradient_bg.copy()
            frame_with_bg.paste(frame, (0, 0), frame if frame.mode == 'RGBA' else None)
            
            # 添加标题叠加层(在缩放之前)
            if use_title and (title or subtitle):
                # 提取色块颜色
                random_color = (macaron_colors[0][0], macaron_colors[0][1], macaron_colors[0][2], 255) if macaron_colors else (100, 150, 200, 255)
                frame_with_bg = self._add_title_overlay(frame_with_bg, title or library_name, subtitle, random_color)
            
            # 添加胶片颗粒
            if use_film_grain:
                frame_with_bg = add_film_grain(frame_with_bg, intensity=0.03)
            
            frames.append(frame_with_bg)
            
            if (frame_idx + 1) % 10 == 0:
                logger.info(f"已生成 {frame_idx + 1}/{frame_count} 帧")
        
        logger.info(f"所有帧生成完成，开始保存为 {output_format.upper()}")
        
        # 缩放到标准输出尺寸 (560x315, 参考原项目)
        output_size = (560, 315)
        logger.info(f"缩放到输出尺寸: {output_size}")
        resized_frames = []
        for frame in frames:
            resized = frame.resize(output_size, Image.Resampling.LANCZOS)
            resized_frames.append(resized)
        frames = resized_frames
        
        # 保存为动画
        output = io.BytesIO()
        
        if output_format.lower() == 'gif':
            # GIF格式 - 使用全局调色板避免文字闪烁（参考jellyfin-library-poster）
            gif_colors = 256  # 使用256色调色板，与原项目一致
            gif_frames = []
            
            # 基于第一帧生成全局调色板，所有帧共享同一调色板以避免文字闪烁
            first_frame_rgb = frames[0].convert("RGB")
            global_palette = first_frame_rgb.quantize(
                colors=gif_colors, 
                method=Image.Quantize.MEDIANCUT
            )
            
            logger.info(f"使用全局调色板处理GIF帧 (调色板大小: {gif_colors}色)...")
            for i, frame in enumerate(frames):
                # 先转换为RGB（移除alpha通道）
                frame_rgb = frame.convert("RGB")
                # 使用全局调色板进行量化，确保颜色一致性
                frame_p = frame_rgb.quantize(
                    palette=global_palette, 
                    dither=Image.Dither.FLOYDSTEINBERG
                )
                gif_frames.append(frame_p)
            
            # 保存GIF，关闭优化以保持颜色一致性
            gif_frames[0].save(
                output,
                format='GIF',
                save_all=True,
                append_images=gif_frames[1:],
                duration=frame_duration,
                loop=0,
                optimize=False
            )
        elif output_format.lower() == 'webp':
            frames[0].save(
                output,
                format='WEBP',
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0,
                quality=85,  # 使用85质量，平衡大小和质量
                method=4  # 使用method=4，更好的压缩
            )
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        output.seek(0)
        logger.info(f"动画封面生成完成: {library_name}, 大小: {len(output.getvalue())} 字节")
        return output.getvalue()


# 创建全局实例
cover_service = CoverGeneratorService()
