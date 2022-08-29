
"""This module proivdes wrapper functionality for the imgur API"""

import requests
from pydantic import BaseModel
import dotenv, os

dotenv.load_dotenv()
AUTH_HEADER = {'Authorization': f"Client-ID {os.getenv('CLIENT_ID')}"}

API_ENDPOINTS = {
    'upload': 'https://api.imgur.com/3/upload/',
    'download': 'http://i.imgur.com/',
    'info': 'https://api.imgur.com/3/image/',
    'delete': 'https://api.imgur.com/3/image/',
    }


class RequestMaker:
    def __init__(self) -> None:
        self.credits = {
            k : None for k in (
            'X-RateLimit-UserLimit', 'X-RateLimit-UserRemaining',
            'X-RateLimit-UserReset', 'X-RateLimit-ClientLimit',
            'X-RateLimit-ClientRemaining', 'X-Post-Rate-Limit-Limit',
            'X-Post-Rate-Limit-Remaining', 'X-Post-Rate-Limit-Reset'
            )
        }
    
    def _update_credit_info(self, resp_headers) -> None:
        self.credits.update({
            k: v for k, v in resp_headers.items() if k in self.credits
        })
    
    def request(self, method: str, *args, **kwargs) -> dict | bytes:
        resp = requests.request(method, *args, **kwargs)
        self._update_credit_info(resp.headers)
        content_type = resp.headers['content-type']
        if 'image' in content_type:
            return resp.content
        elif 'json' in content_type:
            return resp.json()
        else:
            raise RuntimeError('Unexpected response content-type "{resp.content_type}"')
    

class ImgurClient:
    """Class to interact with various API endpoints"""
    def __init__(self) -> None:
        self._request = RequestMaker().request

    def upload_image(self, data: str) -> tuple[str, str]:
        """Upload an image and return img id and deletehash"""
        resp_body = self._request(
            'post',
            API_ENDPOINTS['upload'],
            headers=AUTH_HEADER, 
            data={'image': data, 'type': 'base64'}
        )
        data = resp_body['data']
        return data['id'], data['deletehash']
    
    def download_image(self, image_id: str, ext: str = 'png') -> bytes:
        """Download the image and return the data as bytes. If a file extension
        is not given, 'png' is used"""
        return self._request(
            'get',
            f"{API_ENDPOINTS['download']}{image_id}.{ext}",
        )
        
    def delete_image(self, deletehash: str) -> None:
        """Delete an image using a deletehash string"""
        self._request(
            'delete',
            API_ENDPOINTS['delete'] + deletehash, 
            headers=AUTH_HEADER
        )
