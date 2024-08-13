import re
import shutil
from argparse import ArgumentParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from rich import print
from rich.prompt import Prompt
from rich.tree import Tree

YEAR_REGEX = re.compile(r"(20\d\d)")


@dataclass(frozen=True)
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

    folder_match = re.findall(YEAR_REGEX, path.name)
    if not folder_match:
        return
    folder_year = folder_match[0]

    for child in path.iterdir():
        if child.is_dir():
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
            file_year = Prompt.ask(f"Choose year for {filename}", choices=file_matches)
        else:
            file_year = file_matches[0]

        if file_year != folder_year:
            yield MisplacedFile(original_path=child, year_from_filename=file_year)


def main() -> None:
    options = parse_options()

    tree = Tree(options.directory.name)

    dirs_by_year = {
        re.findall(YEAR_REGEX, dir_path.name)[0]: dir_path
        for dir_path in options.directory.iterdir()
    }

    misplaced_files = []

    for child in options.directory.iterdir():
        if not child.is_dir():
            continue

        child_tree = tree.add(child.name)

        for misplaced_file in misplaced_files_in_directory(child):
            child_tree.add(misplaced_file.original_path.name)
            misplaced_files.append(misplaced_file)

    print("Possibly misplaced files")
    print(tree)

    if options.dry_run:
        print("Rerun with `--no-dry-run` to make the changes")
        return

    for misplaced_file in misplaced_files:
        new_path = dirs_by_year[misplaced_file.year_from_filename] / misplaced_file.original_path.name
        shutil.move(misplaced_file.original_path, new_path)
