from os import path, listdir, remove, environ
from shutil import move
import subprocess
import logging
from time import sleep
from datetime import datetime
import schedule


source_directory = '/app/source'
export_directory = '/app/export'

watch_file_types = environ.get('FILETYPES', None)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a formatter to define the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler to log to a file
file_handler = logging.FileHandler(
    path.join(source_directory, 'convert_jobs.log'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create a console handler to log to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the log level for the console
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def extract_watch_file_types() -> list[str]:
    if watch_file_types is None:
        logging.error(
            'Unable to import environment variable FILETYPES. Exiting...')
        exit(1)

    watch_file_types = [w.lower() for w in watch_file_types.split(',')]

    if len(watch_file_types) == 0:
        logging.error('file type whitelist has no items. Exiting...')
        exit(1)

    return watch_file_types


def generate_convert_list(source_directory: str, file_types: list[str]) -> list[str]:
    media_to_convert = []

    report = f'Found the following MKV files found in {source_directory}:'

    logging.info(
        f'Searching for files in {source_directory} with extensions {file_types}...')
    files = listdir(source_directory)
    for file in files:
        if path.splittext(file)[-1] in file_types:
            media_to_convert.append(path.join(source_directory, file))
            report += f'\n  - {file}'

    logger.info(report)
    return media_to_convert


def convert_file(source_path: str, destination_path: str) -> bool:
    ffmpeg_cmd = f'ffmpeg -y -i "{source_path}" -c:v libx264 -c:a aac -strict experimental -ac 2 -crf 20 "{destination_path}"'

    logger.info(
        f'Converting {source_path} -> {destination_path} with ffmpeg command: {ffmpeg_cmd}')

    t1 = datetime.now()

    cmd = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, shell=True)
    _, err = cmd.communicate()
    if cmd.returncode != 0:
        logger.error(
            f'ffmpeg conversion returned error code {cmd.returncode}: {err}')
        if path.exists(destination_path):
            logger.info(f'Deleting failed export file: {destination_path}')
            remove(destination_path)
        return False

    else:
        logger.info(
            f'Encode complete. Total processing time for file {source_path}: {datetime.now() - t1}')
        return True


def move_export(file_path: str, move_to_directory: str) -> bool:
    new_path = path.join(
        move_to_directory, path.basename(file_path))

    logger.info(f'Moving completed export {file_path} to {new_path}.')

    try:
        move(file_path, new_path)
    except Exception as e:
        logger.error(f'Unable to move {file_path} to {new_path}: {e}')
        return False
    return True


def delete_source_file(source_file: str) -> None:
    try:
        remove(source_file)
        logger.info(f'Deleted file {source_file} successfully.')
    except Exception as e:
        logger.error(f'Unable to delete file {source_file}: {e}')


def main() -> None:
    enable_source_cleanup = environ.get(
        'SOURCE_FILE_CLEANUP', 'false').lower() == 'true'

    file_types = extract_watch_file_types()

    media_to_convert = generate_convert_list(
        source_directory=source_directory,
        file_types=file_types
    )

    if len(media_to_convert) == 0:
        logger.info(
            f'No files with extensions {file_types} detected in {source_directory}.')
        return

    for file in media_to_convert:
        file_name = path.splitext(path.basename(file))[0]
        export_path = f"./{file_name}.m4v"

        if not convert_file(file, export_path):
            continue

        # TODO - add in PSNR / SSIM file comparisons

        if not move_export(export_path, export_directory):
            exit(1)

        if enable_source_cleanup:
            delete_source_file(file)

        logger.info(
            f'Conversion complete for MKV file {path.basename(file)}')


if __name__ == "__main__":
    logger.info('===== Starting batch_convert.py =====')

    try:
        n = int(environ.get('EVERY_N_MINUTES', 10))
    except ValueError:
        logger.error(
            f'unable to convert {environ.get("EVERY_N_MINUTES")} to an integer')
        exit(1)

    logger.info(
        f'Program params:\n  Scan interval: every {n} minutes\n  File formats: {watch_file_types}')

    schedule.every(n).minutes.do(main)
    while True:
        schedule.run_pending()
        sleep(1)
