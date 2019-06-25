#!/usr/bin/env bash


if [ "$1" == "-h" ]; then
    echo "$(basename "$0") [-h] [-d directory_to_upload_path -i index -t threads] -- program to upload images to OVH object storage
where:
    -h  show this help text
    -d  images directories absolute path (with / at the end)
    -i  directory index to start from (0 to 999)
    -t  number of threads for import"
    exit 0
fi

source ovh_object_storage_env
virtualenv import_titelive

source import_titelive/bin/activate
pip install python-swiftclient python-keystoneclient

# GET FOLDER TO UPLOAD PATH
if [[ $# -gt 1 ]] && [[ "$1" == "-d" ]]; then
  absolute_path_to_directory=$2
  shift 2
else
  echo "You must provide an absolute path for backups directory."
  exit 1
fi

# GET FOLDER INDEX TO START FROM
if [[ $# -gt 1 ]] && [[ "$1" == "-i" ]]; then
  index=$2
  shift 2
else
  index=0
fi

# GET THREADS NUMBER
if [[ $# -gt 1 ]] && [[ "$1" == "-t" ]]; then
  THREAD_POOL_SIZE=$2
  shift 2
else
  THREAD_POOL_SIZE=10
fi

thread_count=()

function get_thread_count(){
    process_ids=$(pgrep swift)
    IFS='
    ' read -d '' -a thread_count <<< "${process_ids}"
}

cd "$absolute_path_to_directory"
titelive_directories=$(find "thumbs" -mindepth 1 -maxdepth 1 -type d | sort)

IFS='
' read -d '' -a images_directories <<< "${titelive_directories}"

count=0

for directory in "${images_directories[@]:$index}"
do
    echo "${#thread_count[@]}"

    while [ "${#thread_count[@]}" -ge "$THREAD_POOL_SIZE" ]
    do
        echo "waiting for available pool thread..."
        get_thread_count
        sleep 5
    done

    echo "[Uploading] $directory"
    x-terminal-emulator -e swift --os-auth-url "$OVH_AUTH_URL" \
          --os-tenant-name "$OVH_TENANT_NAME" \
          --os-username "$OVH_USER" \
          --os-password "$OVH_PASSWORD" \
          --os-region-name "$OVH_REGION" \
          -V 2 upload "$CONTAINER_NAME" \
          --object-name 'thumbs/products' \
          --ignore-checksum "$directory"
done

deactivate
