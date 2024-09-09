"""
Renames images and videos to timestamp (ex: 20210511_123456.png)
"""

import os
import logging
from datetime import datetime
import exiftool

multimediaFormats = ["png", "jpg", "jpeg", "m4v", "mov", "mp4"]


def files_are_identical(file1_path, file2_path) -> bool:
    """
    Check if two files are identical.

    Args:
        file1_path (str): The path to the first file.
        file2_path (str): The path to the second file.

    Returns:
        bool: True if the files are identical, False otherwise.
    """
    with (
        open(file1_path, "rb") as file1,
        open(file2_path, "rb") as file2,
    ):
        return file1.read() == file2.read()


def change_filename_until_success(old_filename: str, new_filename: str) -> None:
    """
    Renames a file until a successful rename is achieved.

    Args:
        old_filename (str): The path to the file to be renamed.
        new_filename (str): The desired new name for the file.

    Returns:
        None: This function does not return anything.

    This function attempts to rename a file until a successful rename is achieved.
    If the new filename already exists, it appends a number to the filename until a unique filename is found.
    If the new filename is the same as the old filename, the old file is removed.
    If the new filename is successfully renamed, the function prints the new filename.

    Example:
        >>> change_filename_until_success("old.txt", "new.txt")
        Didn't rename old.txt: new filename is the same. Old file will be removed.
        >>> change_filename_until_success("old.txt", "new (1).txt")
        New filename: new (1).txt
    """
    i = 1
    while True:
        if i != 1:
            new_filename = (
                "."
                + new_filename.split(".")[-2]
                + " ("
                + str(i)
                + ")."
                + new_filename.split(".")[-1]
            )

        if os.path.exists(new_filename):
            if files_are_identical(old_filename, new_filename):
                logging.info(
                    "Didn't rename %s: new filename is the same. Old file will be removed.",
                    old_filename,
                )
                os.remove(old_filename)
            else:
                i += 1
        else:
            if os.path.exists(old_filename):
                os.rename(old_filename, new_filename)
                logging.info("New filename: %s", new_filename)
            else:
                logging.info("Didn't rename %s: old file does not exist", old_filename)
            break


def list_files(startpath) -> list:
    """
    Recursively lists all the files in a given directory and its subdirectories.

    Args:
        startpath (str): The path to the directory to start listing files from.

    Returns:
        None
    """
    file_list = []
    for root, _, files in os.walk(startpath):
        for file in files:
            if file.split(".")[-1].lower() in multimediaFormats:
                file_list.append(os.path.join(root, file))

    return file_list


def find_files_with_datetimeoriginal_metadata(paths) -> tuple:
    """
    Finds files with 'EXIF:DateTimeOriginal' metadata.

    Args:
        paths (List[str]): A list of file paths to search for metadata.

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: A tuple containing two lists.
            The first list contains dictionaries of files with 'EXIF:DateTimeOriginal' metadata.
            The second list contains dictionaries of files without 'EXIF:DateTimeOriginal' metadata.
    """
    valid_files = []
    invalid_files = []

    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(paths)
        for data in metadata:
            if (
                "EXIF:DateTimeOriginal" in data
                and data["EXIF:DateTimeOriginal"] != "0000:00:00 00:00:00"
            ):
                valid_files.append(data)
            else:
                invalid_files.append(data)

    return valid_files, invalid_files


def rename_file_if_any_date_metadata_exists(
    file, file_modify_date, file_create_date
) -> None:
    """
    Renames a file if it has any date metadata. The function takes in three parameters:

    - file (dict): A dictionary containing metadata about the file.
    - file_modify_date (str or None): The modification date of the file.
    - file_create_date (str or None): The creation date of the file.

    If both file_modify_date and file_create_date are not None,
    the function prompts the user to choose a new filename based on the modification date or creation date.

    If only file_modify_date is not None, the function renames the file using the modification date.

    If only file_create_date is not None, the function renames the file using the creation date.

    If neither file_modify_date nor file_create_date are not None,
    the function prints a message indicating that the file does not contain useful date metadata.

    This function does not return anything.
    """
    if file_modify_date is not None and file_create_date is not None:
        modify_datetime = get_datetime(file_modify_date)
        create_datetime = get_datetime(file_create_date)

        logging.info("Old filename: %s", file["SourceFile"])
        logging.info("Modify date: %s", file_modify_date)
        logging.info("Creation date: %s", file_create_date)

        while True:
            option = input("Choose new filename - [O] Old, [M] Modify, [C] Creation: ")
            match option.upper():
                case "M":
                    rename_file_if_necessary(
                        file["SourceFile"], get_new_filename(file, modify_datetime)
                    )
                    break
                case "C":
                    rename_file_if_necessary(
                        file["SourceFile"], get_new_filename(file, create_datetime)
                    )
                    break
                case "O":
                    logging.info(
                        "Didn't rename %s because of user choice", file["SourceFile"]
                    )
                    break
                case _:
                    logging.info("Wrong option. Try again")

    elif file_modify_date is not None:
        rename_file_if_necessary(
            file["SourceFile"], get_new_filename(file, modify_datetime)
        )
    elif file_create_date is not None:
        rename_file_if_necessary(
            file["SourceFile"], get_new_filename(file, create_datetime)
        )
    else:
        logging.info(
            "File: %s doesn't contain useful date metadata", file["SourceFile"]
        )


