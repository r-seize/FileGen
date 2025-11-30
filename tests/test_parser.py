import pytest
from pathlib import Path
from src.parser.markdown_parser import MarkdownParser
from src.utils.exceptions import ParsingError


def test_parse_simple_structure(tmp_path):
    """Test parsing a simple structure"""
    md_content = """
    # FolderA
    ## file1.txt
    File 1 content

    ## file2.txt
    File 2 content
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content)

    parser      = MarkdownParser()
    structure   = parser.parse(md_file)

    assert len(structure) == 3
    assert structure[0]['type'] == 'directory'
    assert structure[0]['path'] == 'FolderA'
    assert structure[1]['type'] == 'file'
    assert structure[1]['name'] == 'file1.txt'


def test_parse_nested_structure(tmp_path):
    """Test parsing a nested structure"""
    md_content = """
    # FolderA/SubFolder
    ## nested.txt
    Nested content
    """
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content)

    parser      = MarkdownParser()
    structure   = parser.parse(md_file)

    assert len(structure) >= 2


def test_parse_empty_file():
    """Test parsing an empty file"""
    parser = MarkdownParser()

    with pytest.raises(ParsingError):
        parser.parse(Path("nonexistent.md"))


def test_parse_file_without_directory(tmp_path):
    """Test parsing a file without a parent directory"""
    md_content = """
    ## orphan_file.txt
    Content without folder
    """
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content)

    parser = MarkdownParser()

    with pytest.raises(ParsingError):
        parser.parse(md_file)


def test_parse_multiple_directories(tmp_path):
    """Test parsing multiple directories"""
    md_content = """# FolderA
## file_a.txt
A

# FolderB
## file_b.txt
B

# FolderC
## file_c.txt
C
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content)

    parser      = MarkdownParser()
    structure   = parser.parse(md_file)
    directories = [item for item in structure if item['type'] == 'directory']
    files       = [item for item in structure if item['type'] == 'file']

    assert len(directories) == 3
    assert len(files) == 3
