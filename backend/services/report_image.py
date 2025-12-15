"""
观影报告图片生成服务
参考 MP 插件的精美设计，生成竖版报告
"""
import io
import logging
import os
import random
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
import requests
from pathlib import Path

from config_storage import config_storage

logger = logging.getLogger(__name__)


class ReportImageService:
    """报告图片生成服务 - 竖版设计"""
    
    def __init__(self):
        # 竖版尺寸 (参考前端 1080px 宽度)
        self.width = 1080
        self.bg_color = (26, 32, 44)  # 深色背景
        self.card_color = (45, 55, 72)  # 卡片背景
        self.text_primary = (255, 255, 255)  # 主文字
        self.text_secondary = (156, 163, 175)  # 次要文字 (#9ca3af)
        self.accent_cyan = (56, 189, 248)  # 青色 (#38bdf8)
        self.accent_purple = (167, 139, 250)  # 紫色 (#a78bfa)
        self.accent_yellow = (251, 191, 36)  # 黄色 (#fbbf24)
        
        # 资源路径
        self.res_dir = Path(__file__).parent.parent.parent / "res"
        
        # Emby 服务器配置（用于实时获取封面）
        self.emby_url = None
        self.emby_api_key = None
        self._load_emby_config()
    
    def _load_emby_config(self):
        """加载 Emby 服务器配置"""
        try:
            # Emby 服务器配置存储在 servers 字典中
            servers = config_storage.get("servers", {})
            if servers:
                # 使用第一个服务器
                server_id = list(servers.keys())[0]
                server = servers[server_id]
                self.emby_url = server.get("url", "").rstrip("/")
                self.emby_api_key = server.get("api_key", "")
                logger.info(f"加载 Emby 配置: URL={self.emby_url}, Server ID={server_id}")
            else:
                logger.warning("未配置 Emby 服务器")
        except Exception as e:
            logger.error(f"加载 Emby 配置失败: {e}")
    
    def _fetch_cover_image(self, item_id: str, width: int = 220, height: int = 310, quality: int = 90) -> Optional[bytes]:
        """实时获取封面图片（参考 MP 插件 primary 方法）
        
        Args:
            item_id: 项目 ID
            width: 最大宽度
            height: 最大高度
            quality: 图片质量 (1-100)
            
        Returns:
            图片字节数据，失败返回 None
        """
        if not self.emby_url or not self.emby_api_key or not item_id:
            logger.warning(f"封面获取条件不足: URL={self.emby_url}, API_KEY={'已设置' if self.emby_api_key else '未设置'}, item_id={item_id}")
            return None
        
        try:
            url = f"{self.emby_url}/Items/{item_id}/Images/Primary"
            params = {
                "maxWidth": width,
                "maxHeight": height,
                "quality": quality,
                "api_key": self.emby_api_key
            }
            
            logger.info(f"正在获取封面: {url} (item_id={item_id})")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"封面获取成功: {len(response.content)} bytes")
                return response.content
            else:
                logger.warning(f"封面获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"封面获取异常: {e}")
            return None
        
    def generate_report_image(self, report: Dict[str, Any], item_images: List[Optional[bytes]] = None) -> bytes:
        """生成报告图片 - 竖版精美设计
        
        Args:
            report: 报告数据
            item_images: 热门内容的封面图片列表（字节数据）
        
        Returns:
            PNG图片字节数据
        """
        # 计算高度 (参考前端组件布局)
        header_height = 260  # 标题区
        stats_height = 340   # 统计卡片 (增加高度)
        content_title_height = 120  # "热门内容"标题
        item_count = min(len(report.get('top_content', [])), 5)
        content_height = item_count * 190 + (item_count - 1) * 20  # 每项190px，间距20px
        footer_height = 100
        total_height = header_height + stats_height + content_title_height + content_height + footer_height
        
        # 创建画布 - 尝试使用背景图
        img = self._create_background(total_height)
        draw = ImageDraw.Draw(img)
        
        # 绘制各部分
        y_offset = 0
        y_offset = self._draw_header(draw, report, y_offset)
        y_offset = self._draw_stats(draw, report, y_offset)
        y_offset = self._draw_top_content(draw, img, report, y_offset, item_images)
        self._draw_footer(draw, total_height - footer_height)
        
        # 转换为字节 - 使用更高质量
        output = io.BytesIO()
        img.save(output, format='PNG', optimize=False, compress_level=1)
        return output.getvalue()
    
    def _create_background(self, height: int) -> Image:
        """创建背景 - 可以是纯色或背景图"""
        # 检查是否有背景图资源
        bg_path = self.res_dir / "bg"
        if bg_path.exists() and bg_path.is_dir():
            bg_files = list(bg_path.glob("*.png")) + list(bg_path.glob("*.jpg"))
            if bg_files:
                try:
                    # 随机选择背景图
                    bg_file = random.choice(bg_files)
                    bg = Image.open(bg_file)
                    
                    # 调整背景图尺寸
                    if bg.size[0] != self.width or bg.size[1] < height:
                        # 按比例缩放
                        aspect = bg.size[0] / bg.size[1]
                        if aspect > self.width / height:
                            # 背景更宽，按高度缩放
                            new_height = height
                            new_width = int(new_height * aspect)
                        else:
                            # 按宽度缩放
                            new_width = self.width
                            new_height = int(new_width / aspect)
                        bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # 居中裁剪
                        left = (new_width - self.width) // 2
                        top = (new_height - height) // 2
                        bg = bg.crop((left, top, left + self.width, top + height))
                    else:
                        bg = bg.crop((0, 0, self.width, height))
                    
                    # 添加半透明遮罩让文字更清晰
                    overlay = Image.new('RGBA', (self.width, height), (*self.bg_color, 200))
                    bg = bg.convert('RGBA')
                    bg = Image.alpha_composite(bg, overlay)
                    bg = bg.convert('RGB')
                    
                    logger.info(f"使用背景图: {bg_file.name}")
                    return bg
                except Exception as e:
                    logger.warning(f"加载背景图失败: {e}，使用纯色背景")
        
        # 使用纯色背景
        return Image.new('RGB', (self.width, height), self.bg_color)
    
    def _draw_header(self, draw: ImageDraw, report: Dict[str, Any], y: int) -> int:
        """绘制标题区域 - 参考前端样式"""
        # 标题 - 添加文字描边效果
        title_font = self._get_font(72, bold=True)
        title_text = report['title']
        self._draw_text_with_stroke(
            draw, (50, y + 50), title_text, title_font,
            fill=self.text_primary, stroke_color=(0, 0, 0), stroke_width=3
        )
        
        # 日期
        date_font = self._get_font(36)
        self._draw_text_with_stroke(
            draw, (50, y + 170), report['period'], date_font,
            fill=self.text_secondary, stroke_color=(0, 0, 0), stroke_width=2
        )
        
        return y + 260
    
    def _draw_stats(self, draw: ImageDraw, report: Dict[str, Any], y: int) -> int:
        """绘制统计卡片 - 参考前端样式，增大尺寸"""
        summary = report['summary']
        
        # 卡片背景
        card_padding = 50
        card_y = y + 20
        card_height = 280  # 增加高度
        draw.rounded_rectangle(
            [(card_padding, card_y), (self.width - card_padding, card_y + card_height)],
            radius=20,
            fill=self.card_color
        )
        
        # 三列统计数据
        col_width = (self.width - 2 * card_padding) // 3
        
        # 观看时长
        hours = summary['total_hours']
        minutes = int((hours % 1) * 60)
        self._draw_stat_item(
            draw, 
            card_padding + col_width * 0 + col_width // 2,
            card_y + 50,
            f"{int(hours)}小时{minutes}分",
            "观看时长",
            self.accent_cyan
        )
        
        # 播放次数
        self._draw_stat_item(
            draw,
            card_padding + col_width * 1 + col_width // 2,
            card_y + 50,
            f"{summary['total_plays']}次",
            "播放次数",
            self.accent_purple
        )
        
        # 观看内容
        total_items = len(report.get('top_content', []))
        self._draw_stat_item(
            draw,
            card_padding + col_width * 2 + col_width // 2,
            card_y + 50,
            f"{total_items}部",
            "观看内容",
            self.accent_yellow
        )
        
        # 底部详细信息
        movie_count = sum(1 for item in report.get('top_content', []) if item.get('type') == 'Movie')
        episode_count = total_items - movie_count
        movie_hours = sum(item.get('hours', 0) for item in report.get('top_content', []) if item.get('type') == 'Movie')
        episode_hours = summary['total_hours'] - movie_hours
        
        detail_text = f"电影 {movie_count}部 · {int(movie_hours)}h{int((movie_hours % 1) * 60)}m    剧集 {episode_count}集 · {int(episode_hours)}h{int((episode_hours % 1) * 60)}m"
        detail_font = self._get_font(22)
        
        # 居中绘制
        bbox = draw.textbbox((0, 0), detail_text, font=detail_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((self.width - text_width) // 2, card_y + card_height - 55),
            detail_text,
            fill=self.text_secondary,
            font=detail_font
        )
        
        return card_y + card_height + 50
    
    def _draw_stat_item(self, draw: ImageDraw, x: int, y: int, value: str, label: str, color: tuple):
        """绘制单个统计项（居中）- 添加描边效果"""
        value_font = self._get_font(52, bold=True)
        label_font = self._get_font(20)
        
        # 计算文字宽度以居中
        value_bbox = draw.textbbox((0, 0), value, font=value_font)
        value_width = value_bbox[2] - value_bbox[0]
        
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_width = label_bbox[2] - label_bbox[0]
        
        # 绘制数值（居中，带描边）
        self._draw_text_with_stroke(
            draw, (x - value_width // 2, y), value, value_font,
            fill=color, stroke_color=(0, 0, 0), stroke_width=2
        )
        
        # 绘制标签（居中）
        draw.text((x - label_width // 2, y + 85), label, fill=self.text_secondary, font=label_font)
    
    def _draw_top_content(self, draw: ImageDraw, img: Image, report: Dict[str, Any], y: int, item_images: List[Optional[bytes]] = None) -> int:
        """绘制热门内容列表 - 参考前端样式"""
        # 标题
        title_font = self._get_font(42, bold=True)
        self._draw_text_with_stroke(
            draw, (50, y), "热门内容", title_font,
            fill=self.text_primary, stroke_color=(0, 0, 0), stroke_width=2
        )
        
        y += 90  # 增加间距
        top_content = report.get('top_content', [])[:5]  # 最多5个
        
        for i, item in enumerate(top_content):
            y = self._draw_content_item(draw, img, y, i, item, item_images[i] if item_images and i < len(item_images) else None)
            y += 20  # 卡片间距
        
        return y
    
    def _draw_content_item(self, draw: ImageDraw, img: Image, y: int, index: int, item: Dict[str, Any], cover_image: Optional[bytes]) -> int:
        """绘制单个内容项 - 参考 MP 插件实时获取封面"""
        card_padding = 50
        item_height = 170  # 增加高度以容纳更大的封面
        
        # 卡片背景
        draw.rounded_rectangle(
            [(card_padding, y), (self.width - card_padding, y + item_height)],
            radius=16,
            fill=self.card_color
        )
        
        x_offset = card_padding + 25
        
        # 排名 - 添加描边
        rank_font = self._get_font(52, bold=True)
        rank_text = f"#{index + 1}"
        self._draw_text_with_stroke(
            draw, (x_offset, y + 60), rank_text, rank_font,
            fill=self.accent_yellow, stroke_color=(0, 0, 0), stroke_width=3
        )
        
        x_offset += 85
        
        # 封面图 - 实时获取（参考 MP 插件）
        cover_width, cover_height = 110, 155
        item_id = item.get('item_id')
        
        # 实时获取封面图片
        logger.info(f"准备获取封面: item_id={item_id}, name={item.get('name')}")
        cover_bytes = self._fetch_cover_image(item_id, width=220, height=310) if item_id else None
        
        if cover_bytes:
            try:
                cover = Image.open(io.BytesIO(cover_bytes))
                # 调整封面大小为固定尺寸
                cover = cover.resize((cover_width, cover_height), Image.Resampling.LANCZOS)
                # 添加圆角
                cover = self._add_rounded_corners(cover, 8)
                # 粘贴到主图
                img.paste(cover, (x_offset, y + 8), cover if cover.mode == 'RGBA' else None)
                logger.info(f"封面绘制成功: {item.get('name')}")
            except Exception as e:
                logger.warning(f"封面图加载失败: {e}")
                self._draw_placeholder_cover(draw, x_offset, y + 8, cover_width, cover_height)
        else:
            logger.warning(f"封面获取失败，使用占位符: {item.get('name')}")
            self._draw_placeholder_cover(draw, x_offset, y + 8, cover_width, cover_height)
        
        x_offset += cover_width + 25
        
        # 内容信息
        name_font = self._get_font(30, bold=True)
        type_font = self._get_font(20)
        stat_font = self._get_font(20)
        
        # 标题（截断）- 添加描边
        name = item['name']
        if len(name) > 20:  # 调整截断长度
            name = name[:20] + "..."
        self._draw_text_with_stroke(
            draw, (x_offset, y + 30), name, name_font,
            fill=self.text_primary, stroke_color=(0, 0, 0), stroke_width=2
        )
        
        # 类型
        item_type = "电影" if item.get('type') == 'Movie' else "剧集"
        draw.text((x_offset, y + 75), item_type, fill=self.text_secondary, font=type_font)
        
        # 播放次数和时长
        hours = item.get('hours', 0)
        minutes = int((hours % 1) * 60)
        stat_text = f"{item['play_count']}次播放 · {int(hours)}h{minutes}m"
        draw.text((x_offset, y + 115), stat_text, fill=self.accent_cyan, font=stat_font)
        
        return y + item_height
    
    def _draw_placeholder_cover(self, draw: ImageDraw, x: int, y: int, width: int, height: int):
        """绘制占位封面"""
        # 背景
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=8,
            fill=(55, 65, 81)  # #374151
        )
        # 文字
        text = "无封面"
        font = self._get_font(14)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(
            (x + (width - text_width) // 2, y + (height - text_height) // 2),
            text,
            fill=(107, 114, 128),  # #6b7280
            font=font
        )
    
    def _add_rounded_corners(self, img: Image, radius: int) -> Image:
        """为图片添加圆角"""
        # 创建圆角遮罩
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
        
        # 应用遮罩
        output = img.copy()
        if output.mode != 'RGBA':
            output = output.convert('RGBA')
        output.putalpha(mask)
        return output
    
    def _draw_footer(self, draw: ImageDraw, y: int):
        """绘制页脚"""
        footer_font = self._get_font(22)
        footer_text = "New Emby Stats"  # 参考前端
        
        # 居中绘制
        bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((self.width - text_width) // 2, y + 40),
            footer_text,
            fill=self.text_secondary,
            font=footer_font
        )
    
    def _draw_text_with_stroke(self, draw: ImageDraw, xy: tuple, text: str, font: ImageFont,
                               fill: tuple, stroke_color: tuple, stroke_width: int):
        """绘制带描边的文字 - 参考 MP 插件的 PSD 风格"""
        x, y = xy
        # 绘制描边（8个方向）
        for offset_x in range(-stroke_width, stroke_width + 1):
            for offset_y in range(-stroke_width, stroke_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), text, font=font, fill=stroke_color)
        # 绘制主文字
        draw.text(xy, text, font=font, fill=fill)
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont:
        """获取字体 - 优先使用更好的中文字体"""
        try:
            # 检查资源目录中的字体
            if self.res_dir.exists():
                font_files = list(self.res_dir.glob("*.ttf")) + list(self.res_dir.glob("*.ttc"))
                if font_files:
                    # 优先使用 Bold 字体
                    if bold:
                        for font_file in font_files:
                            if 'bold' in font_file.name.lower():
                                return ImageFont.truetype(str(font_file), size)
                    # 使用第一个找到的字体
                    return ImageFont.truetype(str(font_files[0]), size)
            
            # 尝试使用系统中文字体
            font_paths = [
                # Windows
                "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                # Linux
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
            ]
            
            for font_path in font_paths:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)
            
            # 如果都不存在，使用默认字体
            logger.warning("未找到中文字体，使用默认字体")
            return ImageFont.load_default()
        
        except Exception as e:
            logger.warning(f"加载字体失败: {e}")
            return ImageFont.load_default()
    
    async def download_cover_image(self, image_url: str) -> Optional[bytes]:
        """下载封面图片"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                logger.warning(f"下载封面失败: {image_url}, HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"下载封面异常: {e}")
            return None


report_image_service = ReportImageService()
