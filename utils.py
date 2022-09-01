import io
import math
import zlib
import base64
import pickle
import numpy as np
from PIL import Image

from os import PathLike
from typing import Any

HEADER_SIZE = 4  # bytes


def compress(b: bytes, level=9) -> bytes:
    """Compress the bytes using zlib"""
    return zlib.compress(b, level)


def decompress(b: bytes) -> bytes:
    """Decompress the bytes using zlib"""
    return zlib.decompress(b)


def object_to_image(obj: Any) -> Image.Image:
    """Take a object and convert it to an image.
    
    The object is first pickled to bytes, then the array is padded and reshaped
    into a NxNx4 array and converted to an RGBA image

    Example of 1d pickle array to image array:
    [1,2,3,4,5,6,7] ->
    [
        [[0,0,0,7], [1,2,3,4]],
        [[5,6,7,0], [0,0,0,0]]
    ]
    The array begins with a 4 byte header representing the length of the data.
    Zeroes are added to the end the ensure that the number pixels is a suare number
    """
    data = compress(pickle.dumps(obj))
    header = len(data).to_bytes(length=HEADER_SIZE, byteorder='big')
    data = header + data

    # divide the data into pixels, add an extra if data doesn't perfectly fit
    whole_pixels, remainder = divmod(len(data), 4)
    n_pixels = whole_pixels + 1 * (remainder != 0)

    # ensure n_pixels is a square number
    side_length = math.ceil(math.sqrt(n_pixels))
    n_pixels = side_length ** 2
    n_bytes = n_pixels * 4

    # right pad the data with zeros so it can be shaped to (n,n,4)
    data += b'\x00' * (n_bytes - len(data))
    
    # create (n,n,4) array from pickle data
    data_arr = np.frombuffer(data, dtype=np.uint8)
    img_arr = np.reshape(data_arr, (side_length, side_length, 4))

    return Image.fromarray(img_arr)


def image_to_object(image: Image.Image) -> Any:
    """Take a PIL Image and unpickle it's data to an object
    
    Convert the image to an array, flatten to obtain serial bytes, then unpickle
    these bytes.
    """
    data_arr = np.array(image).flatten()
    data = data_arr.tobytes()

    # number of bytes containing meaningful data
    length = int.from_bytes(data[:HEADER_SIZE], 'big')

    # slice off header
    data = data[HEADER_SIZE:]
    # slice off zero padding if any
    data = data[:length]

    return pickle.loads(decompress(data))


def image_to_b64_string(img: Image.Image) -> str:
    """Return a str representing the image as b64 encoded bytes"""
    # save the image as PNG to a buffer
    buffer = io.BytesIO()
    img.save(buffer, 'png')
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode()


def bytes_to_image(b: bytes) -> Image.Image:
    """Create an Image using raw bytes"""
    buffer = io.BytesIO(b)
    buffer.seek(0)
    
    return Image.open(buffer)


def write_compressed(data: bytes, fp: PathLike) -> None:
    with open(fp, 'wb') as f:
        f.write(compress(data))


def read_compressed(fp: PathLike) -> bytes:
    with open(fp, 'rb') as f:
        return decompress(f.read())
