#!/bin/bash
HOST=$1
BACKEND=$2

curl -X POST https://dws.com.co/admin/add_route \
    -H "Content-Type: application/json" \
    -d '{"host":$HOST".dws.com.co", "backend":$BACKEND}' \
    -k