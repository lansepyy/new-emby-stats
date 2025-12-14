"""
使用Playwright无头浏览器截图生成报告图片
"""
import logging
import asyncio
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# 检查是否安装了playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright未安装，将使用PIL生成报告图片")


class BrowserScreenshotService:
    """浏览器截图服务"""
    
    def __init__(self, frontend_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        
    async def generate_report_screenshot(self, report_data: Dict[str, Any]) -> Optional[bytes]:
        """使用无头浏览器生成报告截图
        
        Args:
            report_data: 报告数据
            
        Returns:
            PNG图片字节，如果失败返回None
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright未安装，无法生成截图")
            return None
            
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1080, 'height': 1920},
                    device_scale_factor=2  # 2x分辨率，提高清晰度
                )
                page = await context.new_page()
                
                # 构造包含报告数据的HTML页面
                html_content = self._generate_report_html(report_data)
                
                # 加载HTML内容
                await page.set_content(html_content)
                
                # 等待字体和图片加载
                await asyncio.sleep(2)
                
                # 截图
                screenshot = await page.screenshot(
                    full_page=True,
                    type='png'
                )
                
                await browser.close()
                
                logger.info(f"截图生成成功，大小: {len(screenshot)} 字节")
                return screenshot
                
        except Exception as e:
            logger.error(f"生成截图失败: {e}")
            return None
    
    def _generate_report_html(self, report: Dict[str, Any]) -> str:
        """生成报告HTML页面"""
        summary = report['summary']
        hours = int(summary['total_hours'])
        minutes = int((summary['total_hours'] % 1) * 60)
        
        # 生成热门内容HTML
        top_content_html = ""
        for i, item in enumerate(report.get('top_content', [])[:5], 1):
            item_hours = int(item['hours'])
            item_minutes = int((item['hours'] % 1) * 60)
            top_content_html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px; background: #2d3748; padding: 20px; border-radius: 12px;">
                <div style="font-size: 52px; font-weight: bold; color: #38bdf8; width: 80px; text-align: center;">#{i}</div>
                <div style="flex: 1; margin-left: 20px;">
                    <div style="font-size: 30px; font-weight: bold; margin-bottom: 5px;">{item['name']}</div>
                    <div style="font-size: 20px; color: #a0aec0;">{item['type']}</div>
                    <div style="font-size: 20px; color: #a0aec0; margin-top: 5px;">
                        播放 {item['play_count']} 次 | {item_hours}小时{item_minutes}分
                    </div>
                </div>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
            background: #1a202c;
            color: white;
            width: 1080px;
            padding: 50px;
        }}
    </style>
</head>
<body>
    <!-- 标题 -->
    <div style="margin-bottom: 40px;">
        <h1 style="font-size: 72px; font-weight: bold; margin-bottom: 20px;">{report['title']}</h1>
        <div style="font-size: 36px; color: #a0aec0;">{report['period']}</div>
    </div>
    
    <!-- 统计卡片 -->
    <div style="background: #2d3748; padding: 40px; border-radius: 20px; margin-bottom: 40px;">
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div>
                <div style="font-size: 52px; font-weight: bold; color: #38bdf8; margin-bottom: 10px;">
                    {hours}小时{minutes}分
                </div>
                <div style="font-size: 20px; color: #a0aec0;">观看时长</div>
            </div>
            <div>
                <div style="font-size: 52px; font-weight: bold; color: #a78bfa; margin-bottom: 10px;">
                    {summary['total_plays']}
                </div>
                <div style="font-size: 20px; color: #a0aec0;">播放次数</div>
            </div>
            <div>
                <div style="font-size: 52px; font-weight: bold; color: #fbbf24; margin-bottom: 10px;">
                    {len(report.get('top_content', []))}
                </div>
                <div style="font-size: 20px; color: #a0aec0;">内容数量</div>
            </div>
        </div>
    </div>
    
    <!-- 热门内容 -->
    <div style="margin-bottom: 40px;">
        <h2 style="font-size: 42px; font-weight: bold; margin-bottom: 30px;">🎬 热门内容 Top 5</h2>
        {top_content_html}
    </div>
    
    <!-- 页脚 -->
    <div style="text-align: center; color: #a0aec0; font-size: 22px; padding-top: 30px; border-top: 1px solid #2d3748;">
        由 Emby Stats 自动生成
    </div>
</body>
</html>
"""
        return html


browser_screenshot_service = BrowserScreenshotService()
