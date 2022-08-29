# is3

is3 uses imgur to enable bucket storage of arbitray objects. Use at your own risk!

Example usage:
```py
import is3

bucket = is3.Bucket.new()

# add some stuff
bucket.add_object(['hello', 'world'])
bucket.add_object(b'careful! this string bytes!')

# upload all added objects
bucket.push_changes()

# load a bucket file from disk
bucket = is3.Bucket.load(bucket.id)

#  get an uploaded item. Prints the added list ['hello', 'world']
print(bucket.objects[0].retrive())

# delete all objects uploaded in the bucket and delete the bucket file
bucket.delete()
```

You will need to register your application with the Imgur API and put your API client-ID in a .env file like this:
![The .env file contining the client id for the imgur API](https://i.imgur.com/McS1hQp.png)

Objects are stored as PNG images on Imgur, here is the entire text of Shakespeare's Hamlet as uploaded by is3
![Image containing compressed data of Hamlet](https://i.imgur.com/yEUUVLE.png)
