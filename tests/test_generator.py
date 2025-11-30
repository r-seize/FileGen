import pytest
from pathlib import Path
from src.generator.file_generator import FileGenerator
from src.generator.directory_manager import DirectoryManager


def test_create_simple_file(tmp_path):
    """Test creating a simple file"""
    structure = [
        {'type': 'directory', 'path': 'test', 'name': 'test'},
        {
            'type': 'file',
            'path': 'test/file.txt',
            'name': 'file.txt',
            'directory': 'test',
            'content': 'Hello World',
            'extension': 'txt'
        }
    ]

    generator   = FileGenerator(output_dir=tmp_path, force=False)
    result      = generator.generate(structure)

    assert result['directories_created'] == 1
    assert result['files_created'] == 1

    created_file = tmp_path / 'test' / 'file.txt'
    assert created_file.exists()
    assert created_file.read_text() == 'Hello World'


def test_skip_existing_file(tmp_path):
    """Test skipping existing files without force"""
    test_dir = tmp_path / 'test'
    test_dir.mkdir()
    existing_file = test_dir / 'file.txt'
    existing_file.write_text('Original')

    structure = [
        {'type': 'directory', 'path': 'test', 'name': 'test'},
        {
            'type': 'file',
            'path': 'test/file.txt',
            'name': 'file.txt',
            'directory': 'test',
            'content': 'New Content',
            'extension': 'txt'
        }
    ]

    generator   = FileGenerator(output_dir=tmp_path, force=False)
    result      = generator.generate(structure)

    assert result['files_skipped'] == 1
    assert existing_file.read_text() == 'Original'


def test_overwrite_with_force(tmp_path):
    """Test overwriting files with force=True"""
    test_dir = tmp_path / 'test'
    test_dir.mkdir()
    existing_file = test_dir / 'file.txt'
    existing_file.write_text('Original')

    structure = [
        {'type': 'directory', 'path': 'test', 'name': 'test'},
        {
            'type': 'file',
            'path': 'test/file.txt',
            'name': 'file.txt',
            'directory': 'test',
            'content': 'New Content',
            'extension': 'txt'
        }
    ]

    generator   = FileGenerator(output_dir=tmp_path, force=True)
    result      = generator.generate(structure)

    assert result['files_created'] == 1
    assert existing_file.read_text() == 'New Content'


def test_directory_manager_operations(tmp_path):
    """Test DirectoryManager operations"""
    test_dir = tmp_path / 'test_dir'

    DirectoryManager.ensure_directory(test_dir)
    assert test_dir.exists()

    assert DirectoryManager.is_empty(test_dir)

    (test_dir / 'file.txt').write_text('test')
    assert not DirectoryManager.is_empty(test_dir)

    files = DirectoryManager.get_files(test_dir)
    assert len(files) == 1


def test_nested_directory_creation(tmp_path):
    """Test nested directory creation"""
    structure = [
        {'type': 'directory', 'path': 'a', 'name': 'a'},
        {'type': 'directory', 'path': 'a/b', 'name': 'b'},
        {'type': 'directory', 'path': 'a/b/c', 'name': 'c'},
        {
            'type': 'file',
            'path': 'a/b/c/deep.txt',
            'name': 'deep.txt',
            'directory': 'a/b/c',
            'content': 'Deep file',
            'extension': 'txt'
        }
    ]

    generator   = FileGenerator(output_dir=tmp_path)
    result      = generator.generate(structure)

    assert result['directories_created'] == 3
    assert result['files_created'] == 1

    deep_file = tmp_path / 'a' / 'b' / 'c' / 'deep.txt'
    assert deep_file.exists()
    assert deep_file.read_text() == 'Deep file'
