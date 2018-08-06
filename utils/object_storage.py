import os
from datetime import datetime
from pathlib import Path, PurePath
from utils.config import IS_DEV

from utils.human_ids import humanize

import swiftclient


def swift_con():
    user = os.environ.get('OVH_USER')
    key = os.environ.get('OVH_PASSWORD')

    tenant_name = '4754281319661209'
    auth_url = 'https://auth.cloud.ovh.net/v2.0/'
    options = {
        'region_name': 'GRA3'
    }
    auth_version = '2'
    return swiftclient.Connection(user=user,
                                  key=key,
                                  authurl=auth_url,
                                  os_options=options,
                                  tenant_name=tenant_name,
                                  auth_version=auth_version)


STORAGE_DIR = Path(os.path.dirname(os.path.realpath(__file__)))\
              / '..' / 'static' / 'object_store_data'


def local_dir(bucket, id):
    if '/' in id:
        idFolders = PurePath(id).parent
    else:
        idFolders = ''
    return STORAGE_DIR / bucket / idFolders


def local_path(bucket, id):
    return local_dir(bucket, id) / PurePath(id).name


def store_public_object(bucket, id, blob, content_type):
    os.makedirs(local_dir(bucket, id), exist_ok=True)
    newFile = open(local_path(bucket, id), "wb")
    newFile.write(blob)
    newTypeFile = open(str(local_path(bucket, id))+".type", "w")
    newTypeFile.write(content_type)

    if not IS_DEV:
        container_name = os.environ.get('OVH_BUCKET_NAME')
        # we want to store data with a special path
        storage_path = 'storage/thumbs/' + id
        swift_con().put_object(container_name,
                               storage_path,
                               contents=blob,
                               content_type=content_type)


def delete_public_object(bucket, id):
    lpath = local_path(bucket, id)
    if os.path.isfile(lpath):
        os.remove(lpath)


def get_public_object_date(bucket, id):
    lpath = local_path(bucket, id)
    if not os.path.isfile(lpath):
        return None
    return datetime.fromtimestamp(os.path.getmtime(lpath))
