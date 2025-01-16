import aiohttp
import json
from typing import Dict, List, Optional
import logging
from pathlib import Path
import hashlib
from datetime import datetime
import asyncio
from .secure_storage import SecureStorage

logger = logging.getLogger(__name__)

class TemplateSharing:
    def __init__(self, config):
        self.config = config
        self.secure_storage = SecureStorage()
        self.template_cache: Dict[str, Dict] = {}
        self._template_lock = asyncio.Lock()

    async def share_template(self, template_data: Dict) -> str:
        """Share a template to the community repository"""
        try:
            template_hash = self._generate_template_hash(template_data)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.API_URL}/templates/share",
                    json={
                        "template": template_data,
                        "hash": template_hash,
                        "author": self.secure_storage.retrieve("username"),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    headers=self._get_auth_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["template_id"]
                    raise Exception(f"Failed to share template: {response.status}")
                    
        except Exception as e:
            logger.error(f"Template sharing failed: {str(e)}")
            raise

    async def get_shared_templates(self, category: Optional[str] = None) -> List[Dict]:
        """Get templates from the community repository"""
        try:
            params = {"category": category} if category else {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.API_URL}/templates/shared",
                    params=params,
                    headers=self._get_auth_headers()
                ) as response:
                    if response.status == 200:
                        templates = await response.json()
                        async with self._template_lock:
                            for template in templates:
                                self.template_cache[template["id"]] = template
                        return templates
                    raise Exception(f"Failed to get shared templates: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to get shared templates: {str(e)}")
            raise

    async def import_template(self, template_id: str) -> bool:
        """Import a shared template to local storage"""
        try:
            template = self.template_cache.get(template_id)
            if not template:
                template = await self._fetch_template(template_id)
            
            if not template:
                raise Exception(f"Template {template_id} not found")
                
            template_dir = Path("data/templates")
            template_dir.mkdir(exist_ok=True)
            
            with open(template_dir / f"{template['name']}.json", "w") as f:
                json.dump(template["data"], f, indent=2)
                
            logger.info(f"Imported template: {template['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Template import failed: {str(e)}")
            return False

    async def _fetch_template(self, template_id: str) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.API_URL}/templates/{template_id}",
                    headers=self._get_auth_headers()
                ) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch template: {str(e)}")
            return None

    def _generate_template_hash(self, template_data: Dict) -> str:
        """Generate a unique hash for the template"""
        template_str = json.dumps(template_data, sort_keys=True)
        return hashlib.sha256(template_str.encode()).hexdigest()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        token = self.secure_storage.retrieve("api_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
