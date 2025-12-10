import logging
import asyncio
import httpx
from jinja2 import Environment, BaseLoader
from typing import Dict, Any, Optional
from config import settings as app_settings
from notification_settings import notification_settings_store, NotificationSettings

logger = logging.getLogger(__name__)

class NotificationService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._client = httpx.AsyncClient(timeout=30.0)
        self._jinja_env = Environment(loader=BaseLoader())
        self._settings = notification_settings_store.get_settings()
        notification_settings_store.register_change_callback(self._on_settings_change)
        self._initialized = True
        
    def _on_settings_change(self, new_settings: NotificationSettings):
        self._settings = new_settings
        logger.info("NotificationService updated with new settings")

    async def close(self):
        await self._client.aclose()

    async def _request_with_retry(self, method: str, url: str, **kwargs):
        retries = 3
        backoff = 1.0
        for i in range(retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                if i == retries - 1:
                    raise e
                logger.warning(f"Request to {url} failed (attempt {i+1}/{retries}): {e}")
                await asyncio.sleep(backoff)
                backoff *= 2
    
    async def get_ip_location(self, ip: str) -> str:
        if not ip or ip in ['127.0.0.1', '::1', 'localhost', '0.0.0.0']:
            return "本地"
        
        if ip.startswith(('192.168.', '10.', '172.')):
             return "局域网"

        try:
            resp = await self._client.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    parts = [data.get('country', ''), data.get('regionName', ''), data.get('city', ''), data.get('isp', '')]
                    return " ".join(filter(None, parts)).strip()
        except Exception as e:
            logger.warning(f"Failed to get IP location for {ip}: {e}")
        return "未知位置"

    async def render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        if not template_str:
            return ""
        try:
            template = self._jinja_env.from_string(template_str)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template_str

    async def get_tmdb_image(self, tmdb_id: str, media_type: str = 'movie') -> Optional[str]:
        if not self._settings.tmdb_enabled or not self._settings.tmdb_config.api_key:
            return None
            
        api_key = self._settings.tmdb_config.api_key
        try:
            url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={api_key}&language=zh-CN"
            resp = await self._request_with_retry("GET", url)
            data = resp.json()
            poster_path = data.get('backdrop_path') or data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w780{poster_path}"
        except Exception as e:
            logger.error(f"Failed to get TMDB image: {e}")
        return None

    async def get_image_url(self, item: Dict[str, Any], server_id: str) -> Optional[str]:
        # Try TMDB first if enabled
        provider_ids = item.get('ProviderIds', {})
        tmdb_id = provider_ids.get('Tmdb')
        
        if tmdb_id:
            media_type = 'movie'
            if item.get('Type') == 'Episode' or item.get('Type') == 'Series':
                media_type = 'tv'
            
            tmdb_image = await self.get_tmdb_image(str(tmdb_id), media_type)
            if tmdb_image:
                return tmdb_image
                
        # Fallback to Emby
        item_id = item.get('Id')
        if not item_id:
            return None
            
        primary_tag = item.get('ImageTags', {}).get('Primary')
        if primary_tag:
             emby_url = self._settings.emby_connection.url or app_settings.EMBY_URL
             if emby_url.endswith('/'):
                 emby_url = emby_url[:-1]
             return f"{emby_url}/emby/Items/{item_id}/Images/Primary?tag={primary_tag}&quality=90&maxWidth=800"
        
        return None

    async def _send_telegram(self, title: str, text: str, image_url: Optional[str] = None):
        if not self._settings.telegram_enabled or not self._settings.telegram_bot_token:
            return

        token = self._settings.telegram_bot_token
        # Combine admins and users
        chat_ids = set()
        for u in self._settings.telegram_users:
            if u.user_id: chat_ids.add(u.user_id)
        for a in self._settings.telegram_admins:
            if a.user_id: chat_ids.add(a.user_id)

        if not chat_ids:
            return

        message = f"*{title}*\n\n{text}"
        
        for chat_id in chat_ids:
            try:
                if image_url:
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    params = {"chat_id": chat_id, "caption": message, "photo": image_url, "parse_mode": "Markdown"}
                    await self._request_with_retry("POST", url, json=params)
                else:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    params = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
                    await self._request_with_retry("POST", url, json=params)
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {e}")

    async def _send_discord(self, title: str, text: str, image_url: Optional[str] = None):
        if not self._settings.discord_enabled or not self._settings.discord_webhooks:
            return

        embed = {
            "title": title,
            "description": text,
            "color": 3447003, 
        }
        if image_url:
            embed["image"] = {"url": image_url}

        payload = {
            "username": "Emby Stats",
            "embeds": [embed]
        }

        for webhook in self._settings.discord_webhooks:
            if not webhook.url:
                continue
            try:
                await self._request_with_retry("POST", webhook.url, json=payload)
            except Exception as e:
                logger.error(f"Failed to send Discord webhook: {e}")

    async def _send_wecom(self, title: str, text: str, image_url: Optional[str] = None):
         if not self._settings.wecom_enabled:
            return
         
         config = self._settings.wecom_config
         if not config.corp_id or not config.corp_secret or not config.agent_id:
             return
             
         try:
             token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={config.corp_id}&corpsecret={config.corp_secret}"
             
             client = self._client
             if config.proxy:
                 async with httpx.AsyncClient(proxies=config.proxy, timeout=30.0) as proxy_client:
                     resp = await proxy_client.get(token_url)
             else:
                 resp = await client.get(token_url)

             data = resp.json()
             access_token = data.get("access_token")
             
             if not access_token:
                 logger.error(f"Failed to get WeCom access token: {data}")
                 return

             send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
             
             payload = {
                 "touser": config.to_user or "@all",
                 "msgtype": "textcard",
                 "agentid": config.agent_id,
                 "textcard": {
                     "title": title,
                     "description": text,
                     "url": app_settings.EMBY_URL, 
                     "btntxt": "详情"
                 }
             }
             
             if image_url:
                 payload = {
                     "touser": config.to_user or "@all",
                     "msgtype": "news",
                     "agentid": config.agent_id,
                     "news": {
                         "articles": [
                             {
                                 "title": title,
                                 "description": text,
                                 "url": app_settings.EMBY_URL,
                                 "picurl": image_url
                             }
                         ]
                     }
                 }

             if config.proxy:
                 async with httpx.AsyncClient(proxies=config.proxy, timeout=30.0) as proxy_client:
                      await proxy_client.post(send_url, json=payload)
             else:
                 await client.post(send_url, json=payload)

         except Exception as e:
             logger.error(f"Failed to send WeCom message: {e}")

    async def process_event(self, payload: Dict[str, Any]):
        if not self._settings.enabled:
             return

        event_type = payload.get('Event', '')
        logger.debug(f"Processing Emby event: {event_type}")
        
        # Determine Template
        template_config = None
        if event_type == 'system.playback.start':
            template_config = self._settings.templates.playback
        elif event_type == 'system.user.login':
             template_config = self._settings.templates.login
        elif event_type in ['item.markplayed', 'item.markunplayed']:
             template_config = self._settings.templates.mark
        elif event_type == 'library.new':
             template_config = self._settings.templates.library
        else:
            if not event_type.startswith('system.playback.start'):
                return

        if not template_config:
            return

        # Extract Data
        user = payload.get('User', {})
        user_name = user.get('Name', 'Unknown')
        
        item = payload.get('Item', {})
        item_name = item.get('Name', item.get('OriginalTitle', 'Unknown Item'))
        
        session = payload.get('Session', {})
        device_name = session.get('DeviceName', 'Unknown Device')
        client = session.get('Client', 'Unknown Client')
        remote_endpoint = session.get('RemoteEndPoint', '')
        
        # Calculate progress if applicable
        playback_info = payload.get('PlaybackInfo', {})
        position_ticks = playback_info.get('PositionTicks', 0)
        run_time_ticks = item.get('RunTimeTicks', 0)
        percentage = 0
        if run_time_ticks > 0:
            percentage = int((position_ticks / run_time_ticks) * 100)

        context = {
            'user_name': user_name,
            'item_name': item_name,
            'device_name': device_name,
            'client': client,
            'ip': remote_endpoint,
            'event': event_type,
            'progress': percentage,
            'item_count': 1 # For library.new
        }
        
        # Special handling for library.new
        if event_type == 'library.new':
             items = payload.get('Items', [])
             if items:
                 context['item_count'] = len(items)
                 if len(items) == 1:
                     context['item_name'] = items[0].get('Name')
                     item = items[0] 

        # IP Location
        if remote_endpoint:
            location = await self.get_ip_location(remote_endpoint)
            context['location'] = location

        # Fetch image
        fetched_image_url = await self.get_image_url(item, payload.get('ServerId', ''))
        context['item_image'] = fetched_image_url or ''
        
        # Render Text
        title = await self.render_template(template_config.title, context)
        text = await self.render_template(template_config.text, context)
        
        # Image
        image_url = None
        if template_config.image_template:
            image_url = await self.render_template(template_config.image_template, context)
            if not image_url.startswith('http'):
                image_url = None 

        logger.info(f"Sending notification: {title}")
        
        await asyncio.gather(
            self._send_telegram(title, text, image_url),
            self._send_discord(title, text, image_url),
            self._send_wecom(title, text, image_url),
            return_exceptions=True
        )

    async def preview_notification(self, template_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        templates = self._settings.templates.model_dump()
        template_dict = templates.get(template_id)
        
        if not template_dict:
             raise ValueError("Template not found")
             
        title = await self.render_template(template_dict['title'], context)
        text = await self.render_template(template_dict['text'], context)
        image = None
        if template_dict.get('image_template'):
             image = await self.render_template(template_dict['image_template'], context)
             
        return {
            "title": title,
            "text": text,
            "image": image
        }

notification_service = NotificationService()
