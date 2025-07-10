#!/bin/bash
HOST=$1

curl -X POST https://dws.com.co/admin/remove_route \
    -H "Content-Type: application/json" \
    -d '{"host":$HOST".dws.com.co"}' \
    -k