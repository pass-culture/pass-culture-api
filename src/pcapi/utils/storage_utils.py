import os
from pathlib import Path

import swiftclient

from pcapi import settings


def swift_con(dest_container_name):
    if dest_container_name == "storage-pc-dev":
        user = settings.OVH_USER_TESTING
        key = settings.OVH_PASSWORD_TESTING
        tenant_name = settings.OVH_TENANT_NAME_TESTING
        region_name = settings.OVH_REGION_NAME_TESTING
    elif dest_container_name == "storage-pc-staging":
        user = settings.OVH_USER_STAGING
        key = settings.OVH_PASSWORD_STAGING
        tenant_name = settings.OVH_TENANT_NAME_STAGING
        region_name = settings.OVH_REGION_NAME_STAGING
    else:
        print("Ce conteneur ne semble pas exister")
        return 1

    auth_url = "https://auth.cloud.ovh.net/v3/"
    options = {"region_name": region_name}
    auth_version = "3"
    return swiftclient.Connection(
        user=user, key=key, authurl=auth_url, os_options=options, tenant_name=tenant_name, auth_version=auth_version
    )


def swift_con_prod():
    user = settings.OVH_USER_PROD
    key = settings.OVH_PASSWORD_PROD
    tenant_name = settings.OVH_TENANT_NAME_PROD
    region_name = settings.OVH_REGION_NAME_PROD

    auth_url = "https://auth.cloud.ovh.net/v3/"
    options = {"region_name": region_name}
    auth_version = "3"
    return swiftclient.Connection(
        user=user, key=key, authurl=auth_url, os_options=options, tenant_name=tenant_name, auth_version=auth_version
    )


def do_local_backup_prod_container(dest_folder_name):
    # TODO: move this to use settings.OVH_BUCKET_NAME
    if "OVH_BUCKET_NAME" in os.environ:
        prod_container_name = os.environ.get("OVH_BUCKET_NAME")
        prod_conn = swift_con_prod()
    else:
        print("OVH_BUCKET_NAME does not seem to be set.")
        return 1

    download_count = 0
    object_count = 0
    print("Backup starting")

    for data in prod_conn.get_container(prod_container_name)[1]:
        obj_tuple = prod_conn.get_object(prod_container_name, data["name"])
        destination_path = (
            Path(os.path.dirname(os.path.realpath(__file__))) / ".." / "static" / dest_folder_name / data["name"]
        )
        object_count += 1
        if not destination_path.is_file() or data["bytes"] != destination_path.stat().st_size:
            with open(destination_path, "wb") as destination_file:
                destination_file.write(obj_tuple[1])
            download_count += 1
            print("Object [" + data["name"] + "] retrieved")

    print("Backup done.")
    print("%s objects listed" % object_count)
    print("%s objects downloaded." % download_count)

    return 0


def do_copy_prod_container_content_to_dest_container(dest_container_name):
    if dest_container_name == "storage-pc-staging" or dest_container_name == "storage-pc-dev":
        conn = swift_con(dest_container_name)
    else:
        print("Ce conteneur ne semble pas exister")
        return 1

    # TODO: move this to use settings.OVH_BUCKET_NAME
    if "OVH_BUCKET_NAME" in os.environ:
        prod_container_name = os.environ.get("OVH_BUCKET_NAME")
        prod_conn = swift_con_prod()
    else:
        print("OVH_BUCKET_NAME does not seem to be set.")
        return 1

    for data in prod_conn.get_container(prod_container_name)[1]:
        obj_tuple = prod_conn.get_object(prod_container_name, data["name"])
        conn.put_object(dest_container_name, data["name"], contents=obj_tuple[1], content_type=data["content_type"])
        print("Object [" + data["name"] + "] copied")

    return 0


# file_name format : "thumbs/venues/SM"
def do_does_file_exist(container_name, file_name):
    if container_name == "storage-pc-staging" or container_name == "storage-pc-dev":
        conn = swift_con(container_name)
    elif container_name == "storage-pc":
        conn = swift_con_prod()
    else:
        print("Ce conteneur ne semble pas exister")
        return 1

    for data in conn.get_container(container_name)[1]:
        if data["name"] == file_name:
            print("File exist !")
            return 0

    print("File does not exist.")
    return 0


def do_delete_file(container_name, file_name):
    if container_name == "storage-pc-staging" or container_name == "storage-pc-dev":
        conn = swift_con(container_name)
    elif container_name == "storage-pc":
        conn = swift_con_prod()
    else:
        print("Ce conteneur ne semble pas exister")
        return 1
    try:
        conn.delete_object(container_name, file_name)
        print("File deleted with success !")
    except swiftclient.ClientException as err:
        print("File deletion failed.")
        print(err)


def do_list_content(container_name):
    if container_name == "storage-pc-dev":
        conn = swift_con(container_name)
        container_url_path = settings.OVH_URL_PATH_TESTING
    elif container_name == "storage-pc-staging":
        conn = swift_con(container_name)
        container_url_path = settings.OVH_URL_PATH_STAGING
    elif container_name == "storage-pc":
        conn = swift_con_prod()
        container_url_path = settings.OVH_URL_PATH_PROD
    else:
        raise ValueError("Ce conteneur ne semble pas exister")

    objects_urls = []
    for data in conn.get_container(container_name)[1]:
        object_url = container_url_path + data["name"]
        objects_urls.append(object_url)

    return objects_urls
