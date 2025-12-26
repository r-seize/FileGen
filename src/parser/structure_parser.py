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
        Extract paths from tree structure with proper hierarchy
        """
        paths           = []
        lines           = content.split('\n')
        stack           = []
        indent_map      = {}

        for line in lines:
            if not line.strip():
                continue

            original_line       = line
            tree_chars          = re.match(r'^([\s│├└─┬┴┼┤┌┐╭╮╰╯]+)', line)
            if tree_chars:
                tree_prefix     = tree_chars.group(1)
                clean           = line[len(tree_prefix):].strip()
                indent          = len(tree_prefix.replace('│', ' ').replace('├', ' ').replace('└', ' ').replace('─', ''))
            else:
                clean           = line.strip()
                indent          = len(line) - len(line.lstrip())

            if '#' in clean:
                clean = clean.split('#')[0].strip()

            if not clean or len(clean) > 200:
                continue

            if clean.startswith('//'):
                continue

            is_dir  = clean.endswith('/')
            name    = clean.rstrip('/')

            if any(char in name for char in ['<', '>', '|', '*', '?', '"', ',']):
                continue

            if indent not in indent_map:
                indent_map[indent] = len(indent_map)
            level = indent_map[indent]

            if level >= len(stack):
                stack.append(name)
            elif level < len(stack):
                stack = stack[:level]
                stack.append(name)
            else:
                stack[level] = name

            path = '/'.join(stack)
            if path and (path, is_dir) not in paths:
                paths.append((path, is_dir))

        return paths

    def _is_likely_file(self, name: str) -> bool:
        """
        Determine if a name is likely a file
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
    """
    parser = StructureParser()
    return parser.parse(content)


def print_tree_structure(structure: List[Dict], prefix: str = "", is_last: bool = True) -> None:
    """
    Print structure in tree format
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

    print_level('')