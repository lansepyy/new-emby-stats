"""TMDB电影数据库服务"""
import logging
from typing import Optional, Dict, Any
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)


class TMDBService:
    """TMDB图片和信息获取服务"""
    
    def __init__(self, api_key: str, image_base_url: str = "https://image.tmdb.org/t/p/original", emby_server: str = ""):
        self.api_key = api_key
        self.image_base_url = image_base_url
        self.emby_server = emby_server
    
    def get_image_url(self, item: Dict[str, Any]) -> Optional[str]:
        """获取媒体项的图片URL（优先TMDB，回退Emby本地）"""
        if not self.api_key:
            logger.warning("TMDB API密钥未配置，使用Emby本地图片")
            return self.get_emby_local_image(item)
        
        try:
            if item.get("Type") == "Episode":
                return self.get_episode_image(item)
            elif item.get("Type") == "Movie":
                return self.get_movie_image(item)
            else:
                return self.get_emby_local_image(item)
        except Exception as e:
            logger.error(f"获取TMDB图片失败: {str(e)}")
            return self.get_emby_local_image(item)
    
    def get_episode_image(self, item: Dict[str, Any]) -> Optional[str]:
        """获取剧集图片（优先背景图）"""
        series_name = item.get("SeriesName", "").strip()
        if not series_name:
            return self.get_emby_local_image(item)
        
        year = item.get("ProductionYear")
        logger.info(f"搜索TMDB剧集: {series_name} ({year or '无年份'})")
        
        try:
            params = {
                "api_key": self.api_key,
                "query": quote(series_name),
                "language": "zh-CN",
                "include_adult": "false"
            }
            if year:
                params["first_air_date_year"] = year
            
            search_url = "https://api.themoviedb.org/3/search/tv"
            resp = requests.get(search_url, params=params, timeout=10)
            
            if resp.status_code != 200:
                logger.error(f"TMDB搜索失败: HTTP {resp.status_code}")
                return self.get_emby_local_image(item)
            
            results = resp.json().get("results", [])
            if not results:
                logger.debug("TMDB无匹配结果")
                return self.get_emby_local_image(item)
            
            # 选择最受欢迎的结果
            best_match = max(results, key=lambda x: x.get("popularity", 0))
            series_id = best_match.get("id")
            
            # 获取详细信息
            detail_url = f"https://api.themoviedb.org/3/tv/{series_id}"
            detail_resp = requests.get(detail_url, params={"api_key": self.api_key, "language": "zh-CN"}, timeout=10)
            
            if detail_resp.status_code == 200:
                data = detail_resp.json()
                
                # 优先背景图
                backdrop_path = data.get("backdrop_path")
                if backdrop_path:
                    return f"{self.image_base_url}{backdrop_path}"
                
                # 回退海报图（使用weserv转横图）
                poster_path = data.get("poster_path")
                if poster_path:
                    encoded_path = f"{self.image_base_url[8:]}{poster_path}"
                    return (
                        f"https://images.weserv.nl/"
                        f"?url={encoded_path}"
                        f"&fit=contain&width=1280&height=720&bg=000000"
                    )
        
        except Exception as e:
            logger.error(f"TMDB剧集处理异常: {str(e)}")
        
        return self.get_emby_local_image(item)
    
    def get_movie_image(self, item: Dict[str, Any]) -> Optional[str]:
        """获取电影图片（优先背景图）"""
        tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
        if not tmdb_id:
            logger.debug("电影缺少TMDB ID")
            return self.get_emby_local_image(item)
        
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.api_key}&language=zh-CN"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 优先背景图
                backdrop_path = data.get("backdrop_path")
                if backdrop_path:
                    return f"{self.image_base_url}{backdrop_path}"
                
                # 回退海报图（使用weserv转横图）
                poster_path = data.get("poster_path")
                if poster_path:
                    encoded_path = f"{self.image_base_url[8:]}{poster_path}"
                    return (
                        f"https://images.weserv.nl/"
                        f"?url={encoded_path}"
                        f"&fit=contain&width=1280&height=720&bg=000000"
                    )
        except Exception as e:
            logger.warning(f"获取电影图片失败: {str(e)}")
        
        return self.get_emby_local_image(item)
    
    def get_emby_local_image(self, item: Dict[str, Any]) -> Optional[str]:
        """获取Emby本地图片（优先背景图）"""
        if not self.emby_server:
            return None
        
        try:
            item_id = item.get("Id")
            if not item_id:
                return None
            
            # 尝试背景图
            image_url = f"{self.emby_server}/Items/{item_id}/Images/Backdrop?fillWidth=1280&fillHeight=720&quality=90"
            if self.verify_image_url(image_url):
                return image_url
            
            # 回退主图（竖图转横图）
            image_url = f"{self.emby_server}/Items/{item_id}/Images/Primary?quality=90"
            if self.verify_image_url(image_url):
                encoded = image_url.replace("https://", "").replace("http://", "")
                return f"https://images.weserv.nl/?url={encoded}&fit=contain&width=1280&height=720&bg=000000"
        
        except Exception as e:
            logger.error(f"获取Emby本地图片失败: {str(e)}")
        
        return None
    
    def verify_image_url(self, url: str) -> bool:
        """验证图片URL是否有效"""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_movie_info(self, tmdb_id: str) -> Optional[Dict[str, Any]]:
        """获取电影详细信息"""
        if not self.api_key or not tmdb_id:
            return None
        
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.api_key}&language=zh-CN"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取电影信息失败: {str(e)}")
        
        return None
