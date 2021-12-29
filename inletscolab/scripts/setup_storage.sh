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
        nohup redis-server "$REDIS_CONFIG" &
    fi
}


format_juicefs() {
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != ""  ]]; then
        echo "Formatting JuiceFS for Google Cloud Storage with Bucket $GS_BUCKET"
        juicefs format \
            --storage gs \
            --bucket $GS_BUCKET \
            redis://127.0.0.1:6379/0 \
            gscolab
    fi
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" ]]; then
        S3_BUCKET_ENDPOINT="$S3_ENDPOINT/$S3_BUCKET"
        echo "Formatting JuiceFS for AWS S3 with Bucket $S3_BUCKET"
        juicefs format \
            --storage s3 \
            --bucket $S3_BUCKET_ENDPOINT \
            redis://127.0.0.1:6379/1 \
            s3colab
    fi
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" ]]; then
        MINIO_BUCKET_ENDPOINT="$MINIO_ENDPOINT/$MINIO_BUCKET"
        echo "Formatting JuiceFS for Minio with Bucket $MINIO_BUCKET"
        juicefs format \
            --storage minio \
            --bucket $MINIO_BUCKET_ENDPOINT \
            --access-key $MINIO_ACCESS_KEY \
            --secret-key $MINIO_SECRET_KEY \
            redis://127.0.0.1:6379/2 \
            miniocolab
    fi
}

mount_storagefs() {
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != "" && ! "$(ls -A $GS_MOUNT_PATH)" ]]; then
        echo "Mounting GCS Bucket $GS_BUCKET to $GS_MOUNT_PATH"
        mkdir -p $GS_MOUNT_PATH
        sudo juicefs mount -d -o allow_other,writeback_cache redis://127.0.0.1:6379/0 $GS_MOUNT_PATH
    fi
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" && ! "$(ls -A $S3_MOUNT_PATH)" ]]; then
        echo "Mounting S3 Bucket $S3_BUCKET to $S3_MOUNT_PATH"
        mkdir -p $S3_MOUNT_PATH
        sudo juicefs mount -d -o allow_other,writeback_cache redis://127.0.0.1:6379/1 $S3_MOUNT_PATH
    fi
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" && ! "$(ls -A $MINIO_MOUNT_PATH)" ]]; then
        echo "Mounting Minio Bucket $MINIO_BUCKET to $MINIO_MOUNT_PATH"
        mkdir -p $MINIO_MOUNT_PATH
        sudo juicefs mount -d -o allow_other,writeback_cache redis://127.0.0.1:6379/2 $MINIO_MOUNT_PATH
    fi
}

install_prereqs
install_juicefs
start_redis
format_juicefs
mount_storagefs

