
from pydantic import BaseModel
from pathlib import Path
import json
import string
import random
from typing import Any, Optional

from wrapper import ImgurClient as Imgur
import utils

BUCKETS_FOLDER = Path(__file__).parent / 'buckets'


def make_bucket_id() -> str:
    return ''.join(random.choices(string.ascii_letters, k=6))


class BucketObject(BaseModel):
    is_uploaded: bool = False
    id: str = Optional[str]
    deletehash: Optional[str]
    obj: Optional[Any]

    def retrieve(self) -> Any:
        assert self.is_uploaded
        assert self.id is not None

        data = Imgur().download_image(self.id)
        img = utils.bytes_to_image(data)

        return utils.image_to_object(img)

    def push(self):
        assert not self.is_uploaded

        img = utils.object_to_image(self.obj)
        data = utils.image_to_b64_string(img)

        self.id, self.deletehash = Imgur().upload_image(data)
        self.is_uploaded = True
    
    def delete(self):
        assert self.is_uploaded
        assert self.deletehash is not None

        Imgur().delete_image(self.deletehash)

        self.is_uploaded = False
    
    @classmethod
    def new(cls, obj: Any):
        return cls(obj=obj)

    @classmethod
    def from_id(cls, id: str, deletehash: str):
        return BucketObject(id=id, deletehash=deletehash, is_uploaded=True)


class Bucket:
    def __init__(self, id: Optional[str] = None) -> None:
        self.id = id or make_bucket_id()
        self.objects: list[BucketObject] = []
    
    @property
    def is_synced(self) -> bool:
        return all(o.is_uploaded for o in self.objects)

    def add_object(self, obj: Any, push=False) -> None:
        o = BucketObject.new(obj)
        self.objects.append(o)

        if push:
            o.push()
    
    def get_object(self, id: str) -> Any:
        o = next((o for o in self.objects if o.id == id), None)
        if o is None:
            raise ValueError(f"object id not found '{id}'")
        
        return o.retrieve()
    
    def push_changes(self) -> None:
        for o in [o for o in self.objects if not o.is_uploaded]:
            o.push()
        
        self.save_to_disk()
    
    def delete(self):
        """Delete the bucket and all objects it holds"""
        for o in self.objects:
            o.delete()
        
        (BUCKETS_FOLDER / self.id).unlink()
    
    def save_to_disk(self):
        d = [(o.id, o.deletehash) for o in self.objects]
        d = json.dumps(d, indent=None, separators=(',',':'))

        BUCKETS_FOLDER.mkdir(exist_ok=True)
        with open(BUCKETS_FOLDER / self.id, 'wb') as f:
            f.write(utils.compress(d.encode()))

    @classmethod
    def new(cls):
        b = cls()
        b.save_to_disk()
        return b

    @classmethod
    def load(cls, id: str):
        b = cls(id)

        with open(BUCKETS_FOLDER / id, 'rb') as f:
            d = utils.decompress(f.read())

        for obj_id, obj_deletehash in json.loads(d):
            o = BucketObject.from_id(obj_id, obj_deletehash)
            b.objects.append(o)
        
        return b
