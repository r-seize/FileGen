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
                    self.current_directory = title.strip()
                    self._add_directory(self.current_directory)
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
        """Extract file extension"""
        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]
        return ''
