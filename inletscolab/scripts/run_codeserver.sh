#!/bin/bash

BIND_ADDR=$1
CODE_PASSWORD=$2
CODE_BIND_ADDR=${BIND_ADDR:-127.0.0.1:7070}

if [[ ! -f /content/workspace.ipynb ]]; then
    touch /content/workspace.ipynb
fi

if [[ "$CODE_PASSWORD" != "" ]]; then
    PASSWORD="$CODE_PASSWORD" code-server --bind-addr="$CODE_BIND_ADDR" --disable-telemetry
else
    code-server --bind-addr="$CODE_BIND_ADDR" --auth=none --disable-telemetry
fi

