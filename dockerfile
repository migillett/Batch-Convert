# For more information, please refer to https://aka.ms/vscode-docker-python

FROM python:3.11-slim-bullseye

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update
RUN apt-get install ffmpeg -y

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Copy over local files to docker image
COPY . .

CMD [ "python3", "batch_convert.py" ]
