
"""This module proivdes wrapper functionality for the imgur API"""

import aiohttp
import dotenv, os

dotenv.load_dotenv()
AUTH_HEADER = {'Authorization': f"Client-ID {os.getenv('CLIENT_ID')}"}

API_ENDPOINTS = {
    'upload': 'https://api.imgur.com/3/upload/',
    'download': 'http://i.imgur.com/',
    'info': 'https://api.imgur.com/3/image/',
    'delete': 'https://api.imgur.com/3/image/',
    }


# class RequestMaker:
#     def __init__(self) -> None:
#         self.credits = {
#             k : None for k in (
#             'X-RateLimit-UserLimit', 'X-RateLimit-UserRemaining',
#             'X-RateLimit-UserReset', 'X-RateLimit-ClientLimit',
#             'X-RateLimit-ClientRemaining', 'X-Post-Rate-Limit-Limit',
#             'X-Post-Rate-Limit-Remaining', 'X-Post-Rate-Limit-Reset'
#             )
#         }
    
#     def _update_credit_info(self, resp_headers) -> None:
#         self.credits.update({
#             k: v for k, v in resp_headers.items() if k in self.credits
#         })

class ImgurClient:
    """Class to interact with various API endpoints"""
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()
    
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

    async def upload_image(self, data: str) -> tuple[str, str]:
        """Upload an image and return img id and deletehash"""
        r = await self._request(
            method='post',
            url=API_ENDPOINTS['upload'],
            headers=AUTH_HEADER, 
            data={'image': data, 'type': 'base64'}
        )
        return r['id'], r['deletehash']
    
    async def download_image(self, image_id: str) -> bytes:
        """Download the image and return the data as bytes."""
        url = API_ENDPOINTS['download'] + image_id + '.png'
        return await self._request('get', url)
        
    async def delete_image(self, deletehash: str) -> None:
        """Delete an image using a deletehash string"""
        url = API_ENDPOINTS['delete'] + deletehash
        await self._request('delete', url, headers=AUTH_HEADER)
