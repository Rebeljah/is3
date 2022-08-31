# is3

is3 uses imgur to enable bucket storage of arbitray objects. Use at your own risk!

Example usage:
```py
import is3

bucket = is3.new_bucket()

# stage some objects to be uploaded
bucket.add(
    {'pi': 3.14},
    b'nobody',
    ['expects', 'the'],
    {'spammish', ('inquisition')},
)

# upload the staged objects and save bucket index to disk
await bucket.push()

for k, v in bucket.uploaded_objects.items():
    print(k, v)
"""
prints:
xQMJt0N obj_id='xQMJt0N' deletehash='usl5fBowV9yDeVt'
6Dg6DvU obj_id='6Dg6DvU' deletehash='Ebxh1akg81cWpaE'
FEkvW3h obj_id='FEkvW3h' deletehash='ZUvGK3LkONom2v3'
hltKjaW obj_id='hltKjaW' deletehash='kJ7WLwpRwN1A8HU'
"""

# load bucket from disk
bucket = load_bucket(bucket.id)

# download get all of the previously uploaded objects
ids = bucket.uploaded_objects.keys()
objects = await bucket.get(*ids)
print(*objects, sep='\n')
"""
prints:
{'pi': 3.14}
b'nobody'
['expects', 'the']
{'spammish', 'inquisition'}
"""

# delete all uploaded objects and remove the bucket index from the disk
await bucket.delete()
```

You will need to register your application with the Imgur API and put your API client-ID in a .env file like this:

![The .env file contining the client id for the imgur API](https://i.imgur.com/McS1hQp.png)

Objects are stored as PNG images on Imgur, here is the entire text of Shakespeare's Hamlet as uploaded by is3:

![Image containing compressed data of Hamlet](https://i.imgur.com/yEUUVLE.png)
