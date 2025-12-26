"""
Advanced parser for ChatGPT responses
Handles simple and complex structures, avoids duplicates
Enhanced with intelligent tree structure detection and support for:
- Dotfiles (.env, .gitignore, .github, etc.)
- Files without extensions (LICENSE, Dockerfile, README, etc.)
"""
import re
from typing import List, Dict, Set, Optional, Tuple


class ChatGPTParser:
    """Parse ChatGPT responses to extract files and structure"""

    # Common files without extensions
    EXTENSIONLESS_FILES = {
        'LICENSE', 'LICENCE', 'README', 'CHANGELOG', 'CONTRIBUTING',
        'AUTHORS', 'CREDITS', 'INSTALL', 'MANIFEST', 'NOTICE',
        'Dockerfile', 'Makefile', 'Procfile', 'Rakefile',
        'Gemfile', 'Podfile', 'Fastfile', 'Appfile',
        'CODEOWNERS', 'Vagrantfile', 'Brewfile'
    }

    # Common dotfile patterns
    DOTFILE_PATTERNS = {
        '.env', '.gitignore', '.gitattributes', '.editorconfig',
        '.prettierrc', '.eslintrc', '.babelrc', '.dockerignore',
        '.npmrc', '.yarnrc', '.nvmrc', '.ruby-version', '.python-version',
        '.node-version', '.tool-versions', '.htaccess', '.browserslistrc'
    }

    def __init__(self):
        self.seen_files     = set()
        self.seen_dirs      = set()
        self.project_root   = None

    def parse(self, content: str) -> List[Dict]:
        """
        Parse ChatGPT response content with enhanced tree structure detection

        Args:
            content: ChatGPT response content

        Returns:
            List of dictionaries representing the structure
        """
        self.seen_files     = set()
        self.seen_dirs      = set()
        structure           = []
        self.project_root   = self._detect_project_root(content)
        tree_structure      = self._extract_from_tree_structure(content)

        if tree_structure:
            for file_path in tree_structure:
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

                file_name       = parts[-1]
                directory       = '/'.join(parts[:-1]) if len(parts) > 1 else '.'
                file_content    = self._find_content_for_file(content, file_path)

                structure.append({
                    'type': 'file',
                    'path': file_path,
                    'name': file_name,
                    'directory': directory,
                    'content': file_content,
                    'extension': self._get_extension(file_name)
                })

        code_blocks = self._extract_code_blocks_advanced(content)

        for file_path, file_content, language in code_blocks:
            if not file_path:
                continue

            if self.project_root and file_path.startswith(self.project_root + '/'):
                file_path = file_path[len(self.project_root) + 1:]

            if file_path in self.seen_files:
                for item in structure:
                    if item.get('path') == file_path and item.get('type') == 'file':
                        if not item.get('content') or len(file_content) > len(item.get('content', '')):
                            item['content'] = file_content
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

            file_name   = parts[-1]
            directory   = '/'.join(parts[:-1]) if len(parts) > 1 else '.'

            structure.append({
                'type': 'file',
                'path': file_path,
                'name': file_name,
                'directory': directory,
                'content': file_content,
                'extension': self._get_extension(file_name)
            })

        return structure

    def _find_content_for_file(self, content: str, file_path: str) -> str:
        """
        Find content for a specific file in the conversation

        Args:
            content: Full ChatGPT response
            file_path: File path to search for

        Returns:
            File content if found, empty string otherwise
        """
        file_name       = file_path.split('/')[-1]
        code_pattern    = r'```(\w+)?\s*\n(.*?)```'
        matches         = list(re.finditer(code_pattern, content, re.DOTALL))

        for match in matches:
            before_text = content[max(0, match.start() - 500):match.start()]
            if file_path in before_text or file_name in before_text:
                return match.group(2).strip()
        return ''

    def _detect_project_root(self, content: str) -> Optional[str]:
        """
        Detect project root directory from tree structure

        Examples:
            my-project/
            project-name/
        """
        pattern1    = r'^([a-zA-Z0-9_\-]+)/\s*$'
        pattern2    = r'```\s*\n([a-zA-Z0-9_\-]+)/\s*\n'
        pattern3    = r'(?:tree|structure|projet|project).*?\n\s*([a-zA-Z0-9_\-]+)/\s*\n'

        for pattern in [pattern1, pattern2, pattern3]:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_code_blocks_advanced(self, content: str) -> List[Tuple[str, str, str]]:
        """
        Extract code blocks with smart filename detection
        Enhanced to support dotfiles and extensionless files

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
            elif language in ['env', 'dotenv', 'bash'] or self._looks_like_env_content(code):
                file_path = self._detect_special_filename(content, match.start(), code)
                if file_path:
                    blocks.append((file_path, code, self._detect_language(file_path)))
        return blocks

    def _is_valid_filename(self, name: str) -> bool:
        """
        Check if a name is a valid file or directory name
        Enhanced to recognize dotfiles and extensionless files
        Universal approach working for all languages

        Args:
            name: Filename to check

        Returns:
            True if it's a valid filename
        """
        if not name or len(name) > 100:
            return False

        # Reject lines with too many spaces (likely prose)
        # File/folder names typically don't have multiple spaces
        if name.count(' ') > 1:
            return False

        # Reject invalid filesystem characters
        if any(char in name for char in ['<', '>', '|', '*', '?', '"', ',', ';', ':', '\\']):
            return False

        # Reject URLs
        if name.startswith('http') or '://' in name:
            return False

        basename = name.split('/')[-1]

        # Universal prose detection: check for sentence patterns
        # Prose typically has: punctuation at end, multiple words with lowercase, etc.
        if len(name.split()) > 3:
            # If more than 3 words, check for sentence indicators
            if name.endswith('.') or name.endswith('!') or name.endswith('?'):
                return False
            # Check if it contains common sentence patterns (word word word)
            words = name.split()
            lowercase_count = sum(1 for w in words if w.islower() and len(w) > 2)
            if lowercase_count >= 3:
                return False

        # Accept dotfiles
        if basename.startswith('.'):
            if len(basename) > 1:
                return True
            return False

        # Accept known extensionless files
        if basename.upper() in [f.upper() for f in self.EXTENSIONLESS_FILES]:
            return True

        # Accept files with extensions
        if '.' in basename:
            return True

        return False

    def _looks_like_env_content(self, content: str) -> bool:
        """
        Check if content looks like environment variables

        Returns:
            True if content appears to be .env format
        """
        lines = content.strip().split('\n')

        if not lines:
            return False

        env_pattern     = r'^[A-Z_][A-Z0-9_]*\s*=\s*.+$'
        matches         = 0

        for line in lines:
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            if re.match(env_pattern, line):
                matches += 1
        
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        if non_empty_lines and matches / len(non_empty_lines) >= 0.5:
            return True
        return False

    def _detect_special_filename(self, content: str, block_start: int, code_content: str) -> Optional[str]:
        """
        Detect special filenames (dotfiles, extensionless) from context

        Args:
            content: Full content
            block_start: Position where code block starts
            code_content: Content of the code block

        Returns:
            Filename if detected, None otherwise
        """
        before_text         = content[max(0, block_start - 300):block_start]
        dotfile_pattern     = r'(\.(?:env|git[a-z]*|[a-z]+rc|[a-z]+ignore|[a-z]+attributes)(?:\.\w+)?)'
        match               = re.search(dotfile_pattern, before_text, re.IGNORECASE)
        if match:
            return match.group(1)

        for filename in self.EXTENSIONLESS_FILES:
            if re.search(r'\b' + re.escape(filename) + r'\b', before_text, re.IGNORECASE):
                return filename

        if self._looks_like_env_content(code_content):
            return '.env'

        return None

    def _detect_language(self, filename: str) -> str:
        """
        Detect language from filename

        Args:
            filename: Name of the file

        Returns:
            Language identifier
        """
        ext = self._get_extension(filename)

        language_map = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'py': 'python',
            'rb': 'ruby',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml',
            'md': 'markdown',
            'sh': 'bash',
            'env': 'bash',
            'gitignore': 'text',
        }

        return language_map.get(ext, 'text')

    def _find_filename_before_block(self, content: str, block_start: int, block_index: int) -> Optional[str]:
        """
        Find filename before a code block using multiple strategies
        Enhanced to detect dotfiles and extensionless files
        """
        before_text     = content[max(0, block_start - 500):block_start]
        lines           = before_text.split('\n')

        # Strategy 1: Look for emoji indicators
        for line in reversed(lines[-5:]):
            emoji_match = re.search(r'(?:📄|📁|🔧|⚙️|🔒)\s*([a-zA-Z0-9_\-/.]+(?:\.\w+)?|\.[\w.]+)', line)
            if emoji_match:
                potential = emoji_match.group(1).strip()
                if self._is_valid_filename(potential):
                    return potential

        # Strategy 2: Look for markdown headers
        for line in reversed(lines[-5:]):
            header_match = re.search(r'#+\s*(?:`)?([a-zA-Z0-9_\-/.]+(?:\.\w+)?|\.[\w.]+)(?:`)?', line)
            if header_match:
                potential = header_match.group(1).strip()
                if self._is_valid_filename(potential):
                    return potential

        # Strategy 3: Look for quoted filenames (including dotfiles)
        for line in reversed(lines[-5:]):
            quote_match = re.search(r'["`\']((?:\.?[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-\.]+)*(?:\.\w+)?)|\.[\w.]+)["`\']', line)
            if quote_match:
                potential = quote_match.group(1)
                if self._is_valid_filename(potential):
                    return potential

        # Strategy 4: Look for extensionless files or dotfiles in clean text
        for line in reversed(lines[-5:]):
            clean_line = re.sub(r'[*_`]', '', line).strip()

            if len(clean_line) < 100:
                # Check for extensionless files
                for filename in self.EXTENSIONLESS_FILES:
                    if re.search(r'\b' + re.escape(filename) + r'\b', clean_line):
                        return filename

                # Check for dotfiles
                dotfile_match = re.search(r'(\.(?:[a-zA-Z0-9_\-]+)(?:\.\w+)?)', clean_line)
                if dotfile_match:
                    potential = dotfile_match.group(1)
                    if self._is_valid_filename(potential):
                        return potential

                # General file pattern
                file_match = re.search(
                    r'(\.?[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-\.]+)*(?:\.[a-zA-Z0-9]+)?)',
                    clean_line
                )
                if file_match:
                    potential_file = file_match.group(1)
                    if self._is_valid_filename(potential_file):
                        return potential_file

        # Strategy 5: Look in tree structure
        tree_pattern = r'(\.?[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-\.]+)*(?:\.[a-zA-Z0-9]+)?|\.[\w.]+)'
        for line in reversed(lines[-20:]):
            if re.match(r'\s*[├└│]\s*', line):
                file_match = re.search(tree_pattern, line)
                if file_match:
                    potential = file_match.group(1)
                    if self._is_valid_filename(potential):
                        return potential

        return None

    def _extract_from_tree_structure(self, content: str) -> List[str]:
        """
        Extract file paths from ASCII tree structure
        Enhanced to handle dotfiles, .github directories, and extensionless files
        """
        paths           = []
        lines           = content.split('\n')
        current_path    = []
        prev_indent     = 0
        tree_started    = False

        for line in lines:
            line_stripped = line.strip()
            if line_stripped == '```' or line_stripped.startswith('```'):
                if not tree_started:
                    tree_started = True
                    continue
                else:
                    break

            if not tree_started:
                continue

            if not line.strip():
                continue

            clean_line      = re.sub(r'^[\s│├└─]+', '', line)
            stripped        = line.lstrip()
            indent          = len(line) - len(stripped)
            name            = clean_line.strip()
            if '#' in name:
                name = name.split('#')[0].strip()

            if not name or len(name) > 100:
                continue

            if ' ' in name and not name.startswith('.') and '/' not in name:
                word_count = len([w for w in name.split() if len(w) > 2])
                if word_count > 3:
                    continue

            is_dir          = name.endswith('/')
            name            = name.rstrip('/')

            if any(char in name for char in ['<', '>', '|', '*', '?', '"', ',']):
                continue

            if indent > prev_indent:
                current_path.append(name)
            elif indent == prev_indent:
                if current_path:
                    current_path[-1] = name
                else:
                    current_path.append(name)
            else:
                indent_diff     = prev_indent - indent
                levels_up       = max(1, indent_diff // 4)
                current_path    = current_path[:-levels_up] if levels_up < len(current_path) else []
                current_path.append(name)

            if not is_dir:
                file_path = '/'.join(current_path)
                if (name.startswith('.') or 
                    '.' in name or 
                    name.upper() in [f.upper() for f in self.EXTENSIONLESS_FILES]):
                    if file_path not in paths:
                        paths.append(file_path)

            prev_indent = indent

        return paths

    @staticmethod
    def _get_extension(file_name: str) -> str:
        """
        Extract file extension
        Enhanced to handle dotfiles and extensionless files

        Args:
            file_name: Name of the file

        Returns:
            Extension or special identifier
        """
        if file_name.startswith('.'):
            if file_name.count('.') > 1:
                return file_name[1:]
            elif file_name.count('.') == 1:
                return file_name[1:]

        if '.' in file_name:
            return file_name.rsplit('.', 1)[1]
        return ''