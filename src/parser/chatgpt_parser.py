"""
Advanced parser for ChatGPT responses
Handles simple and complex structures, avoids duplicates
"""
import re
from typing import List, Dict, Set, Optional, Tuple


class ChatGPTParser:
    """Parse ChatGPT responses to extract files and structure"""

    def __init__(self):
        self.seen_files     = set()
        self.seen_dirs      = set()
        self.project_root   = None

    def parse(self, content: str) -> List[Dict]:
        """
        Parse ChatGPT response content

        Args:
            content: ChatGPT response content

        Returns:
            List of dictionaries representing the structure
        """
        self.seen_files     = set()
        self.seen_dirs      = set()
        structure           = []
        self.project_root   = self._detect_project_root(content)
        code_blocks         = self._extract_code_blocks_advanced(content)

        for file_path, file_content, language in code_blocks:
            if not file_path:
                continue

            if self.project_root and file_path.startswith(self.project_root + '/'):
                file_path = file_path[len(self.project_root) + 1:]

            if file_path in self.seen_files:
                continue

            self.seen_files.add(file_path)

            parts = file_path.split('/')
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

            file_name = parts[-1]
            directory = '/'.join(parts[:-1]) if len(parts) > 1 else '.'

            structure.append({
                'type': 'file',
                'path': file_path,
                'name': file_name,
                'directory': directory,
                'content': file_content,
                'extension': self._get_extension(file_name)
            })

        return structure

    def _detect_project_root(self, content: str) -> Optional[str]:
        """
        Detect project root directory from tree structure

        Examples:
            my-project/
            project-name/
        """

        pattern1 = r'^([a-zA-Z0-9_\-]+)/\s*$'
        pattern2 = r'```\s*\n([a-zA-Z0-9_\-]+)/\s*\n'

        for pattern in [pattern1, pattern2]:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1)

        return None

    def _extract_code_blocks_advanced(self, content: str) -> List[Tuple[str, str, str]]:
        """
        Extract code blocks with smart filename detection

        Returns:
            List of tuples (filepath, content, language)
        """
        blocks          = []
        code_pattern    = r'```(\w+)?\s*\n(.*?)```'
        matches         = list(re.finditer(code_pattern, content, re.DOTALL))

        for i, match in enumerate(matches):
            language    = match.group(1) or ''
            code        = match.group(2).strip()
            file_path   = self._find_filename_before_block(content, match.start(), i)
            if file_path:
                blocks.append((file_path, code, language))
        return blocks

    def _find_filename_before_block(self, content: str, block_start: int, block_index: int) -> Optional[str]:
        """
        Find filename before a code block using multiple strategies
        """

        before_text     = content[max(0, block_start - 500):block_start]
        lines           = before_text.split('\n')

        for line in reversed(lines[-5:]):
            emoji_match = re.search(r'(?:📄|📁)\s*([a-zA-Z0-9_\-/.]+\.\w+)', line)
            if emoji_match:
                return emoji_match.group(1).strip()

        for line in reversed(lines[-5:]):
            header_match = re.search(r'#+\s*([a-zA-Z0-9_\-/.]+\.\w+)', line)
            if header_match:
                return header_match.group(1).strip()

        for line in reversed(lines[-5:]):
            clean_line = re.sub(r'[*_`]', '', line).strip()

            if '.' in clean_line and len(clean_line) < 100:
                file_match = re.search(r'([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*\.[a-zA-Z0-9]+)', clean_line)
                if file_match:
                    potential_file = file_match.group(1)
                    if not potential_file.startswith('http') and '://' not in potential_file:
                        return potential_file

        tree_pattern = r'([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*\.[a-zA-Z0-9]+)'
        for line in reversed(lines[-20:]):
            if re.match(r'\s*[├└│]\s*', line):
                file_match = re.search(tree_pattern, line)
                if file_match:
                    return file_match.group(1)

        return None

    def _extract_from_tree_structure(self, content: str) -> List[str]:
        """
        Extract file paths from ASCII tree structure

        Example:
            my-project/
                src/
                    index.js
                package.json
        """
        paths           = []
        lines           = content.split('\n')
        current_path    = []
        prev_indent     = 0

        for line in lines:
            if not line.strip():
                continue

            indent  = len(line) - len(line.lstrip())
            clean   = re.sub(r'[├└│─\s]+', '', line).strip()

            if not clean:
                continue

            is_dir  = clean.endswith('/')
            clean   = clean.rstrip('/')

            if indent > prev_indent:
                current_path.append(clean)
            elif indent == prev_indent:
                if current_path:
                    current_path[-1] = clean
                else:
                    current_path.append(clean)
            else:
                levels_up       = (prev_indent - indent) // 4 + 1
                current_path    = current_path[:-levels_up]
                current_path.append(clean)

            if not is_dir and '.' in clean:
                paths.append('/'.join(current_path))

            prev_indent = indent

        return paths

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """Extract file extension"""
        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]
        return ''