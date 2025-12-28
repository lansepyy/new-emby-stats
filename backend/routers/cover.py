"""
封面生成 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
import logging
import urllib.parse

from services.cover_generator import cover_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cover", tags=["cover"])


class GenerateCoverRequest(BaseModel):
    """生成封面请求"""
    library_id: str
    library_name: str
    style: str = "multi_1"  # single_1, single_2, multi_1
    title: Optional[str] = None
    subtitle: Optional[str] = None
    use_title: bool = True
    poster_count: int = 9
    use_blur: bool = False
    use_macaron: bool = True
    use_film_grain: bool = True
    blur_size: int = 15
    color_ratio: float = 0.7
    font_size_ratio: float = 0.12
    date_font_size_ratio: float = 0.05
    # 动画相关参数
    is_animated: bool = False
    frame_count: int = 30
    frame_duration: int = 50
    output_format: str = "gif"  # gif, webp


@router.get("/libraries")
async def get_libraries():
    """获取媒体库列表"""
    try:
        libraries = await cover_service.get_library_list()
        return {
            "success": True,
            "data": libraries
        }
    except Exception as e:
        logger.error(f"获取媒体库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_cover(request: GenerateCoverRequest):
    """生成封面"""
    try:
        logger.info(f"收到封面生成请求: {request.library_name}, 风格: {request.style}, 动画: {request.is_animated}")
        logger.info(f"完整请求数据: {request.dict()}")
        logger.info(f"标题信息: title='{request.title}', subtitle='{request.subtitle}'")
        logger.info(f"动画参数: frame_count={request.frame_count}, frame_duration={request.frame_duration}, output_format={request.output_format}")
        logger.info(f"🔍 判断条件: style={request.style}, is_animated={request.is_animated}, 进入分支: {'动画' if request.is_animated else '静态'}")
        
        # 根据是否启用动画决定生成类型（与upload接口逻辑保持一致）
        if request.is_animated:
            # ===== 生成动画版本 =====
            logger.info("开始生成动画封面...")
            image_data = await cover_service.generate_animated_cover(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                subtitle=request.subtitle,
                style=request.style,
                frame_count=request.frame_count,
                frame_duration=request.frame_duration,
                output_format=request.output_format,
                use_title=request.use_title,
                use_macaron=request.use_macaron,
                use_film_grain=request.use_film_grain,
                poster_count=request.poster_count
            )
            
            # 根据输出格式设置 content_type
            content_type = f"image/{request.output_format}"
            logger.info(f"✅ 动画封面生成成功，类型: {content_type}, 大小: {len(image_data)} bytes")
            return Response(
                content=image_data,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="cover.{request.output_format}"'
                }
            )
        
        # ===== 生成静态版本 =====
        if request.style == "multi_1":
            # 多图拼贴风格 - 静态版本
            logger.info("开始生成多图静态封面...")
            image_data = await cover_service.generate_style_multi(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                subtitle=request.subtitle,
                poster_count=request.poster_count,
                use_blur=request.use_blur,
                blur_size=request.blur_size,
                color_ratio=request.color_ratio
            )
        elif request.style == "single_1":
            # 单图风格1 - 卡片旋转（只支持静态）
            logger.info("开始生成单图风格1封面...")
            image_data = await cover_service.generate_style_single(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                subtitle=request.subtitle,
                use_film_grain=request.use_film_grain,
                blur_size=request.blur_size,
                color_ratio=request.color_ratio
            )
        elif request.style == "single_2":
            # 单图风格2 - 斜线分割（只支持静态）
            logger.info("开始生成单图风格2封面...")
            image_data = await cover_service.generate_style_single_2(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                subtitle=request.subtitle
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的风格: {request.style}")
        
        if not image_data:
            raise HTTPException(status_code=500, detail="封面生成失败")
        
        # 生成文件名并进行 URL 编码
        filename = f"{request.library_name}_cover.png"
        encoded_filename = urllib.parse.quote(filename)
        
        # 返回图片,使用 RFC 5987 格式支持中文文件名
        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成封面失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成封面失败: {str(e)}")


@router.get("/preview/{library_id}")
async def preview_library(
    library_id: str,
    limit: int = Query(default=9, ge=1, le=50)
):
    """预览媒体库项目（用于前端显示）"""
    try:
        items = await cover_service.get_library_items(library_id, limit=limit)
        
        # 只返回必要信息
        preview_items = []
        for item in items:
            preview_items.append({
                "id": item.get("Id"),
                "name": item.get("Name"),
                "type": item.get("Type"),
                "has_primary_image": "ImageTags" in item and "Primary" in item.get("ImageTags", {})
            })
        
        return {
            "success": True,
            "data": preview_items
        }
    except Exception as e:
        logger.error(f"预览媒体库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{library_id}")
async def upload_cover_to_emby(
    library_id: str,
    request: GenerateCoverRequest
):
    """生成并上传封面到 Emby"""
    try:
        logger.info(f"开始生成并上传封面: {request.library_name}")
        
        # 生成封面
        if request.is_animated:
            # 动画封面
            image_data = await cover_service.generate_animated_cover(
                library_id=request.library_id,
                library_name=request.library_name,
                style=request.style,
                frame_count=request.frame_count,
                frame_duration=request.frame_duration,
                output_format=request.output_format,
                use_title=request.use_title,
                use_macaron=request.use_macaron,
                use_film_grain=request.use_film_grain,
                poster_count=request.poster_count
            )
        elif request.style == "multi_1":
            # 多图拼贴风格
            image_data = await cover_service.generate_style_multi(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                subtitle=request.subtitle,
                poster_count=request.poster_count,
                use_blur=request.use_blur,
                use_macaron=request.use_macaron
            )
        else:
            # 单图马卡龙风格
            image_data = await cover_service.generate_style_single(
                library_id=request.library_id,
                library_name=request.library_name,
                title=request.title,
                use_film_grain=request.use_film_grain,
                blur_size=request.blur_size,
                color_ratio=request.color_ratio
            )
        
        if not image_data:
            raise HTTPException(status_code=500, detail="封面生成失败")
        
        logger.info(f"封面生成成功，大小: {len(image_data)} 字节")
        
        # 上传到 Emby
        from services.emby import emby_service
        
        success = await emby_service.upload_library_image(
            library_id=library_id,
            image_data=image_data,
            image_type="Primary"
        )
        
        if success:
            logger.info(f"封面已成功上传到Emby: {library_id}")
            return {
                "success": True,
                "message": "封面已生成并上传到Emby",
                "library_id": library_id
            }
        else:
            raise HTTPException(status_code=500, detail="上传封面到Emby失败")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传封面失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
