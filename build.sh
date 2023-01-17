#!/bin/bash

docker buildx build --platform linux/amd64 --load -t cadquery-server-api .