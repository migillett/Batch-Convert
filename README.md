# Batch Convert
 A Docker container using [Python3](https://www.python.org/downloads/) and [ffmpeg](https://ffmpeg.org/download.html) to create a watch folder to convert media files to M4V. This script uses the python library [schedule](https://schedule.readthedocs.io/en/stable/index.html) to scan a folder every x minutes for new files.

## Running Locally
Make sure you install [Docker Compose](https://docs.docker.com/compose/install/) in order to run this container. Before starting the container, make sure to modify the `docker-compose.yml` file to meet your requirements. Here's an example:

```
version: "3"
services:
  batch_convert:
    container_name: batch_convert
    build: .
    environment:
      - PUID=1000 # use whatever user you need
      - PGID=1000 # use whatever group you need
      - SOURCE_FILE_CLEANUP='true'
      - FILETYPES="mkv,mov,mp4" # must be a string of file types split by commas and no spaces
      - RUN_EVERY="10" # how often to run the scan in minutes
    volumes:
      - /path/to/source/directory:/app/source:rw # the source files you want to convert
      - /path/to/destination/directory:/app/export:rw # where you want to save the ocnverted files to
    
```
