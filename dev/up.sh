#!bin/bash
docker build . -t embyplus/embybot:latest
docker compose up && docker compose rm -f
