import re
import shutil
from argparse import ArgumentParser, Action
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator


YEAR_REGEX = re.compile(r"(20\d\d)")


@dataclass
class Options:
    directory: Path
    dry_run: bool = field(default=True)


@dataclass
class MisplacedFile:
    original_path: Path
    year_from_filename: str


def parse_options() -> Options:
    parser = ArgumentParser()
    parser.add_argument(
        "directory", help="Directory where files with date tags are stored", type=Path
    )
    parser.add_argument("--no-dry-run", action="store_true")
    args = parser.parse_args()
    return Options(directory=args.directory, dry_run=not args.no_dry_run)


def misplaced_files_in_directory(path: Path) -> Generator[MisplacedFile, None, None]:
    assert path.is_dir()
    print(f"Checking folder {path}")

    folder_match = re.findall(YEAR_REGEX, path.name)
    if not folder_match:
        return
    folder_year = folder_match[0]
    print(f"Source folder has the year {folder_year}")

    for child in path.iterdir():
        if child.is_dir():
            print(f"Unknown directory {child} under {path}")
            continue

        filename = child.name
        file_matches = [
            match
            for match in re.findall(YEAR_REGEX, filename)
            if int(match) in range(2014, 2025)
        ]
        if not file_matches:
            continue

        if len(file_matches) > 1:
            print(f"Found multiple year matches for file {filename}")
            continue

        if file_matches[0] != folder_year:
            yield MisplacedFile(original_path=child, year_from_filename=file_matches[0])


def main() -> None:
    options = parse_options()

    dirs_by_year = {
        re.findall(YEAR_REGEX, dir_path.name)[0]: dir_path
        for dir_path in options.directory.iterdir()
    }

    for child in options.directory.iterdir():
        if not child.is_dir():
            continue

        for misplaced_file in misplaced_files_in_directory(child):
            if options.dry_run:
                print(f"Moving file {misplaced_file.original_path.name} from {misplaced_file.original_path.parent} to {dirs_by_year[misplaced_file.year_from_filename]}")
            else:
                new_path = dirs_by_year[misplaced_file.year_from_filename] / misplaced_file.original_path.name
                shutil.move(misplaced_file.original_path, new_path)