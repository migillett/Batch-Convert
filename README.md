# Batch Convert
 A Docker container using [Python3](https://www.python.org/downloads/) and [ffmpeg](https://ffmpeg.org/download.html) to create a watch folder to convert media files to M4V. This script uses the python library [schedule](https://schedule.readthedocs.io/en/stable/index.html) to scan a folder every x minutes for new files.

## Running Locally
First, pull down this GitHub repository using `git clone https://github.com/migillett/Batch-Convert.git` and move into the directory.

Make sure you install [Docker Compose](https://docs.docker.com/compose/install/) to run this container. You'll want tomodify the `docker-compose.yml` file to meet your requirements. Here's an example:

```
version: "3"
services:
  batch_convert:
    container_name: batch_convert
    build: .
    environment:
      - PUID=1000 # use whatever user you need
      - PGID=1000 # use whatever group you need
      - SOURCE_FILE_CLEANUP=true
      - FILETYPES=mkv,mov,mp4 # must be a string of file types split by commas and no spaces
      - EXPORT_FORMAT=m4v
      - RUN_EVERY=10 # how often to run the scan in minutes
    volumes:
      - /path/to/source/directory:/app/source:rw # the source files you want to convert
      - /path/to/destination/directory:/app/export:rw # where you want to save the converted files to
    # OPTIONAL - set resource limits on the transcoding
    deploy:
      resources:
        limits:
          cpus: '3'
          memory: 8G
    
```

Then run `docker-compose up -d --force-recreate --build` to pull the base image, build, and run the container.

## Future Updates
I would like to add in a feature that scans the exported file and compares it using PSNR and/or SSIM analsis to make sure the source and export is the same.
