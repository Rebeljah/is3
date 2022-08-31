
import asyncio
import pickle
import random
import string
from pathlib import Path
from PIL import Image
from typing import Any, Optional

from pydantic import BaseModel

import utils
from wrapper import ImgurClient as Imgur

BUCKETS_FOLDER = Path(__file__).parent / 'buckets'


def make_bucket_id() -> str:
    return ''.join(random.choices(string.ascii_letters, k=6))


class _UploadedObject(BaseModel):
    obj_id: str
    deletehash: str


class _StagedObject(BaseModel):
    """Represents a bucket object that has been added to a bucket but not yet
    uploaded"""
    obj: Any

    def image(self) -> Image.Image:
        return utils.object_to_image(self.obj)


class _Bucket:
    def __init__(self, id: Optional[str] = None) -> None:
        self.id = id or make_bucket_id()
        self.uploaded_objects: dict[str, _UploadedObject] = {}
        self.staged_objects: list[_StagedObject] = []

    def add(self, *objs: tuple[Any]) -> None:
        for obj in objs:
            o = _StagedObject(obj=obj)
            self.staged_objects.append(o)
    
    async def get(self, *obj_ids: tuple[str]) -> list:
        return await(_download_objects(*obj_ids))
    
    async def push(self) -> None:
        objects = await _upload_objects(*self.staged_objects)
        self.staged_objects.clear()
        for o in objects:
            self.uploaded_objects[o.obj_id] = o
        self._save_to_disk()
    
    async def delete(self):
        """Delete the bucket and all objects it holds"""
        await _delete_objects(*self.uploaded_objects.values())
        (BUCKETS_FOLDER / self.id).unlink()
    
    def _save_to_disk(self):
        d = pickle.dumps(self.uploaded_objects)
        BUCKETS_FOLDER.mkdir(exist_ok=True)
        with open(BUCKETS_FOLDER / self.id, 'wb') as f:
            f.write(utils.compress(d))


async def _upload_objects(*objects: tuple[_StagedObject]) -> list[_UploadedObject]:
    async with Imgur() as imgur:
        images = (utils.image_to_b64_string(o.image()) for o in objects)
        coros = map(imgur.upload_image, images)
        obj_info = await asyncio.gather(*coros)
    
    uploaded_objects = []
    for obj_id, obj_deletehash in obj_info:
        o = _UploadedObject(obj_id=obj_id, deletehash=obj_deletehash)
        uploaded_objects.append(o)
    
    return uploaded_objects


async def _download_objects(*obj_ids: tuple[str]) -> list:
    async with Imgur() as imgur:
        coros = map(imgur.download_image, obj_ids)
        images: tuple[bytes] = await asyncio.gather(*coros)
    
    images = map(utils.bytes_to_image, images)
    downloaded_objects = list(map(utils.image_to_object, images))

    return downloaded_objects


async def _delete_objects(*objects: tuple[_UploadedObject]) -> None:
    async with Imgur() as imgur:
        deletehashes = (o.deletehash for o in objects)
        coros = map(imgur.delete_image, deletehashes)
        await asyncio.gather(*coros)


def new_bucket():
    return _Bucket()


def load_bucket(bucket_id: str) -> _Bucket:
    b = _Bucket(bucket_id)

    with open(BUCKETS_FOLDER / bucket_id, 'rb') as f:
        objects: dict = pickle.loads(utils.decompress(f.read()))
    
    b.uploaded_objects = objects

    return b


async def main():
    bucket = new_bucket()

    bucket.add(
        {'pi': 3.14},
        b'nobody',
        ['expects', 'the'],
        {'spammish', ('inquisition')},
    )

    await bucket.push()

    for k, v in bucket.uploaded_objects.items():
        print(k, v)

    bucket = load_bucket(bucket.id)

    ids = bucket.uploaded_objects.keys()
    objects = await bucket.get(*ids)
    print(*objects, sep='\n')

    await bucket.delete()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
