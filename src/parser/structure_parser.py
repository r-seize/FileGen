"""
Structure parser - Ultra-robust version
Parse raw tree structures with advanced error handling and flexibility
Handles: multiple trees, misaligned characters, various formats, shell errors
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

from src.utils.exceptions import ParsingError


class StructureParser:
    """Parse raw tree structure strings with maximum flexibility and error recovery"""

    EXTENSIONLESS_FILES = {
        'LICENSE', 'LICENCE', 'README', 'CHANGELOG', 'CONTRIBUTING',
        'AUTHORS', 'CREDITS', 'INSTALL', 'MANIFEST', 'NOTICE',
        'Dockerfile', 'Makefile', 'Procfile', 'Rakefile',
        'Gemfile', 'Podfile', 'Fastfile', 'Appfile',
        'CODEOWNERS', 'Vagrantfile', 'Brewfile'
    }

    TREE_CHARS = {
        '│', '├', '└', '─', '┬', '┴', '┼', '┤', '┌', '┐', '╭', '╮', '╰', '╯',
        '|', '+', '-', '`', '\'', '\\', '/', '~', '·', '•'
    }

    INVALID_PATH_CHARS          = {'<', '>', '|', '*', '?', '"', '\0'}
    MAX_PATH_LENGTH             = 250
    MAX_FILENAME_LENGTH         = 255
    MAX_DEPTH                   = 100

    def __init__(self):
        self.seen_files         = set()
        self.seen_dirs          = set()
        self.warnings           = []
        self.current_tree       = []
        self.trees              = []

    def parse(self, content: str) -> List[Dict]:
        """
        Parse raw tree structure with maximum flexibility

        Args:
            content: Raw tree structure string (can contain multiple trees)

        Returns:
            List of dictionaries representing the structure

        Raises:
            ParsingError: If parsing fails completely
        """
        self.seen_files         = set()
        self.seen_dirs          = set()
        self.warnings           = []
        self.trees              = []

        if not content.strip():
            raise ParsingError("Content is empty")

        if '\n' not in content and Path(content).exists():
            try:
                with open(content, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise ParsingError(f"Unable to read file: {e}")

        content         = self._deep_clean_content(content)
        all_paths       = self._extract_all_trees(content)

        if not all_paths:
            raise ParsingError("No valid structure found in content")

        structure = self._build_unified_structure(all_paths)

        if not structure:
            raise ParsingError("Unable to build structure from paths")

        return structure

    def _deep_clean_content(self, content: str) -> str:
        """
        Deep clean content - remove shell errors, normalize encoding, fix alignment
        """
        lines = []
        
        for line in content.split('\n'):
            if not line.strip():
                lines.append('')
                continue

            if self._is_shell_error_or_command(line):
                continue

            cleaned = ''
            for char in line:
                if char.isprintable() or char in '\t ':
                    cleaned += char
                elif char in self.TREE_CHARS:
                    cleaned += char

            cleaned = cleaned.replace('\t', '    ')
            cleaned = cleaned.rstrip()

            if cleaned.strip():
                lines.append(cleaned)

        return '\n'.join(lines)

    def _is_shell_error_or_command(self, line: str) -> bool:
        """
        Detect shell errors, command outputs, and invalid lines
        """
        stripped = line.strip()

        if not stripped:
            return False

        error_patterns = [
            'command not found',
            ': not found',
            'No such file',
            'syntax error',
            'permission denied',
            'cannot access',
            'bash:',
            'zsh:',
            'sh:',
            'fish:',
        ]
        
        for pattern in error_patterns:
            if pattern.lower() in stripped.lower():
                return True

        if re.match(r'^[│├└─┬┴┼┤┌┐╭╮╰╯|+\-`\s]+:\s*$', stripped):
            return True

        if re.search(r'\^[A-Z]', stripped):
            return True

        if '\x1b[' in line or '\033[' in line:
            return True

        return False

    def _extract_all_trees(self, content: str) -> List[Tuple[str, bool]]:
        """
        Extract paths from content - handles multiple tree structures with accurate depth tracking
        """
        all_paths           = []
        lines               = content.split('\n')
        path_stack          = []
        depth_stack         = []

        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1

            if not line.strip():
                continue

            result = self._smart_parse_line(line)

            if result is None:
                continue

            name, depth, is_dir, has_tree_chars = result

            if depth == 0 and not has_tree_chars:
                path_stack      = [name]
                depth_stack     = [0]
                all_paths.append((name, True))
                continue

            if not path_stack:
                path_stack      = [name]
                depth_stack     = [0]
                all_paths.append((name, True))
                continue

            while depth_stack and depth <= depth_stack[-1]:
                path_stack.pop()
                depth_stack.pop()

            path_stack.append(name)
            depth_stack.append(depth)

            full_path = '/'.join(path_stack)

            if len(path_stack) > self.MAX_DEPTH:
                self.warnings.append(f"Path too deep (>{self.MAX_DEPTH}): {full_path} - skipped")
                path_stack.pop()
                depth_stack.pop()
                continue

            if len(full_path) > self.MAX_PATH_LENGTH:
                self.warnings.append(f"Path too long (>{self.MAX_PATH_LENGTH}): {full_path} - skipped")
                path_stack.pop()
                depth_stack.pop()
                continue

            if (full_path, is_dir) not in all_paths:
                all_paths.append((full_path, is_dir))

        return all_paths

    def _smart_parse_line(self, line: str) -> Optional[Tuple[str, int, bool, bool]]:
        """
        Intelligently parse a line - handles various formats and misalignments
        Returns: (name, depth, is_dir, has_tree_chars)
        """
        if not line.strip():
            return None

        tree_prefix, content, depth, has_tree_chars = self._extract_tree_components(line)

        if content is None:
            return None

        content = content.strip()

        if '#' in content and not content.startswith('#'):
            content = content.split('#')[0].strip()

        is_dir  = content.endswith('/')
        name    = content.rstrip('/')

        if not self._is_valid_name(name):
            return None

        if len(name) > self.MAX_FILENAME_LENGTH:
            self.warnings.append(f"Filename too long: {name[:50]}... - skipped")
            return None

        if not is_dir and not self._is_likely_file(name):
            is_dir = True

        return name, depth, is_dir, has_tree_chars

    def _extract_tree_components(self, line: str) -> Tuple[str, Optional[str], int, bool]:
        """
        Extract tree drawing characters, content, and calculate depth level
        Returns: (tree_prefix, content, depth, has_tree_chars)
        
        Depth calculation strategy:
        - Count vertical bars (│) which indicate parent levels
        - Connectors (├ └) indicate current item depth
        """
        if not line:
            return '', None, 0, False

        leading_spaces      = len(line) - len(line.lstrip(' \t'))
        stripped            = line.lstrip(' \t')
        tree_char_end       = 0
        has_tree_chars      = False

        for i, char in enumerate(stripped):
            if char in self.TREE_CHARS:
                has_tree_chars = True
                tree_char_end = i + 1
            elif char in ' \t' and has_tree_chars:
                tree_char_end = i + 1
            else:
                break

        tree_prefix     = stripped[:tree_char_end]
        content         = stripped[tree_char_end:].strip()
        depth           = 0

        if has_tree_chars:
            vertical_bars = tree_prefix.count('│') + tree_prefix.count('|')
            has_connector = any(char in tree_prefix for char in ['├', '└', '─'])

            if vertical_bars > 0:
                depth = vertical_bars + (1 if has_connector else 0)
            elif has_connector:
                depth = 1
            else:
                depth = max(0, leading_spaces // 4)
        else:
            depth = 0

        return tree_prefix, content, depth, has_tree_chars

    def _smart_calculate_levels(self, last_indent: int, current_indent: int) -> int:
        """
        Calculate level difference with flexibility for misalignment
        """
        if current_indent >= last_indent:
            return 0

        indent_diff = last_indent - current_indent
        
        if indent_diff < 3:
            return 1
        elif indent_diff < 7:
            return 2
        elif indent_diff < 11:
            return 3
        else:
            return max(1, (indent_diff + 2) // 4)

    def _is_valid_name(self, name: str) -> bool:
        """
        Validate name - flexible but safe
        """
        if not name or not name.strip():
            return False

        name = name.strip()

        if any(char in name for char in self.INVALID_PATH_CHARS):
            return False

        if name in {'.', '..'}:
            return False

        reserved_pattern = r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)'
        if re.match(reserved_pattern, name, re.IGNORECASE):
            return False

        if name.count(' ') > 5:
            return False

        if not re.search(r'[a-zA-Z0-9_]', name):
            return False

        return True

    def _is_likely_file(self, name: str) -> bool:
        """
        Determine if name is likely a file vs directory
        """
        if '.' in name and not name.startswith('.'):
            parts = name.rsplit('.', 1)
            if len(parts) == 2 and 1 <= len(parts[1]) <= 5 and parts[1].replace('_', '').isalnum():
                return True

        if name.upper() in [f.upper() for f in self.EXTENSIONLESS_FILES]:
            return True

        if name.startswith('.') and len(name) > 1:
            return True

        if name.endswith(('.sh', '.bat', '.cmd', '.ps1', '.py', '.js', '.rb')):
            return True

        return False

    def _build_unified_structure(self, paths: List[Tuple[str, bool]]) -> List[Dict]:
        """
        Build structure from all extracted paths
        """
        structure   = []
        all_dirs    = set()
        for path, is_dir in paths:
            if is_dir:
                all_dirs.add(path)
            parts = path.split('/')
            for i in range(1, len(parts)):
                parent = '/'.join(parts[:i])
                all_dirs.add(parent)

        for path, is_dir in paths:
            if path in self.seen_files or path in self.seen_dirs:
                continue

            parts = path.split('/')

            for i in range(1, len(parts)):
                dir_path = '/'.join(parts[:i])
                if dir_path not in self.seen_dirs:
                    self.seen_dirs.add(dir_path)
                    structure.append({
                        'type': 'directory',
                        'path': dir_path,
                        'name': parts[i-1]
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
                    structure.append({
                        'type': 'file',
                        'path': path,
                        'name': parts[-1],
                        'directory': '/'.join(parts[:-1]) if len(parts) > 1 else '.',
                        'content': '',
                        'extension': self._get_extension(parts[-1])
                    })

        return structure

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """Extract file extension"""
        if file_name.startswith('.'):
            if file_name.count('.') > 1:
                return file_name[1:]
            return file_name[1:]

        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]

        return ''

    def get_warnings(self) -> List[str]:
        """Get all parsing warnings"""
        return self.warnings


def parse_raw_structure(content: str) -> Tuple[List[Dict], List[str]]:
    """
    Convenience function to parse raw structure

    Returns:
        Tuple of (structure, warnings)
    """
    parser      = StructureParser()
    structure   = parser.parse(content)
    return structure, parser.get_warnings()


def print_tree_structure(structure: List[Dict]) -> None:
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
            parent = item.get('directory', '.')
            if parent == '.':
                parent = ''
            if parent not in tree:
                tree[parent] = {'dirs': [], 'files': []}
            tree[parent]['files'].append(item)

    def print_level(path: str, prefix: str = ""):
        if path not in tree:
            return

        items = tree[path]['dirs'] + tree[path]['files']
        for i, item in enumerate(items):
            is_last         = (i == len(items) - 1)
            connector       = "└── " if is_last else "├── "

            if item['type'] == 'directory':
                print(f"{prefix}{connector}{item['name']}/")
                extension = "    " if is_last else "│   "
                print_level(item['path'], prefix + extension)
            else:
                print(f"{prefix}{connector}{item['name']}")

    print_level('')