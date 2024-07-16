"""
Renames images and videos to timestamp (ex: 20210511_123456.png)
"""

import ffmpeg
import os
from PIL import Image

imgFormats = ["png", "jpg", "jpeg"]
videoFormats = ["m4v", "mov", "mp4"]


def date_img(path: str) -> str:
    return Image.open(path)._getexif()[36867]


def date_vid(path: str) -> str:
    return (
        ffmpeg.probe(path)["streams"][1]["tags"]["creation_time"]
        .replace("T", " ")
        .replace("-", ":")
        .split(".")[0]
    )


def endswith_one_of_extensions(file: str, extensions: list[str]) -> bool:
    for ext in extensions:
        if file.endswith(ext):
            return True
    return False


def timestamp_filename(timestamp: str, extension: str) -> str:
    return timestamp.replace(":", "").replace(" ", "_") + "." + extension


def change_name_until_success(old_filename: str, new_filename: str):
    print("Changing name from: " + old_filename + " to: " + new_filename)
    i = 1
    while True:
        try:
            if i == 1:
                os.rename(old_filename, new_filename)
                break
            else:
                os.rename(
                    old_filename,
                    new_filename.split(".")[0]
                    + " ("
                    + str(i)
                    + ")."
                    + new_filename.split(".")[1],
                )
                break
        except FileExistsError:
            i += 1


def main():
    for old_filename in os.listdir():
        if not old_filename.endswith(".py"):
            new_filename = ""
            extension = old_filename.split(".")[-1]
            if endswith_one_of_extensions(old_filename.lower(), videoFormats):
                # Working for Redmi Note 8 Pro, maybe other devices
                new_filename = timestamp_filename(date_vid(old_filename), extension)
            if endswith_one_of_extensions(old_filename.lower(), imgFormats):
                new_filename = timestamp_filename(date_img(old_filename), extension)
            change_name_until_success(old_filename, new_filename)


if __name__ == "__main__":
    main()
