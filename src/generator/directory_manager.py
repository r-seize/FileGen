"""
File Manager
Advanced directory operations
"""
from pathlib import Path
from typing import List, Optional
import shutil


class DirectoryManager:
    """Manages file operations"""

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """
        Ensures that a file exists

        Args:
            path: Folder path
        """
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_empty(path: Path) -> bool:
        """
        Check if a folder is empty

        Args:
            path: Folder path

        Returns:
            True if the folder is empty
        """
        if not path.exists() or not path.is_dir():
            return True
        return not any(path.iterdir())

    @staticmethod
    def get_subdirectories(path: Path, recursive: bool = False) -> List[Path]:
        """
        Returns all subfolders

        Args:
            path: Folder path parent
            recursive: Recursive search

        Returns:
            Liste des sous-dossiers
        """
        if not path.exists() or not path.is_dir():
            return []

        if recursive:
            return [p for p in path.rglob('*') if p.is_dir()]
        return [p for p in path.iterdir() if p.is_dir()]

    @staticmethod
    def get_files(path: Path, recursive: bool = False, pattern: str = '*') -> List[Path]:
        """
        Returns all files

        Args:
            path: Folder path
            recursive: Recursive search
            pattern: Pattern de recherche (ex: '*.py')

        Returns:
            List of files
        """
        if not path.exists() or not path.is_dir():
            return []

        if recursive:
            return [p for p in path.rglob(pattern) if p.is_file()]
        return [p for p in path.glob(pattern) if p.is_file()]

    @staticmethod
    def get_size(path: Path, recursive: bool = True) -> int:
        """
        Calculates the total size of a folder

        Args:
            path: Folder path
            recursive: Include subfolders

        Returns:
            Size in bytes
        """
        if not path.exists():
            return 0

        if path.is_file():
            return path.stat().st_size

        total = 0
        for item in path.iterdir():
            if item.is_file():
                total += item.stat().st_size
            elif item.is_dir() and recursive:
                total += DirectoryManager.get_size(item, recursive=True)

        return total

    @staticmethod
    def clean_directory(path: Path, keep_root: bool = True) -> None:
        """
        Cleans a folder (deletes all its contents)

        Args:
            path: Folder path
            keep_root: Keep the root folder
        """
        if not path.exists():
            return

        if keep_root:
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        else:
            shutil.rmtree(path)

    @staticmethod
    def copy_directory(src: Path, dst: Path, overwrite: bool = False) -> None:
        """
        Copy a folder

        Args:
            src: Source folder
            dst: Destination folder
            overwrite: Overwrite if exists
        """
        if dst.exists() and not overwrite:
            raise FileExistsError(f"The folder {dst} already exists")

        if dst.exists():
            shutil.rmtree(dst)

        shutil.copytree(src, dst)

    @staticmethod
    def create_structure(base_path: Path, structure: dict) -> None:
        """
        Creates a folder structure from a dictionary

        Args:
            base_path: Base path
            structure: Structure dictionary

        Example:
            structure = {
                'src': {
                    'utils': {},
                    'models': {}
                },
                'tests': {}
            }
        """
        for name, subdirs in structure.items():
            dir_path = base_path / name
            dir_path.mkdir(exist_ok=True)

            if isinstance(subdirs, dict) and subdirs:
                DirectoryManager.create_structure(dir_path, subdirs)