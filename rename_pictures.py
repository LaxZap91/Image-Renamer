import argparse
from os import rename, walk, sep
from os.path import getctime, join
from datetime import datetime

from PIL import Image, ExifTags
from pillow_heif import HeifImagePlugin

SUPPORTED_EXTENSIONS = (*tuple(Image.registered_extensions()), ".heic")


def get_time(path, include_creation_type, formating):
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
            ).strftime(formating)
            return date_obj
        except (KeyError, AttributeError):
            try:
                image_exif = image.getexif()
                date_obj = datetime.strptime(
                    image_exif[306], r"%Y:%m:%d %H:%M:%S"
                ).strftime(formating)
                return date_obj
            except KeyError:
                if include_creation_type:
                    date_obj = datetime.fromtimestamp(getctime(path)).strftime(
                        formating
                    )
                    return date_obj
                return None


# def rename_files(source_folders, include_creation_type, recursion, formating):
#     for folder in source_folders:
#         for file_name in listdir(folder):
#             if isfile(join(folder, file_name)) and (
#                 file_name.lower().endswith(SUPPORTED_EXTENSIONS)
#             ):
#                 file_time = get_time(
#                     join(folder, file_name), include_creation_type, formating
#                 )
#                 if file_time:
#                     new_file_name = f"{file_time}-{file_name}"
#                 else:
#                     new_file_name = file_name
#                 rename(join(folder, file_name), join(folder, new_file_name))
#             elif isdir(join(folder, file_name)) and recursion != 0:
#                 rename_files(
#                     (join(folder, file_name),), include_creation_type, recursion - 1
#                 )


def rename_files(source_folders, include_creation_type, recursion, formating):
    for folder in source_folders:
        for dirpath, _, files in walk(folder):
            if recursion == -1 or dirpath[len(folder) :].count(sep) <= recursion:
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        file_time = get_time(
                            join(dirpath, file_name), include_creation_type, formating
                        )
                        if file_time:
                            new_file_name = f"{file_time}-{file_name}"
                            rename(
                                join(dirpath, file_name), join(dirpath, new_file_name)
                            )


def undo_rename_files(source_folders, recursion, formating):
    for folder in source_folders:
        for dirpath, _, files in walk(folder):
            if recursion == -1 or dirpath[len(folder) :].count(sep) <= recursion:
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        file_time = get_time(join(dirpath, file_name), True, formating)
                        if file_name.startswith(file_time):
                            new_file_name = file_name.replace(f"{file_time}-", "")
                            rename(
                                join(dirpath, file_name), join(dirpath, new_file_name)
                            )


def validate_recursion_value(value: str):
    try:
        value = int(value)
        if value >= -1 and value != 0:
            return value
    except Exception as E:
        raise argparse.ArgumentTypeError(f"invalid recursion value: {E}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renames image files in given folders")
    parser.add_argument(
        "folder_paths", nargs="+", help="paths to the folders of images to be renamed"
    )
    parser.add_argument(
        "-ct",
        "--creation_time",
        action="store_true",
        required=False,
        help="use file creation time if date taken is not used",
    )
    parser.add_argument(
        "-r",
        "--recursion",
        required=False,
        nargs="?",
        default=0,
        const=-1,
        type=validate_recursion_value,
        help="whether to use recursion and how many layers deep (default: %(default)s) (const: infinite)",
    )
    parser.add_argument(
        "-f",
        "--format",
        required=False,
        default="%Y-%m-%d-%H-%M-%S",
        help="the way the time is formated as (default: %(default)s)",
    )
    parser.add_argument(
        "-u",
        "--undo",
        action="store_true",
        required=False,
        help="undos the renaming (use the same format)",
    )
    args = parser.parse_args()

    if not args.undo:
        rename_files(args.folder_paths, args.creation_time, args.recursion, args.format)
    else:
        undo_rename_files(args.folder_paths, args.recursion, args.format)
