#!/bin/bash

ENVFILE=$1

SCRIPTS_DIR=$(dirname "$(realpath $0)")
ENV_FILE=${ENVFILE:-"$SCRIPTS_DIR/load_env.sh"}

echo "Loading Env from $ENV_FILE"
source "$ENV_FILE"


install_prereqs() {
    apt update && apt install -y curl fuse
}

install_gcsfuse() {
    if [[ "$(which gcsfuse)" == "" ]]; then
        export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
        echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
        curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
        sudo apt-get update && sudo apt-get install -y gcsfuse
    fi
}


mount_gcsfuse() {
    if [[ "$MOUNT_GS" == "True" && "$GS_BUCKET" != "" ]]; then
        if [[ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
            echo "No GOOGLE_APPLICATION_CREDENTIALS found at $GOOGLE_APPLICATION_CREDENTIALS. This may not work."
        fi
        mkdir -p "$GS_MOUNT_PATH"
        if [[ "$(ls -A $GS_MOUNT_PATH)" ]]; then
            echo "Another Bucket is already mounted at $GS_MOUNT_PATH"
        else
            echo "Mounting Google Storage Bucket $GS_BUCKET to $GS_MOUNT_PATH"
            gcsfuse "$GS_BUCKET" "$GS_MOUNT_PATH"
        fi
    fi
}


install_s3fs() {
    if [[ "$(which s3fs)" == "" ]]; then
        sudo apt-get update && sudo apt-get install -y s3fs
    fi
}

setup_s3fs_credentials() {
    echo "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY" > /etc/passwd-s3fs
    chmod 600 /etc/passwd-s3fs
}

mount_s3fs() {
    if [[ "$MOUNT_S3" == "True" && "$S3_BUCKET" != "" ]]; then
        setup_s3fs_credentials
        mkdir -p "$S3_MOUNT_PATH"
        if [[ "$(ls -A $S3_MOUNT_PATH)" ]]; then
            echo "S3 Bucket is already mounted at $S3_MOUNT_PATH"
        else
            echo "Mounting S3 Bucket $S3_BUCKET to $S3_MOUNT_PATH"
            s3fs "$S3_BUCKET" "$S3_MOUNT_PATH" -o passwd_file=/etc/passwd-s3fs
        fi
    fi

}

setup_miniofs_credentials() {
    echo "$MINIO_ACCESS_KEY:$MINIO_SECRET_KEY" > /etc/passwd-miniofs
    chmod 600 /etc/passwd-miniofs
}

mount_miniofs() {
    if [[ "$MOUNT_MINIO" == "True" && "$MINIO_BUCKET" != "" ]]; then
        setup_miniofs_credentials
        mkdir -p "$MINIO_MOUNT_PATH"
        if [[ "$(ls -A $MINIO_MOUNT_PATH)" ]]; then
            echo "Minio Bucket is already mounted at $MINIO_MOUNT_PATH"
        else
            echo "Mounting Minio Bucket $MINIO_BUCKET to $MINIO_MOUNT_PATH"
            s3fs "$MINIO_BUCKET" "$MINIO_MOUNT_PATH" -o passwd_file=/etc/passwd-miniofs -o url="$MINIO_ENDPOINT/" -o use_path_request_style
            
        fi
    fi

}

install_storage() {
    install_prereqs
    if [[ "$MOUNT_GS" == "True" ]]; then
        install_gcsfuse
    fi
    if [[ "$MOUNT_S3" == "True" || "$MOUNT_MINIO" == "True" ]]; then
        install_s3fs
    fi
}


mount_storage() {
    if [[ "$MOUNT_GS" == "True" ]]; then
        mount_gcsfuse
    fi
    if [[ "$MOUNT_S3" == "True" ]]; then
        mount_s3fs
    fi
    if [[ "$MOUNT_MINIO" == "True" ]]; then
        mount_miniofs
    fi
}


install_storage
mount_storage
