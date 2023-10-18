from os import path, listdir, remove, replace
import subprocess
import logging
from time import sleep
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a formatter to define the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler to log to a file
file_handler = logging.FileHandler('convert_jobs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create a console handler to log to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the log level for the console
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def main(check_interval=600):
    logger.info('===== Starting batch_convert.py =====')

    source_directory = '/app/source'
    export_directory = '/app/export'

    while True:

        media_to_convert = []

        report = f'Found the following MKV files found in {source_directory}:'

        logging.info(f'Searching for new MKV files in {source_directory}...')
        files = listdir(source_directory)
        for file in files:
            if file.endswith('.mkv'):
                media_to_convert.append(path.join(source_directory, file))
                report += f'\n  - {file}'

        if len(media_to_convert) == 0:
            logger.info(
                f'No MKV files detected in {source_directory}. Sleeping for {check_interval} seconds...')
            sleep(check_interval)
            continue

        logger.info(report)

        for file in media_to_convert:
            file_name = path.splitext(path.basename(file))[0]
            export_path = f"./{file_name}.m4v"

            ffmpeg_cmd = f'ffmpeg -y -i "{file}" -c:v libx264 -c:a aac -strict experimental -ac 2 -crf 20 "{export_path}"'
            logger.info(
                f'Converting {file} -> {export_path} with ffmpeg command: {ffmpeg_cmd}')

            t1 = datetime.now()

            cmd = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            _, err = cmd.communicate()
            if cmd.returncode != 0:
                logger.error(
                    f'ffmpeg conversion returned error code {cmd.returncode}: {err}')
                if path.exists(export_path):
                    logger.info(f'Deleting failed export file: {export_path}')
                    remove(export_path)
                continue

            copy_to = path.join(export_directory,
                                path.basename(export_path))
            logger.info(f'Moving completed export {export_path} to {copy_to}.')
            try:
                replace(export_path, copy_to)
            except PermissionError:
                logger.error(f'Unable to copy {export_path} to {copy_to}')
                exit(1)

            logger.info('File move complete.')

            logger.info(f'Attempting to delete source MKV file {file}')
            try:
                remove(file)
                logger.info(f'Deleted file {file} successfully.')
            except Exception as e:
                logger.error(f'Unable to delete file {file}: {e}')
                continue

            logger.info(
                f'Conversion complete for MKV file {path.basename(copy_to)} | Total process time: {datetime.now() - t1}')


if __name__ == "__main__":
    main()
