"""
Structure parser
Parse raw tree structures directly
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from src.utils.exceptions import ParsingError


class StructureParser:
    """Parse raw tree structure strings"""

    # Common files without extensions
    EXTENSIONLESS_FILES = {
        'LICENSE', 'LICENCE', 'README', 'CHANGELOG', 'CONTRIBUTING',
        'AUTHORS', 'CREDITS', 'INSTALL', 'MANIFEST', 'NOTICE',
        'Dockerfile', 'Makefile', 'Procfile', 'Rakefile',
        'Gemfile', 'Podfile', 'Fastfile', 'Appfile',
        'CODEOWNERS', 'Vagrantfile', 'Brewfile'
    }

    def __init__(self):
        self.seen_files = set()
        self.seen_dirs = set()

    def parse(self, content: str) -> List[Dict]:
        """
        Parse raw tree structure

        Args:
            content: Raw tree structure string

        Returns:
            List of dictionaries representing the structure

        Raises:
            ParsingError: If parsing fails
        """
        self.seen_files = set()
        self.seen_dirs = set()

        if not content.strip():
            raise ParsingError("Content is empty")

        if '\n' not in content and Path(content).exists():
            try:
                with open(content, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise ParsingError(f"Unable to read file: {e}")

        paths = self._extract_from_tree(content)

        if not paths:
            raise ParsingError("No valid structure found in content")

        structure = self._build_structure(paths)

        if not structure:
            raise ParsingError("Unable to build structure from paths")

        return structure

    def _extract_from_tree(self, content: str) -> List[Tuple[str, bool]]:
        """
        Extract paths from tree structure

        Args:
            content: Tree structure content

        Returns:
            List of tuples (path, is_directory)
        """
        paths                   = []
        lines                   = content.split('\n')
        current_path            = []
        prev_indent             = 0
        in_code_block           = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue

            if not stripped:
                continue

            clean_line          = re.sub(r'^[\s│├└─┬┴┼┤├┌┐└┘╭╮╰╯]+', '', line)
            indent              = len(line) - len(line.lstrip())
            name                = clean_line.strip()

            if not name or len(name) > 200:
                continue

            if name.startswith('#') or name.startswith('//'):
                continue

            is_dir              = name.endswith('/')
            name                = name.rstrip('/')

            if any(char in name for char in ['<', '>', '|', '*', '?', '"']):
                continue

            if indent > prev_indent:
                current_path.append(name)
            elif indent == prev_indent:
                if current_path:
                    current_path[-1] = name
                else:
                    current_path.append(name)
            else:
                indent_diff = prev_indent - indent
                levels_back = max(1, indent_diff // 2)

                if levels_back >= len(current_path):
                    current_path = [name]
                else:
                    current_path = current_path[:-levels_back]
                    current_path.append(name)

            if is_dir:
                path = '/'.join(current_path)
                paths.append((path, True))
            else:
                if self._is_likely_file(name):
                    path = '/'.join(current_path)
                    paths.append((path, False))

            prev_indent = indent

        return paths

    def _is_likely_file(self, name: str) -> bool:
        """
        Determine if a name is likely a file

        Args:
            name: Item name

        Returns:
            True if it's likely a file
        """
        if '.' in name:
            return True

        if name.upper() in [f.upper() for f in self.EXTENSIONLESS_FILES]:
            return True

        if name.startswith('.'):
            return True

        if name.endswith('.sh') or name.endswith('.bat'):
            return True

        return False

    def _build_structure(self, paths: List[Tuple[str, bool]]) -> List[Dict]:
        """
        Build structure from paths

        Args:
            paths: List of (path, is_directory) tuples

        Returns:
            Structure as list of dictionaries
        """
        structure = []

        for path, is_dir in paths:
            if path in self.seen_files or path in self.seen_dirs:
                continue

            parts = path.split('/')

            if len(parts) > 1:
                for i in range(len(parts) - 1):
                    dir_path = '/'.join(parts[:i+1])
                    if dir_path not in self.seen_dirs:
                        self.seen_dirs.add(dir_path)
                        structure.append({
                            'type': 'directory',
                            'path': dir_path,
                            'name': parts[i]
                        })

            if is_dir:
                if path not in self.seen_dirs:
                    self.seen_dirs.add(path)
                    structure.append({
                        'type': 'directory',
                        'path': path,
                        'name': parts[-1]
                    })
            else:
                if path not in self.seen_files:
                    self.seen_files.add(path)
                    file_name = parts[-1]
                    directory = '/'.join(parts[:-1]) if len(parts) > 1 else '.'
                    structure.append({
                        'type': 'file',
                        'path': path,
                        'name': file_name,
                        'directory': directory,
                        'content': '',
                        'extension': self._get_extension(file_name)
                    })

        return structure

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """
        Extract file extension

        Args:
            file_name: Name of the file

        Returns:
            Extension or empty string
        """
        if file_name.startswith('.'):
            if file_name.count('.') > 1:
                return file_name[1:]
            return file_name[1:]

        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]

        return ''


def parse_raw_structure(content: str) -> List[Dict]:
    """
    Convenience function to parse raw structure

    Args:
        content: Raw tree structure string or file path

    Returns:
        Parsed structure

    Example:
        >>> structure = parse_raw_structure('''
        ... project/
        ... ├── src/
        ... │   ├── main.py
        ... │   └── utils.py
        ... └── README.md
        ... ''')
    """
    parser = StructureParser()
    return parser.parse(content)