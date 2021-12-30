#!/bin/bash

ENVFILE=$1

SCRIPTS_DIR=$(dirname "$(realpath $0)")
ENV_FILE=${ENVFILE:-"$SCRIPTS_DIR/load_env.sh"}

echo "Loading Env from $ENV_FILE"
source "$ENV_FILE"

REDIS_CONFIG="$SCRIPTS_DIR/redis.conf"


install_prereqs() {
    apt update && apt install -y curl fuse redis-server
    mkdir -p /content/cache/redis
}

install_juicefs() {
    if [[ "$(which juicefs)" == "" ]]; then
        echo "Installing JuiceFS for S3"
        mkdir -p /tmp/juicefs && \
        cd /tmp/juicefs && \
        JFS_LATEST_TAG=$(curl -s https://api.github.com/repos/juicedata/juicefs/releases/latest | grep 'tag_name' | cut -d '"' -f 4 | tr -d 'v') && \
        curl -s -L "https://github.com/juicedata/juicefs/releases/download/v${JFS_LATEST_TAG}/juicefs-${JFS_LATEST_TAG}-linux-amd64.tar.gz" \
        | tar -zx && \
        install juicefs /usr/bin && \
        cd .. && \
        rm -rf /tmp/juicefs
    fi
}

start_redis() {
    testRedis=$(redis-cli ping)
    if [[ "$testRedis" != "PONG" ]]; then
        echo "Starting Redis Server"
        cd /content/cache/redis
        nohup redis-server "$REDIS_CONFIG" &> /dev/null
    fi
}

stop_redis() {
    testRedis=$(redis-cli ping)
    if [[ "$testRedis" == "PONG" ]]; then
        echo "Stopping Redis Server"
        redis-cli shutdown
    fi
}

restore_backupfile() {
    ## Gs = 0, S3 = 1, min = 2
    bfExists=$(gsutil -q stat $STORAGE_BACKUP/storage_backup.tar.gz || echo 1)
    if [[ $bfExists != 1 ]]; then
        ## this means the file exists so we can restore it
        mkdir -p /content/cache/.backup
        gsutil -m cp $STORAGE_BACKUP/storage_backup.tar.gz /content/cache/storage_backup.tar.gz
        tar -zxvf /content/cache/storage_backup.tar.gz -C /content/cache/.backup
        stop_redis
        if [[ -f /content/cache/.backup/dump.rdb ]]; then
            cp /content/cache/.backup/dump.rdb /content/cache/redis/dump.rdb
        fi
        if [[ -f /content/cache/.backup/appendonly.aof ]]; then
            cp /content/cache/.backup/appendonly.aof /content/cache/redis/appendonly.aof
        fi
        start_redis

        if [[ -f /content/cache/.backup/gs_metadata.json && "$MOUNT_GS" == "True" && "$GS_BUCKET" != "" ]]; then
            juicefs load redis://127.0.0.1:6379/0 /content/cache/.backup/gs_metadata.json
        fi
        if [[ -f /content/cache/.backup/s3_metadata.json && "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" ]]; then
            juicefs load redis://127.0.0.1:6379/1 /content/cache/.backup/s3_metadata.json
        fi
        if [[ -f /content/cache/.backup/minio_metadata.json && "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" ]]; then
            juicefs load redis://127.0.0.1:6379/2 /content/cache/.backup/minio_metadata.json
        fi
        rm -rf /content/cache/.backup
        rm /content/cache/storage_backup.tar.gz
    fi
}

format_juicefs() {
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != ""  ]]; then
        echo "Formatting JuiceFS for Google Cloud Storage with Bucket $GS_BUCKET"
        juicefs format \
            --storage gs \
            --bucket $GS_BUCKET \
            --compress zstd \
            redis://127.0.0.1:6379/0 \
            colab
    fi
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" ]]; then
        S3_BUCKET_ENDPOINT="$S3_ENDPOINT/$S3_BUCKET"
        echo "Formatting JuiceFS for AWS S3 with Bucket $S3_BUCKET"
        juicefs format \
            --storage s3 \
            --access-key $AWS_ACCESS_KEY_ID \
            --secret-key $AWS_SECRET_ACCESS_KEY \
            --bucket $S3_BUCKET_ENDPOINT \
            --compress zstd \
            redis://127.0.0.1:6379/1 \
            colab
    fi
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" ]]; then
        MINIO_BUCKET_ENDPOINT="$MINIO_ENDPOINT/$MINIO_BUCKET"
        echo "Formatting JuiceFS for Minio with Bucket $MINIO_BUCKET"
        juicefs format \
            --storage minio \
            --bucket $MINIO_BUCKET_ENDPOINT \
            --access-key $MINIO_ACCESS_KEY \
            --secret-key $MINIO_SECRET_KEY \
            --compress zstd \
            redis://127.0.0.1:6379/2 \
            colab
    fi
}

mount_storagefs() {
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != "" && ! "$(ls -A $GS_MOUNT_PATH)" ]]; then
        echo "Mounting GCS Bucket $GS_BUCKET to $GS_MOUNT_PATH"
        mkdir -p $GS_MOUNT_PATH
        mkdir -p /content/cache/.juicefs/gs
        sudo juicefs mount -d \
            --no-usage-report \
            --writeback \
            --cache-dir /content/cache/.juicefs/gs \
            --log /content/cache/juicefs_gs.log \
            -o allow_other,writeback_cache \
            redis://127.0.0.1:6379/0 \
            $GS_MOUNT_PATH
        sudo juicefs warmup -b $GS_MOUNT_PATH
    fi
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" && ! "$(ls -A $S3_MOUNT_PATH)" ]]; then
        echo "Mounting S3 Bucket $S3_BUCKET to $S3_MOUNT_PATH"
        mkdir -p $S3_MOUNT_PATH
        mkdir -p /content/cache/.juicefs/s3
        sudo juicefs mount -d \
            --no-usage-report \
            --writeback \
            --cache-dir /content/cache/.juicefs/s3 \
            --log /content/cache/juicefs_s3.log \
            -o allow_other,writeback_cache \
            redis://127.0.0.1:6379/1 \
            $S3_MOUNT_PATH
        sudo juicefs warmup -b $S3_MOUNT_PATH
    fi
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" && ! "$(ls -A $MINIO_MOUNT_PATH)" ]]; then
        echo "Mounting Minio Bucket $MINIO_BUCKET to $MINIO_MOUNT_PATH"
        mkdir -p $MINIO_MOUNT_PATH
        mkdir -p /content/cache/.juicefs/minio
        sudo juicefs mount -d \
            --no-usage-report \
            --writeback \
            --cache-dir /content/cache/.juicefs/minio \
            --log /content/cache/juicefs_minio.log \
            -o allow_other,writeback_cache \
            redis://127.0.0.1:6379/2 \
            $MINIO_MOUNT_PATH
        sudo juicefs warmup -b $MINIO_MOUNT_PATH
    fi
}

install_prereqs
install_juicefs

## Attempt to restore backupfile if redis file doesnt exist
if [[ ! -f /content/cache/redis/appendonly.aof ]]; then
    restore_backupfile
else
    start_redis
    format_juicefs
fi
mount_storagefs

