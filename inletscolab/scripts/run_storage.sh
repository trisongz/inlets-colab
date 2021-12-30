#!/bin/bash

ENVFILE=$1
SAVE_INTERVAL=$2

SCRIPTS_DIR=$(dirname "$(realpath $0)")
ENV_FILE=${ENVFILE:-"$SCRIPTS_DIR/load_env.sh"}

# every 5 mins
INTERVAL=${SAVE_INTERVAL:-300}

create_backupfile() {
    ## Gs = 0, S3 = 1, min = 2
    redis-cli save
    mkdir -p /content/cache/.backup
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != ""  ]]; then
        juicefs dump redis://127.0.0.1:6379/0 /content/cache/.backup/gs_metadata.json
    fi
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" ]]; then
        juicefs dump redis://127.0.0.1:6379/1 /content/cache/.backup/s3_metadata.json
    fi
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" ]]; then
        juicefs dump redis://127.0.0.1:6379/2 /content/cache/.backup/minio_metadata.json
    fi
    cp /content/cache/redis/dump.rdb /content/cache/.backup/dump.rdb
    cp /content/cache/redis/appendonly.aof /content/cache/.backup/appendonly.aof
    tar -zcvf /content/cache/storage_backup.tar.gz /content/cache/.backup/
}

run_backup() {
    echo "Loading Env from $ENV_FILE"
    source "$ENV_FILE"
    echo "Backing Up Storage to $STORAGE_BACKUP"
    create_backupfile
    gsutil -m cp /content/cache/storage_backup.tar.gz "$STORAGE_BACKUP/"
    rm -rf /content/cache/.backup
    rm /content/cache/storage_backup.tar.gz
}

while ((1)) ; do
    run_backup
    sleep $INTERVAL
done
