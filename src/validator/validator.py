"""
Structure validator
Validates structure before generation
"""
import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool          = True
    errors: List[str]       = field(default_factory=list)
    warnings: List[str]     = field(default_factory=list)
    conflicts: List[str]    = field(default_factory=list)


class StructureValidator:
    """Validates structure before generation"""

    INVALID_CHARS = r'[<>:"|?*\x00-\x1f]'

    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr',
        'vbs', 'ps1', 'sh'
    }

    def __init__(self, warn_dangerous: bool = True):
        self.warn_dangerous = warn_dangerous

    def validate(
        self,
        structure: List[Dict],
        output_dir: Path
    ) -> ValidationResult:
        result                  = ValidationResult()
        seen_paths: Set[str]    = set()

        for item in structure:
            if item['path'] in seen_paths:
                result.errors.append(
                    f"Duplicate path: {item['path']}"
                )
                result.is_valid = False
            seen_paths.add(item['path'])
            
            if not self._is_valid_name(item['name']):
                result.errors.append(
                    f"Invalid name: {item['name']} "
                    f"(contains forbidden characters)"
                )
                result.is_valid = False

            if not self._is_valid_path(item['path']):
                result.errors.append(
                    f"Invalid path: {item['path']}"
                )
                result.is_valid = False

            if item['type'] == 'file':
                file_path = output_dir / item['path']
                if file_path.exists():
                    result.conflicts.append(item['path'])

                if self.warn_dangerous:
                    ext = item.get('extension', '').lower()
                    if ext in self.DANGEROUS_EXTENSIONS:
                        result.warnings.append(
                            f"Potentially dangerous extension: "
                            f"{item['path']} (.{ext})"
                        )

            full_path = output_dir / item['path']
            if len(str(full_path)) > 255:
                result.warnings.append(
                    f"Very long path (may cause issues on Windows): "
                    f"{item['path']}"
                )

        return result

    def _is_valid_name(self, name: str) -> bool:
        if not name or name.strip() == '':
            return False

        if re.search(self.INVALID_CHARS, name):
            return False

        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5',
            'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }

        name_upper = name.split('.')[0].upper()
        if name_upper in reserved_names:
            return False

        if name.endswith('.') or name.endswith(' '):
            return False

        return True

    def _is_valid_path(self, path: str) -> bool:
        if not path or path.strip() == '':
            return False

        parts = path.split('/')
        for part in parts:
            if not self._is_valid_name(part):
                return False

        if path.startswith('/') or path.startswith('\\'):
            return False

        if '..' in parts:
            return False

        return True