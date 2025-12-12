"""
观影报告图片生成服务
"""
import io
import logging
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportImageService:
    """报告图片生成服务"""
    
    def __init__(self):
        self.width = 768
        self.bg_color = (26, 32, 44)  # 深色背景
        self.card_color = (45, 55, 72)  # 卡片背景
        self.text_primary = (255, 255, 255)  # 主文字
        self.text_secondary = (160, 174, 192)  # 次要文字
        self.accent_cyan = (56, 189, 248)  # 青色
        self.accent_purple = (167, 139, 250)  # 紫色
        self.accent_yellow = (251, 191, 36)  # 黄色
        
    def generate_report_image(self, report: Dict[str, Any], item_images: List[Optional[bytes]] = None) -> bytes:
        """生成报告图片
        
        Args:
            report: 报告数据
            item_images: 热门内容的封面图片列表（字节数据）
        
        Returns:
            PNG图片字节数据
        """
        # 计算高度
        header_height = 200
        stats_height = 200
        content_height = len(report.get('top_content', [])) * 140 + 80
        footer_height = 60
        total_height = header_height + stats_height + content_height + footer_height
        
        # 创建画布
        img = Image.new('RGB', (self.width, total_height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # 绘制各部分
        y_offset = 0
        y_offset = self._draw_header(draw, report, y_offset)
        y_offset = self._draw_stats(draw, report, y_offset)
        y_offset = self._draw_top_content(draw, img, report, y_offset, item_images)
        self._draw_footer(draw, total_height - footer_height)
        
        # 转换为字节
        output = io.BytesIO()
        img.save(output, format='PNG', quality=95)
        return output.getvalue()
    
    def _draw_header(self, draw: ImageDraw, report: Dict[str, Any], y: int) -> int:
        """绘制标题区域"""
        # 标题
        title_font = self._get_font(48, bold=True)
        draw.text((40, y + 40), report['title'], fill=self.text_primary, font=title_font)
        
        # 日期
        date_font = self._get_font(24)
        draw.text((40, y + 110), report['period'], fill=self.text_secondary, font=date_font)
        
        return y + 200
    
    def _draw_stats(self, draw: ImageDraw, report: Dict[str, Any], y: int) -> int:
        """绘制统计卡片"""
        summary = report['summary']
        
        # 卡片背景
        card_padding = 40
        card_y = y + 20
        card_height = 140
        draw.rounded_rectangle(
            [(card_padding, card_y), (self.width - card_padding, card_y + card_height)],
            radius=16,
            fill=self.card_color
        )
        
        # 三列统计数据
        col_width = (self.width - 2 * card_padding) // 3
        
        # 观看时长
        self._draw_stat_item(
            draw, 
            card_padding + col_width * 0 + col_width // 2,
            card_y + 40,
            f"{summary['total_hours']}小时{int((summary['total_hours'] % 1) * 60)}分",
            "观看时长",
            self.accent_cyan
        )
        
        # 播放次数
        self._draw_stat_item(
            draw,
            card_padding + col_width * 1 + col_width // 2,
            card_y + 40,
            f"{summary['total_plays']}次",
            "播放次数",
            self.accent_purple
        )
        
        # 观看内容
        total_items = len(report.get('top_content', []))
        self._draw_stat_item(
            draw,
            card_padding + col_width * 2 + col_width // 2,
            card_y + 40,
            f"{total_items}部",
            "观看内容",
            self.accent_yellow
        )
        
        # 底部详细信息
        movie_count = sum(1 for item in report.get('top_content', []) if item.get('type') == 'Movie')
        episode_count = sum(1 for item in report.get('top_content', []) if item.get('type') == 'Episode')
        movie_hours = sum(item.get('hours', 0) for item in report.get('top_content', []) if item.get('type') == 'Movie')
        episode_hours = sum(item.get('hours', 0) for item in report.get('top_content', []) if item.get('type') == 'Episode')
        
        detail_text = f"电影 {movie_count}部 · {movie_hours:.0f}h{int((movie_hours % 1) * 60)}m    剧集 {episode_count}集 · {episode_hours:.0f}h{int((episode_hours % 1) * 60)}m"
        detail_font = self._get_font(16)
        
        # 居中绘制
        bbox = draw.textbbox((0, 0), detail_text, font=detail_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((self.width - text_width) // 2, card_y + card_height - 40),
            detail_text,
            fill=self.text_secondary,
            font=detail_font
        )
        
        return card_y + card_height + 40
    
    def _draw_stat_item(self, draw: ImageDraw, x: int, y: int, value: str, label: str, color: tuple):
        """绘制单个统计项（居中）"""
        value_font = self._get_font(32, bold=True)
        label_font = self._get_font(14)
        
        # 计算文字宽度以居中
        value_bbox = draw.textbbox((0, 0), value, font=value_font)
        value_width = value_bbox[2] - value_bbox[0]
        
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_width = label_bbox[2] - label_bbox[0]
        
        # 绘制数值（居中）
        draw.text((x - value_width // 2, y), value, fill=color, font=value_font)
        
        # 绘制标签（居中）
        draw.text((x - label_width // 2, y + 50), label, fill=self.text_secondary, font=label_font)
    
    def _draw_top_content(self, draw: ImageDraw, img: Image, report: Dict[str, Any], y: int, item_images: List[Optional[bytes]] = None) -> int:
        """绘制热门内容列表"""
        # 标题
        title_font = self._get_font(28, bold=True)
        draw.text((40, y), "热门内容", fill=self.text_primary, font=title_font)
        
        y += 60
        top_content = report.get('top_content', [])[:5]  # 最多5个
        
        for i, item in enumerate(top_content):
            y = self._draw_content_item(draw, img, y, i, item, item_images[i] if item_images and i < len(item_images) else None)
        
        return y
    
    def _draw_content_item(self, draw: ImageDraw, img: Image, y: int, index: int, item: Dict[str, Any], cover_image: Optional[bytes]) -> int:
        """绘制单个内容项"""
        card_padding = 40
        item_height = 120
        
        # 卡片背景
        draw.rounded_rectangle(
            [(card_padding, y), (self.width - card_padding, y + item_height)],
            radius=12,
            fill=self.card_color
        )
        
        x_offset = card_padding + 20
        
        # 排名
        rank_font = self._get_font(36, bold=True)
        draw.text((x_offset, y + 40), f"#{index + 1}", fill=self.accent_yellow, font=rank_font)
        
        x_offset += 60
        
        # 封面图
        if cover_image:
            try:
                cover = Image.open(io.BytesIO(cover_image))
                # 调整封面大小 (保持比例)
                cover.thumbnail((70, 100))
                # 粘贴到主图
                img.paste(cover, (x_offset, y + 10))
            except Exception as e:
                logger.warning(f"封面图加载失败: {e}")
        
        x_offset += 90
        
        # 内容信息
        name_font = self._get_font(20, bold=True)
        type_font = self._get_font(14)
        stat_font = self._get_font(14)
        
        # 标题（截断）
        name = item['name']
        if len(name) > 20:
            name = name[:20] + "..."
        draw.text((x_offset, y + 25), name, fill=self.text_primary, font=name_font)
        
        # 类型
        item_type = "电影" if item.get('type') == 'Movie' else "剧集"
        draw.text((x_offset, y + 55), item_type, fill=self.text_secondary, font=type_font)
        
        # 播放次数和时长
        hours = item.get('hours', 0)
        minutes = int((hours % 1) * 60)
        stat_text = f"{item['play_count']}次播放 · {int(hours)}h{minutes}m"
        draw.text((x_offset, y + 80), stat_text, fill=self.accent_cyan, font=stat_font)
        
        return y + item_height + 20
    
    def _draw_footer(self, draw: ImageDraw, y: int):
        """绘制页脚"""
        footer_font = self._get_font(16)
        footer_text = "Emby Stats"
        
        # 居中绘制
        bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((self.width - text_width) // 2, y + 20),
            footer_text,
            fill=self.text_secondary,
            font=footer_font
        )
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont:
        """获取字体"""
        try:
            # 尝试使用系统中文字体
            font_paths = [
                # Windows
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                # Linux
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
            ]
            
            if bold:
                font_paths.insert(0, "C:/Windows/Fonts/msyhbd.ttc")  # 微软雅黑 Bold
            
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
