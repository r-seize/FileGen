"""
File and folder generator
Physically creates the structure on the file system
"""
from pathlib import Path
from typing import List, Dict, Optional

from src.utils.exceptions import GenerationError
from src.utils.logger import Logger


class FileGenerator:
    """Generates files and folders from a structure"""

    def __init__(
        self,
        output_dir: Path,
        force: bool                 = False,
        logger: Optional[Logger]    = None
    ):
        """
        Args:
            output_dir: Destination directory
            force: Overwrite existing files
            logger: Logger for messages
        """
        self.output_dir     = output_dir
        self.force          = force
        self.logger         = logger or Logger()

        self.stats = {
            'directories_created': 0,
            'files_created': 0,
            'files_skipped': 0,
            'errors': []
        }

    def generate(self, structure: List[Dict]) -> Dict:
        """
        Generates all files and folders

        Args:
            structure: Structure to generate

        Returns:
            Dictionary containing statistics
        """

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise GenerationError(f"Unable to create output directory: {e}")

        for item in structure:
            if item['type'] == 'directory':
                self._create_directory(item)

        for item in structure:
            if item['type'] == 'file':
                self._create_file(item)

        return self.stats

    def _create_directory(self, item: Dict) -> None:
        """Creates a directory"""
        dir_path = self.output_dir / item['path']

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.stats['directories_created'] += 1
            self.logger.debug(f"  [DIR] {item['path']}")
        except Exception as e:
            error_msg = f"Failed to create directory {item['path']}: {e}"
            self.stats['errors'].append(error_msg)
            self.logger.error(f"  [ERROR] {error_msg}")

    def _create_file(self, item: Dict) -> None:
        """Creates a file with its content"""
        file_path = self.output_dir / item['path']

        if file_path.exists() and not self.force:
            self.stats['files_skipped'] += 1
            self.logger.warning(f"  [SKIP] {item['path']} (already exists)")
            return

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(item.get('content', ''))

            self.stats['files_created'] += 1
            self.logger.debug(f"  [FILE] {item['path']}")
        except Exception as e:
            error_msg = f"Failed to create file {item['path']}: {e}"
            self.stats['errors'].append(error_msg)
            self.logger.error(f"  [ERROR] {error_msg}")


class DirectoryManager:
    """Manages directory operations"""

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Ensures a directory exists"""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_empty(path: Path) -> bool:
        """Checks if a directory is empty"""
        return not any(path.iterdir())

    @staticmethod
    def get_subdirectories(path: Path) -> List[Path]:
        """Returns all subdirectories"""
        return [p for p in path.iterdir() if p.is_dir()]

    @staticmethod
    def get_files(path: Path, recursive: bool = False) -> List[Path]:
        """Returns all files"""
        if recursive:
            return [p for p in path.rglob('*') if p.is_file()]
        return [p for p in path.iterdir() if p.is_file()]
