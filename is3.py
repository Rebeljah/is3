
import pickle
import asyncio
from pathlib import Path
from pydantic import BaseModel

from typing import Any
from PIL import Image
ObjectName = ObjectId = BucketName = str

import utils
from wrapper import ImgurClient as Imgur

BUCKETS_FOLDER = Path(__file__).parent / 'buckets'
EXTENSION = '.bkt'

def filename(name: str):
    return name + EXTENSION


class UploadedObject(BaseModel):
    """Represents an object that has been uploaded"""
    name: ObjectName
    obj_id: ObjectId
    deletehash: str
    cached_obj: Any = None

    def __getstate__(self):
        d = super().__getstate__()
        d['__dict__']['cached_obj'] = None
        d['__fields_set__'].discard('cached_obj')
        return d

    async def download(self) -> Any:
        """Return the wrapped object."""
        if self.cached_obj is not None:
            return self.cached_obj

        async with Imgur() as imgur:
            img = await imgur.download_image(self.obj_id)

        obj = self.cached_obj = utils.image_to_object(img)
        return obj
    
    async def delete(self) -> None:
        """Delete the uploaded object"""
        async with Imgur() as imgur:
            await imgur.delete_image(self.deletehash)


class StagedObject(BaseModel):
    """Represents a bucket object that has been added to a bucket but not yet
    uploaded"""
    name: ObjectName
    obj: Any

    def image(self) -> Image.Image:
        return utils.object_to_image(self.obj)
    
    async def upload(self) -> UploadedObject:
        """Upload the wrapped object and return an UploadedObject.
        
        The wrapped object is cached to the UploadObject so that a retrieval
        during the same runtime does not need to download the object.
        """
        async with Imgur() as imgur:
            oid, delete = await imgur.upload_image(self.image())
        
        return UploadedObject(
            name=self.name,
            obj_id=oid,
            deletehash=delete,
            cached_obj=self.obj
        )


class Bucket:
    def __init__(self, name) -> None:
        self.name = name
        self.uploaded: dict[ObjectName, UploadedObject] = {}
        self.pending: dict[ObjectName, StagedObject] = {}
    
    def __repr__(self) -> str:
        n_pending = len(self.pending)
        n_uploaded = len(self.uploaded)
        return f'<Bucket {self.name} (pending: {n_pending}, uploaded: {n_uploaded})>'
    
    def _save(self):
        """Pickle and dump the bucket to the buckets folder"""
        fn = filename(self.name)
        utils.write_compressed(pickle.dumps(self), BUCKETS_FOLDER / fn)

    def stage_obj(self, obj: Any, name: str) -> None:
        self.pending[name] = StagedObject(obj=obj, name=name)

        self._save()
    
    def unstage_obj(self, name: str) -> None:
        del self.pending[name]
        self._save()
    
    async def commit(self):
        """Upload all staged objects"""
        coros = [o.upload() for o in self.pending.values()]

        # upload concurrently and filter out errors
        results = await asyncio.gather(*coros, return_exceptions=True)
        uploaded = [e for e in results if isinstance(e, UploadedObject)]
        
        # remove succesful uploads from pending
        for o in uploaded:
            del self.pending[o.name]

        # track uploaded objects
        self.uploaded.update({o.name: o for o in uploaded})

        self._save()

        # warn about unuploaded pending objects
        if self.pending:
            msg = (
                f"{len(self.pending)} objects failed to upload:\n" +
                '\n'.join(o.name for o in self.pending.values())
            )
            raise Warning(msg)
    
    async def get_obj(self, name: str) -> Any:
        return await self.uploaded[name].download()

    async def delete_obj(self, name: str) -> None:
        """Remove the object with the given name from uploaded objects"""
        if not (o := self.uploaded.pop(name, 0)):
            raise ValueError(f'No obj with name {name} found in {self}')

        await o.delete()
        self._save()
    
    async def delete(self):
        """Delete the bucket and all objects it holds"""
        coros = [o.delete() for o in self.uploaded.values()]
        await asyncio.gather(*coros)
        (BUCKETS_FOLDER / filename(self.name)).unlink()

    @classmethod
    def load(cls, name: str) -> "Bucket":
        fn = filename(name)
        return pickle.loads(utils.read_compressed(BUCKETS_FOLDER / fn))
