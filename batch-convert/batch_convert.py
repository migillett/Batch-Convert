from os import path, listdir, remove, environ
from shutil import move
import subprocess
import logging
from time import sleep
from datetime import datetime
import schedule

from utils.data_structures import InterlaceDetect


class BatchConverter:
    def __init__(self):
        self.source_directory = '/app/source'
        self.export_directory = '/app/export'

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self.export_format = environ.get('EXPORT_FORMAT', 'mkv')

        # Create a formatter to define the log message format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

        # Create a file handler to log to a file
        file_handler = logging.FileHandler(
            path.join(self.source_directory, 'convert_jobs.log'))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Create a console handler to log to the console
        console_handler = logging.StreamHandler()
        # Set the log level for the console
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info('===== Starting batch_convert.py =====')

        try:
            self.every_n_minutes = int(environ.get('RUN_EVERY', 10))
            self.logger.info(
                f'Scanning source directory every {self.every_n_minutes} minutes')
        except ValueError:
            self.logger.error(
                f'unable to convert {environ.get("RUN_EVERY")} to an integer')
            exit(1)

        self.media_to_convert = []

    def extract_watch_file_types(self) -> list[str]:
        file_types = environ.get('FILETYPES', None)
        if file_types is None:
            logging.error(
                'Unable to import environment variable FILETYPES. Exiting...')
            exit(1)
        return [w.lower() for w in file_types.split(',')]

    def generate_convert_list(self, watch_file_types: list[str]) -> list[str]:
        # returns a list of media files that match file types

        if len(watch_file_types) == 0:
            logging.error(
                'File type list has a length of 0. Unable to find any files with matching extensions.')
            exit(1)

        # reset media conversion list to empty
        convert_list = []

        report = f'Found the following MKV files found in {self.source_directory}:'

        files = listdir(self.source_directory)
        for file in files:
            if path.splitext(file)[-1].replace('.', '') in watch_file_types and not file.startswith('.'):
                convert_list.append(
                    path.join(self.source_directory, file))
                report += f'\n  - {file}'

        if len(convert_list) > 0:
            self.logger.info(report)

        return convert_list

    def check_interlaced(self, source_path: str, analyze_frames: int = 360) -> InterlaceDetect | None:
        response = None

        self.logger.info(f'Determining if file is interlaced: {source_path}')

        ffmpeg_cmd = f'ffmpeg -filter:v idet -frames:v {analyze_frames} -an -f rawvideo -y /dev/null -i {source_path}'

        cmd = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        _, err = cmd.communicate()

        if cmd.returncode != 0:
            self.logger.error(
                f'ffmpeg interlacing detection failed for {source_path}: {err}'
            )
            return

        for line in cmd.stdout:
            if 'Multi frame detection:' in line:
                try:
                    response = InterlaceDetect.from_string(line)
                except ValueError:
                    self.logger.error(
                        f'Unable to parse interlace ffmpeg interlace detection log: {line}')
                    continue

        return response

    def convert_file(self, source_path: str, destination_path: str) -> bool:
        filters = '-c:v libx264 -c:a aac -strict experimental -ac 2 -crf 20'

        interlace = self.check_interlaced(source_path=source_path)
        if interlace is not None:
            filters += ' -vf yadif=1'

        ffmpeg_cmd = f'ffmpeg -y -i "{source_path}" {filters} "{destination_path}"'

        self.logger.info(
            f'Converting {source_path} -> {destination_path} with ffmpeg command: {ffmpeg_cmd}')

        t1 = datetime.now()

        cmd = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
        _, err = cmd.communicate()

        if cmd.returncode != 0:
            self.logger.error(
                f'ffmpeg conversion returned error code {cmd.returncode}: {err}')
            if path.exists(destination_path):
                self.logger.info(
                    f'Deleting failed export file: {destination_path}')
                remove(destination_path)
            return False

        else:
            self.logger.info(
                f'Encode complete. Total processing time for file {source_path}: {datetime.now() - t1}')
            return True

    def move_export(self, file_path: str, move_to_directory: str) -> bool:
        new_path = path.join(
            move_to_directory, path.basename(file_path))

        self.logger.info(f'Moving completed export {file_path} to {new_path}.')

        try:
            move(file_path, new_path)
        except Exception as e:
            self.logger.error(f'Unable to move {file_path} to {new_path}: {e}')
            return False
        return True

    def delete_source_file(self, source_file: str) -> None:
        try:
            remove(source_file)
            self.logger.info(f'Deleted file {source_file} successfully.')
        except Exception as e:
            self.logger.error(f'Unable to delete file {source_file}: {e}')

    def run(self) -> None:
        enable_source_cleanup = environ.get(
            'SOURCE_FILE_CLEANUP', 'false').lower() == 'true'

        file_types = self.extract_watch_file_types()
        if len(file_types) == 0:
            logging.error('file type watch list has no items. Exiting...')
            exit(1)

        media_to_convert = self.generate_convert_list(file_types)
        if len(media_to_convert) == 0:
            return

        for file in media_to_convert:
            file_name = path.splitext(path.basename(file))[0]
            export_path = f"./{file_name}.{self.export_format}"

            if not self.convert_file(file, export_path):
                continue

            # TODO - add in PSNR / SSIM file comparisons

            if not self.move_export(export_path, self.export_directory):
                exit(1)

            if enable_source_cleanup:
                self.delete_source_file(file)

            self.logger.info(
                f'Conversion complete for MKV file {path.basename(file)}')

    def run_on_schedule(self) -> None:
        schedule.every(self.every_n_minutes).minutes.do(self.run)
        while True:
            schedule.run_pending()
            sleep(1)


if __name__ == "__main__":
    batchconvert = BatchConverter()
    batchconvert.run_on_schedule()
