import asyncio


async def demo():
    import is3
    
    # creating a new bucket
    bucket = is3.Bucket('my-is3-bucket')

    # adding items to a bucket and uploading them
    some_object = {'hello': b'world', ('foo', 'bar'): {'baz'}}
    bucket.stage_obj(some_object, 'my-object')
    bucket.stage_obj(['another', 'one'], 'my-other-object')

    await bucket.commit()

    # loading a bucket from disk
    bucket = is3.Bucket.load('my-is3-bucket')

    # retrieving items stored in a bucket
    retrieved_object = await bucket.get_obj('my-object')
    assert retrieved_object == {'hello': b'world', ('foo', 'bar'): {'baz'}}

    # delete a specific item in a bucket
    await bucket.delete_obj('my-object')

    # delete an entire bucket and its contents
    await bucket.delete()


loop = asyncio.new_event_loop()
loop.run_until_complete(demo())
