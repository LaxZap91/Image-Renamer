from sys import argv
from os import listdir, rename
from os.path import isfile, getctime, join
from datetime import datetime

from PIL import Image, ExifTags
from pillow_heif import register_heif_opener

register_heif_opener()

# source_folder = argv[1]
source_folder = r"E:\Code Projects\Python Projects\Image Renamer\imgs"


def get_time(path):
    with Image.open(path) as image:
        try:
            image_exif = image._getexif()
            exif = {
                ExifTags.TAGS[k]: v
                for k, v in image_exif.items()
                if k in ExifTags.TAGS and type(v) is not bytes
            }
            date_obj = datetime.strptime(
                exif["DateTimeOriginal"], r"%Y:%m:%d %H:%M:%S"
            ).strftime(r"%Y-%d-%m-%H-%M-%S")
            return date_obj
        except (KeyError, AttributeError):
            try:
                image_exif = image.getexif()
                date_obj = datetime.strptime(
                    image_exif[306], r"%Y:%m:%d %H:%M:%S"
                ).strftime(r"%Y-%d-%m-%H-%M-%S")
                return date_obj
            except KeyError:
                date_obj = datetime.fromtimestamp(getctime(path)).strftime(
                    r"%Y-%d-%m-%H-%M-%S"
                )
                return date_obj


for file_name in listdir(source_folder):
    if (
        file_name.upper().endswith(".HEIC")
        or file_name.upper().endswith(".JPEG")
        or file_name.upper().endswith(".JPG")
        or file_name.upper().endswith(".PNG")
    ) and isfile(join(source_folder, file_name)):
        file_time = get_time(join(source_folder, file_name))
        new_file_name = f"{file_time}-{file_name}"
        rename(join(source_folder, file_name), join(source_folder, new_file_name))
