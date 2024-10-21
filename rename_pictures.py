import argparse
from os import rename, walk, sep
from os.path import getctime, isdir
from pathlib import Path
from datetime import datetime

from typing import Union, Final

from PIL import Image, ExifTags
from pillow_heif import HeifImagePlugin

SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (
    *tuple(Image.registered_extensions()),
    ".heic",
)


def get_time(
    path: Path, include_creation_type: bool, formatting: str
) -> Union[str, None]:
    with Image.open(path) as image:
        image_exif = image.getexif()

        try:
            image_date = datetime.strptime(
                image_exif.get(306), "%Y:%m:%d %H:%M:%S"
            ).strftime(formatting)
            return image_date
        except (KeyError, TypeError):
            pass

        try:
            image_date = datetime.strptime(
                image_exif.get(36867), "%Y:%m:%d %H:%M:%S"
            ).strftime(formatting)
            return image_date
        except (KeyError, TypeError):
            pass

        try:
            exif = {
                ExifTags.TAGS[k]: v
                for k, v in image_exif.items()
                if k in ExifTags.TAGS and type(v) is not bytes
            }
            image_date = datetime.strptime(
                exif["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S"
            ).strftime(formatting)
            return image_date
        except (KeyError, TypeError):
            pass

    if include_creation_type:
        image_date = datetime.fromtimestamp(getctime(path)).strftime(formatting)
        return image_date
    return None


def rename_files(
    source_folders: list[Path],
    include_creation_type: bool,
    recursion: int,
    formatting: str,
):

    for folder in source_folders:
        if not isdir(folder):
            print(f"Directory not found: '{folder}'")
            continue

        for dirpath, _, files in walk(folder):
            if recursion == -1 or dirpath[len(folder) :].count(sep) <= recursion:
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        file_path = Path(dirpath, file_name)
                        file_time = get_time(
                            file_path, include_creation_type, formatting
                        )

                        if file_time:
                            new_file_path = Path(dirpath, f"{file_time}-{file_name}")

                            try:
                                rename(file_path, new_file_path)
                            except PermissionError:
                                raise PermissionError(
                                    f"Permission denied: Unable to rename '{file_path}' due to file permission"
                                )
                            except FileExistsError:
                                raise FileExistsError(
                                    f"File already exists: '{new_file_path}' already exists"
                                )


def undo_rename_files(source_folders: list[Path], recursion: int, formatting: str):
    for folder in source_folders:
        if not isdir(folder):
            print(f"Directory not found: '{folder}'")

        for dirpath, _, files in walk(folder):
            if recursion == -1 or dirpath[len(folder) :].count(sep) <= recursion:
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        file_path = Path(dirpath, file_name)
                        file_time = get_time(file_path, True, formatting)

                        if file_name.startswith(file_time):
                            new_file_path = Path(
                                dirpath, file_name.replace(f"{file_time}-", "")
                            )

                            try:
                                rename(file_path, new_file_path)
                            except OSError as E:
                                print(E)


def validate_recursion_value(value: str) -> int:
    try:
        int(value)
    except ValueError as E:
        raise argparse.ArgumentTypeError(
            f"Invalid recursion value: '{value}' must be an integer"
        )

    value = int(value)
    if value >= -1:
        return value
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid recursion value: '{value}' must be greater than or equal to -1"
        )


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
        help="use file creation time if date taken does not exist",
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
        help="undoes the renaming (use the same format)",
    )
    args = parser.parse_args()

    if not args.undo:
        rename_files(args.folder_paths, args.creation_time, args.recursion, args.format)
    else:
        undo_rename_files(args.folder_paths, args.recursion, args.format)
