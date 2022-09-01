
"""This module proivdes wrapper functionality for the imgur API"""

import dotenv, os
from PIL import Image
from aiohttp import ClientSession

from typing import Optional

import utils

dotenv.load_dotenv()
AUTH_HEADER = {'Authorization': f"Client-ID {os.getenv('CLIENT_ID')}"}
API_ENDPOINTS = {
    'upload': 'https://api.imgur.com/3/upload/',
    'download': 'http://i.imgur.com/',
    'info': 'https://api.imgur.com/3/image/',
    'delete': 'https://api.imgur.com/3/image/',
    }

class ImgurClient:
    """Class to interact with various API endpoints"""
    def __init__(self, session: Optional[ClientSession] = None) -> None:
        self._session = session or ClientSession()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *err):
        await self._session.close()
    
    async def _request(
        self,
        method: str,
        url: str,
        *args, **kwargs
        ) -> dict | bytes:
        """Make a request with the specified method to the endpoint. All requests
        should either return raw image data as bytes or other data as JSON"""
        async with self._session.request(method, url, *args, **kwargs) as resp:
            match resp.content_type:
                case 'image/png': return await resp.read()
                case 'application/json': return (await resp.json())['data']
                case _: raise RuntimeError(
                    'Unexpected response content-type "{resp.content_type}"'
                    )

    async def upload_image(self, img: Image.Image) -> tuple[str, str]:
        """Upload an image and return img id and deletehash"""
        data = utils.image_to_b64_string(img)
        r = await self._request(
            method='post',
            url=API_ENDPOINTS['upload'],
            headers=AUTH_HEADER, 
            data={'image': data, 'type': 'base64'}
        )
        return r['id'], r['deletehash']
    
    async def download_image(self, image_id: str) -> Image.Image:
        """Download the image and return the data as bytes."""
        url = API_ENDPOINTS['download'] + image_id + '.png'
        data = await self._request('get', url)

        return utils.bytes_to_image(data)
        
    async def delete_image(self, deletehash: str) -> None:
        """Delete an image using a deletehash string"""
        url = API_ENDPOINTS['delete'] + deletehash
        await self._request('delete', url, headers=AUTH_HEADER)
