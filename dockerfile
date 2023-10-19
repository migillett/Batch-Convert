# For more information, please refer to https://aka.ms/vscode-docker-python

FROM python:3.11-slim-bullseye

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update
RUN apt-get install ffmpeg -y

# Copy over local files to docker image
COPY . .

CMD [ "python3", "batch_convert.py" ]
