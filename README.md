# is3

is3 uses imgur to enable bucket storage of arbitray objects. Use at your own risk!

First import is3
```py
import is3
```

Creating a new bucket
```py
bucket = is3.Bucket('my-is3-bucket')
```

Adding and uploading objects
```py
some_object = {'hello': b'world', ('foo', 'bar'): {'baz'}}
another_one = ['another', 'one']

bucket.stage_obj(some_object, 'my-object')
bucket.stage_obj(another_one, 'my-other-object')

await bucket.commit()
```

Loading a bucket from disk
```py
bucket = is3.Bucket.load('my-is3-bucket')
```

Retrieving items stored in a bucket
```py
obj = await bucket.get_obj('my-object')
assert obj == {'hello': b'world', ('foo', 'bar'): {'baz'}}
```

Delete a specific item in a bucket
```py
await bucket.delete_obj('my-object')
```

Delete an entire bucket and its contents
```py
await bucket.delete()
```

You will need to register your application with the Imgur API and put your API client-ID in a .env file like this:

![The .env file contining the client id for the imgur API](https://i.imgur.com/McS1hQp.png)

Objects are stored as PNG images on Imgur, here is the entire text of Shakespeare's Hamlet as uploaded by is3:

![Image containing compressed data of Hamlet](https://i.imgur.com/yEUUVLE.png)
