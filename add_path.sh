#!/bin/bash
curl -X POST https://dws.com.co/admin/add_route     -H "Content-Type: application/json"     -d '{
   "path": "/usuario1/",
   "backend": "http://192.168.2.19:8890"
     }'


