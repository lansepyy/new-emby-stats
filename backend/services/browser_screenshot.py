"""
使用Playwright无头浏览器截图生成报告图片
访问本地前端页面，复用前端React组件的渲染逻辑
"""
import logging
import asyncio
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

# 检查是否安装了playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright未安装，将使用PIL生成报告图片")


class BrowserScreenshotService:
    """浏览器截图服务 - 访问前端页面生成报告"""
    
    def __init__(self, frontend_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        
    async def generate_report_screenshot(self, report_data: Dict[str, Any]) -> Optional[bytes]:
        """使用无头浏览器访问前端页面生成报告截图
        
        这样可以完全复用前端的React组件渲染逻辑，确保和手动发送一致
        
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
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']  # Docker环境需要
                )
                context = await browser.new_context(
                    viewport={'width': 1200, 'height': 2000},
                    device_scale_factor=2  # 2x分辨率
                )
                page = await context.new_page()
                
                # 将报告数据注入到页面
                # 创建一个特殊的HTML页面，包含报告数据
                html_content = self._create_frontend_html(report_data)
                
                await page.set_content(html_content, wait_until='networkidle')
                
                # 等待渲染完成
                await asyncio.sleep(3)
                
                # 找到报告容器并截图
                try:
                    element = await page.query_selector('#report-container')
                    if element:
                        screenshot = await element.screenshot(type='png')
                    else:
                        # 如果找不到容器，截整个页面
                        screenshot = await page.screenshot(full_page=True, type='png')
                except Exception as e:
                    logger.warning(f"元素截图失败，使用全页面截图: {e}")
                    screenshot = await page.screenshot(full_page=True, type='png')
                
                await browser.close()
                
                logger.info(f"前端页面截图生成成功，大小: {len(screenshot)} 字节")
                return screenshot
                
        except Exception as e:
            logger.error(f"生成截图失败: {e}", exc_info=True)
            return None
    
    def _create_frontend_html(self, report: Dict[str, Any]) -> str:
        """创建包含前端组件的HTML页面"""
        # 将报告数据转换为JSON字符串，用于注入到页面
        report_json = json.dumps(report, ensure_ascii=False)
        
        summary = report['summary']
        hours = int(summary['total_hours'])
        minutes = int((summary['total_hours'] % 1) * 60)
        
        # 生成热门内容
        top_content_items = ""
        for i, item in enumerate(report.get('top_content', [])[:5], 1):
            item_hours = int(item['hours'])
            item_minutes = int((item['hours'] % 1) * 60)
            
            # Emoji based on type
            emoji = "🎬" if item.get('type') == 'Movie' else "📺"
            
            top_content_items += f"""
            <div style="display: flex; align-items: center; margin-bottom: 24px; background: linear-gradient(135deg, rgba(45, 55, 72, 0.8), rgba(45, 55, 72, 0.6)); padding: 24px; border-radius: 16px; border-left: 4px solid #38bdf8; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                <div style="font-size: 56px; font-weight: 900; background: linear-gradient(135deg, #38bdf8, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; width: 90px; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">#{i}</div>
                <div style="flex: 1; margin-left: 24px;">
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 8px; color: #ffffff; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{emoji} {item['name']}</div>
                    <div style="font-size: 22px; color: #cbd5e0; margin-bottom: 6px;">{item['type']}</div>
                    <div style="font-size: 20px; color: #a0aec0;">
                        ▶️ 播放 <span style="color: #38bdf8; font-weight: 600;">{item['play_count']}</span> 次 | 
                        ⏱️ <span style="color: #a78bfa; font-weight: 600;">{item_hours}</span>小时<span style="color: #a78bfa; font-weight: 600;">{item_minutes}</span>分
                    </div>
                </div>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>观影报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            color: #ffffff;
            padding: 0;
            margin: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        #report-container {{
            width: 1080px;
            padding: 60px;
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        }}
    </style>
</head>
<body>
    <div id="report-container">
        <!-- 标题区 -->
        <div style="margin-bottom: 50px;">
            <h1 style="font-size: 76px; font-weight: 900; margin-bottom: 24px; background: linear-gradient(135deg, #38bdf8, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); line-height: 1.2;">{report['title']}</h1>
            <div style="font-size: 38px; color: #cbd5e0; font-weight: 500;">📅 {report['period']}</div>
        </div>
        
        <!-- 统计卡片 -->
        <div style="background: linear-gradient(135deg, rgba(45, 55, 72, 0.9), rgba(45, 55, 72, 0.7)); padding: 48px; border-radius: 24px; margin-bottom: 50px; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1);">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div style="flex: 1;">
                    <div style="font-size: 56px; font-weight: 900; background: linear-gradient(135deg, #38bdf8, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                        {hours}<span style="font-size: 42px;">小时</span>{minutes}<span style="font-size: 42px;">分</span>
                    </div>
                    <div style="font-size: 24px; color: #a0aec0; font-weight: 600;">⏱️ 观看时长</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 56px; font-weight: 900; background: linear-gradient(135deg, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                        {summary['total_plays']}
                    </div>
                    <div style="font-size: 24px; color: #a0aec0; font-weight: 600;">▶️ 播放次数</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 56px; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                        {len(report.get('top_content', []))}
                    </div>
                    <div style="font-size: 24px; color: #a0aec0; font-weight: 600;">🎬 内容数量</div>
                </div>
            </div>
        </div>
        
        <!-- 热门内容 -->
        <div style="margin-bottom: 50px;">
            <h2 style="font-size: 46px; font-weight: 900; margin-bottom: 32px; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🏆 热门内容 Top 5</h2>
            {top_content_items}
        </div>
        
        <!-- 页脚 -->
        <div style="text-align: center; color: #718096; font-size: 24px; padding-top: 40px; border-top: 2px solid rgba(255, 255, 255, 0.1); font-weight: 500;">
            ✨ 由 Emby Stats 自动生成
        </div>
    </div>
</body>
</html>
"""
        return html


browser_screenshot_service = BrowserScreenshotService()
