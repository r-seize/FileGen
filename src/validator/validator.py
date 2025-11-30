"""
Validateur de structure
Vérifie la validité de la structure avant génération
"""
import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Résultat de la validation"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


class StructureValidator:
    """Valide une structure avant génération"""
    
    # Caractères interdits dans les noms de fichiers (Windows + Unix)
    INVALID_CHARS = r'[<>:"|?*\x00-\x1f]'
    
    # Extensions potentiellement dangereuses
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr',
        'vbs', 'ps1', 'sh'
    }
    
    def __init__(self, warn_dangerous: bool = True):
        """
        Args:
            warn_dangerous: Avertir pour les extensions dangereuses
        """
        self.warn_dangerous = warn_dangerous
    
    def validate(
        self,
        structure: List[Dict],
        output_dir: Path
    ) -> ValidationResult:
        """
        Valide une structure complète
        
        Args:
            structure: Structure à valider
            output_dir: Répertoire de destination
            
        Returns:
            Résultat de la validation
        """
        result = ValidationResult()
        seen_paths: Set[str] = set()
        
        for item in structure:
            # Vérifier les doublons
            if item['path'] in seen_paths:
                result.errors.append(
                    f"Chemin en double: {item['path']}"
                )
                result.is_valid = False
            seen_paths.add(item['path'])
            
            # Valider le nom
            if not self._is_valid_name(item['name']):
                result.errors.append(
                    f"Nom invalide: {item['name']} "
                    f"(contient des caractères interdits)"
                )
                result.is_valid = False
            
            # Valider le chemin
            if not self._is_valid_path(item['path']):
                result.errors.append(
                    f"Chemin invalide: {item['path']}"
                )
                result.is_valid = False
            
            # Vérifier les fichiers existants
            if item['type'] == 'file':
                file_path = output_dir / item['path']
                if file_path.exists():
                    result.conflicts.append(item['path'])
                
                # Avertir pour les extensions dangereuses
                if self.warn_dangerous:
                    ext = item.get('extension', '').lower()
                    if ext in self.DANGEROUS_EXTENSIONS:
                        result.warnings.append(
                            f"Potentially dangerous extension: "
                            f"{item['path']} (.{ext})"
                        )
            
            # Vérifier la longueur du chemin (limite Windows: 260 caractères)
            full_path = output_dir / item['path']
            if len(str(full_path)) > 255:
                result.warnings.append(
                    f"Chemin très long (peut causer des problèmes sur Windows): "
                    f"{item['path']}"
                )
        
        return result
    
    def _is_valid_name(self, name: str) -> bool:
        """Vérifie si un nom de fichier/dossier est valide"""
        if not name or name.strip() == '':
            return False
        
        # Vérifier les caractères invalides
        if re.search(self.INVALID_CHARS, name):
            return False
        
        # Noms réservés Windows
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
        
        # Ne doit pas se terminer par un point ou un espace
        if name.endswith('.') or name.endswith(' '):
            return False
        
        return True
    
    def _is_valid_path(self, path: str) -> bool:
        """Vérifie si un chemin est valide"""
        if not path or path.strip() == '':
            return False
        
        # Vérifier chaque composant du chemin
        parts = path.split('/')
        for part in parts:
            if not self._is_valid_name(part):
                return False
        
        # Pas de chemins absolus
        if path.startswith('/') or path.startswith('\\'):
            return False
        
        # Pas de navigation parent (..)
        if '..' in parts:
            return False
        
        return True