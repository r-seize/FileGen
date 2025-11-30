"""
Structure builder
Organizes and optimizes parsed structure
"""
from typing import List, Dict, Set


class StructureBuilder:
    """Builds and optimizes file structure"""

    @staticmethod
    def build(raw_structure: List[Dict]) -> List[Dict]:
        """
        Builds an optimized structure

        Args:
            raw_structure: Raw parser structure

        Returns:
            Organized and optimized structure
        """
        sorted_structure = sorted(
            raw_structure,
            key=lambda x: (x['path'].count('/'), x['path'])
        )

        seen_dirs: Set[str]     = set()
        optimized               = []

        for item in sorted_structure:
            if item['type'] == 'directory':
                if item['path'] not in seen_dirs:
                    seen_dirs.add(item['path'])
                    optimized.append(item)
            else:
                optimized.append(item)

        return optimized

    @staticmethod
    def get_tree_representation(structure: List[Dict]) -> str:
        """
        Generates a tree representation of the structure

        Returns:
            String representing the tree
        """
        lines = []

        for item in structure:
            depth   = item['path'].count('/')
            indent  = "  " * depth

            if item['type'] == 'directory':
                lines.append(f"{indent}📁 {item['name']}/")
            else:
                lines.append(f"{indent}📄 {item['name']}")

        return "\n".join(lines)

    @staticmethod
    def validate_hierarchy(structure: List[Dict]) -> bool:
        """
        Validates that the hierarchy is consistent

        Returns:
            True if hierarchy is valid
        """
        directories = {
            item['path'] 
            for item in structure 
            if item['type'] == 'directory'
        }

        for item in structure:
            if item['type'] == 'file':
                parent = item['directory']
                if parent not in directories:
                    return False

        return True
