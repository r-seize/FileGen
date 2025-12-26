"""
Markdown file parser
Extracts folder and file structure
"""
import re
from pathlib import Path
from typing import List, Dict, Optional

from src.utils.exceptions import ParsingError


class MarkdownParser:
    """Parse Markdown files to extract structure"""

    EXTENSIONLESS_FILES = {
        'LICENSE', 'LICENCE', 'README', 'CHANGELOG', 'CONTRIBUTING',
        'AUTHORS', 'CREDITS', 'INSTALL', 'MANIFEST', 'NOTICE',
        'Dockerfile', 'Makefile', 'Procfile', 'Rakefile',
        'Gemfile', 'Podfile', 'Fastfile', 'Appfile',
        'CODEOWNERS', 'Vagrantfile', 'Brewfile'
    }

    def __init__(self):
        self.current_directory: Optional[str]   = None
        self.structure: List[Dict]              = []

    def parse(self, file_path: Path) -> List[Dict]:
        """
        Parse a Markdown file and return the structure

        Args:
            file_path: Path to the Markdown file

        Returns:
            List of dictionaries representing the structure

        Raises:
            ParsingError: If parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ParsingError(f"Unable to read file: {e}")

        if not content.strip():
            raise ParsingError("Markdown file is empty")

        self._parse_content(content)

        if not self.structure:
            raise ParsingError("No structure found in the file")

        return self.structure

    def _parse_content(self, content: str) -> None:
        """Parse Markdown content"""
        lines   = content.split('\n')
        i       = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith('#'):
                level, title = self._parse_heading(line)

                if level == 1:
                    dir_name = title.strip()
                    if dir_name:
                        self.current_directory = dir_name
                        self._add_directory(dir_name)
                elif level == 2:
                    if not self.current_directory:
                        raise ParsingError(
                            f"File '{title}' defined before any directory (line {i+1})"
                        )

                    file_content_lines  = []
                    i                   += 1
                    in_code_block       = False

                    while i < len(lines) and not (lines[i].startswith('#') and not in_code_block):
                        line = lines[i]

                        if line.startswith('```'):
                            in_code_block = not in_code_block
                            i += 1
                            continue

                        file_content_lines.append(line)
                        i += 1

                    file_content = '\n'.join(file_content_lines).strip()
                    self._add_file(title.strip(), file_content)
                    continue

            i += 1

    def _parse_heading(self, line: str) -> tuple:
        """
        Parse a Markdown heading line

        Returns:
            (level, title)
        """
        match = re.match(r'^(#+)\s+(.+)$', line)
        if not match:
            return (0, "")

        level = len(match.group(1))
        title = match.group(2).strip()
        return (level, title)

    def _add_directory(self, dir_name: str) -> None:
        """Add directory to structure"""
        parts           = dir_name.split('/')
        current_path    = ""

        for part in parts:
            if current_path:
                current_path += "/" + part
            else:
                current_path = part

            if not any(
                item['type'] == 'directory' and item['path'] == current_path
                for item in self.structure
            ):
                self.structure.append({
                    'type': 'directory',
                    'path': current_path,
                    'name': part
                })

    def _add_file(self, file_name: str, content: str) -> None:
        """Add file to structure"""
        file_path = f"{self.current_directory}/{file_name}"

        self.structure.append({
            'type': 'file',
            'path': file_path,
            'name': file_name,
            'directory': self.current_directory,
            'content': content,
            'extension': self._get_extension(file_name)
        })

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """
        Extract file extension
        Enhanced to handle dotfiles and extensionless files
        """
        if file_name.startswith('.'):
            if file_name.count('.') > 1:
                return file_name[1:]
            elif file_name.count('.') == 1:
                return file_name[1:]

        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]
        return ''


def print_tree_structure(structure: List[Dict]) -> None:
    """
    Print structure in tree format

    Args:
        structure: List of structure items
    """
    tree = {}
    for item in structure:
        if item['type'] == 'directory':
            parent = '/'.join(item['path'].split('/')[:-1]) if '/' in item['path'] else ''
            if parent not in tree:
                tree[parent] = {'dirs': [], 'files': []}
            tree[parent]['dirs'].append(item)
        else:
            parent = item['directory'] if item['directory'] != '.' else ''
            if parent not in tree:
                tree[parent] = {'dirs': [], 'files': []}
            tree[parent]['files'].append(item)

    def print_level(path: str, prefix: str = ""):
        if path not in tree:
            return

        items = tree[path]['dirs'] + tree[path]['files']
        for i, item in enumerate(items):
            is_last_item    = (i == len(items) - 1)
            connector       = "└── " if is_last_item else "├── "

            if item['type'] == 'directory':
                print(f"{prefix}{connector}{item['name']}/")
                extension = "    " if is_last_item else "│   "
                print_level(item['path'], prefix + extension)
            else:
                print(f"{prefix}{connector}{item['name']}")

    if tree.get(''):
        print_level('')
    else:
        root_dirs = [item for item in structure if item['type'] == 'directory' and '/' not in item['path']]
        for root in root_dirs:
            print(f"{root['name']}/")
            print_level(root['path'], "")