def cut_out_time_zone(date_string: str) -> str:
    """
    Given a date string, this function removes the timezone information from the string and returns the modified string.

    :param date_string: A string representing a date in the format "YYYY:MM:DD HH:MM:SS+HH:MM".
    :type date_string: str
    :return: A string representing the date without the timezone information.
    :rtype: str
    """
    return date_string.split("+", 1)[0]


def get_datetime(date_string: str) -> datetime:
    """
    Converts a string representation of a date and time into a `datetime` object.

    Args:
        date_string (str): A string representing the date and time in the format "YYYY:MM:DD HH:MM:SS".

    Returns:
        datetime: A `datetime` object representing the given date and time.
    """
    return datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")


def get_filename_from_datetime(dt) -> None:
    """
    Returns a string representing the filename generated from the given datetime object.

    Args:
        dt (datetime): The datetime object to generate the filename from.

    Returns:
        str: The generated filename in the format "YYYYMMDD_HHMMSS".
    """
    return dt.strftime("%Y%m%d_%H%M%S")


def get_new_filename(file, dt) -> str:
    """
    Generates a new filename by replacing the original filename with a timestamp.

    Args:
        file (dict): A dictionary containing metadata about the file, including the original filename.
        dt (datetime): The datetime object representing the timestamp to be used in the new filename.

    Returns:
        str: The new filename with the timestamp appended to the original filename.
    """
    return (
        os.path.dirname(file["SourceFile"])
        + "/"
        + get_filename_from_datetime(dt)
        + "."
        + file["SourceFile"].split(".")[-1].lower()
    )


def rename_file_if_necessary(old_filename: str, new_filename: str) -> None:
    """
    Renames a file if the new filename is different from the old filename.

    Args:
        old_filename (str): The path to the old file.
        new_filename (str): The desired new name for the file.

    Returns:
        None: This function does not return anything.
        It prints a message indicating whether the file was renamed or not.
    """
    if old_filename == new_filename:
        logging.info("Didn't rename %s: new filename is the same", old_filename)
    else:
        change_filename_until_success(old_filename, new_filename)
    logging.info("")


def main() -> None:
    """
    Runs the main function of the program.

    This function lists all the files in the 'images' directory and separates them into two lists:
    'valid_files' and 'invalid_files'. 'valid_files' contains files that have 'EXIF:DateTimeOriginal'
    metadata, while 'invalid_files' contains files that do not have this metadata.

    For each file in 'valid_files', the function generates a new filename by replacing the original filename
    with a timestamp derived from the 'EXIF:DateTimeOriginal' metadata. It then prints the old filename and
    the original image date, and renames the file if the new filename is different from the old filename.

    For each file in 'invalid_files', the function tries to find a new filename based on the 'File:FileModifyDate'
    and 'File:FileCreateDate' metadata. If both metadata are present, the user is prompted to choose a new filename
    based on the modification date or creation date. If only one of the metadata is present, the function renames the
    file using the corresponding date. If neither metadata is present, the function prints a message indicating that
    the file does not contain useful date metadata.

    This function does not return anything. It prints messages indicating the progress of the renaming process.
    """
    # configure logging
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file = f"log_{timestamp}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_file,
        filemode="a",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # start script work
    old_paths = list_files(r".\images")
    valid_files, invalid_files = find_files_with_datetimeoriginal_metadata(old_paths)

    # Rename files that contain valid metadata
    logging.info("Good files:")
    for file in valid_files:
        old_filename = file["SourceFile"]
        try:
            new_filename = get_new_filename(
                file, get_datetime(file["EXIF:DateTimeOriginal"])
            )
        except ValueError:
            print()

        logging.info("Old filename: %s", old_filename)
        logging.info("Original image date: %s", file["EXIF:DateTimeOriginal"])
        rename_file_if_necessary(old_filename, new_filename)

    logging.info("Error files:")
    for file in invalid_files:
        file_modify_date = (
            cut_out_time_zone(file["File:FileModifyDate"])
            if "File:FileModifyDate" in file
            else None
        )
        file_create_date = (
            cut_out_time_zone(file["File:FileCreateDate"])
            if "File:FileCreateDate" in file
            else None
        )

        rename_file_if_any_date_metadata_exists(
            file, file_modify_date, file_create_date
        )
        logging.info("")


if __name__ == "__main__":
    main()
