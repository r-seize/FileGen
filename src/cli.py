"""
Simple CLI interface for FileGen
"""
import sys
from pathlib import Path
from typing import Optional
import traceback
from src.parser.markdown_parser import MarkdownParser
from src.parser.chatgpt_parser import ChatGPTParser
from src.parser.structure_parser import StructureParser
from src.generator.file_generator import FileGenerator
from src.validator.validator import StructureValidator
from src.utils.exceptions import FileGenError, ParsingError, ValidationError, GenerationError

__version__ = "0.1.4"


def print_tree_preview(structure: list) -> None:
    """
    Print structure in proper tree format with correct hierarchy

    Args:
        structure: List of structure items with 'path' and 'type'
    """
    print("\nStructure:")

    if not structure:
        print("(empty)")
        return

    tree            = {}
    all_paths       = set()

    for item in structure:
        path = item['path']
        all_paths.add(path)

        if '/' in path:
            parent = '/'.join(path.split('/')[:-1])
        else:
            parent = ''

        if parent not in tree:
            tree[parent] = []
        tree[parent].append(item)

    for parent in tree:
        tree[parent].sort(key=lambda x: (x['type'] == 'file', x['name']))

    def print_level(parent_path: str, prefix: str = ""):
        if parent_path not in tree:
            return

        items = tree[parent_path]

        for i, item in enumerate(items):
            is_last     = (i == len(items) - 1)
            connector   = "└── " if is_last else "├── "

            if item['type'] == 'directory':
                print(f"{prefix}{connector}{item['name']}/")
                extension = "    " if is_last else "│   "
                print_level(item['path'], prefix + extension)
            else:
                print(f"{prefix}{connector}{item['name']}")

    print_level('')


def raw_structure_mode(input_file: Optional[Path] = None):
    """Mode for parsing raw tree structures"""

    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[ERROR] Unable to read file: {e}")
            return 1
    else:
        print("[INFO] Raw structure mode - Paste your tree structure below")
        print("[INFO] Press Enter twice when done")
        print("=" * 60)

        lines           = []
        empty_count     = 0

        try:
            while True:
                try:
                    line = input()
                except KeyboardInterrupt:
                    print("\n[WARN] Interrupted")
                    return 130

                if not line.strip():
                    empty_count += 1
                    if empty_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_count = 0
                    lines.append(line)

        except EOFError:
            pass

        content = '\n'.join(lines)

    if not content.strip():
        print("[ERROR] No content provided")
        return 1

    print("\n" + "=" * 60)
    print("[INFO] Parsing tree structure...")

    try:
        parser      = StructureParser()
        structure   = parser.parse(content)

        if not structure:
            print("[ERROR] No files found in the structure")
            return 1

        print(f"[INFO] Found {len(structure)} elements")

        warnings = parser.get_warnings()
        if warnings:
            print(f"[WARN] {len(warnings)} warning(s):")
            for warning in warnings[:5]:
                print(f"  - {warning}")
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more")

        validator   = StructureValidator()
        output_dir  = Path.cwd()
        result      = validator.validate(structure, output_dir)

        if not result.is_valid:
            print("[ERROR] Validation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        print_tree_preview(structure)

        response = input("\nCreate these files? [y/N] ")
        if response.lower() not in ['y', 'yes']:
            print("[INFO] Cancelled")
            return 0

        print("\n[INFO] Creating files...")
        generator   = FileGenerator(output_dir=output_dir, force=False)
        stats       = generator.generate(structure)

        print(f"\n[OK] Created {stats['directories_created']} directories")
        print(f"[OK] Created {stats['files_created']} files")

        if stats['errors']:
            print(f"[ERROR] {len(stats['errors'])} errors occurred")
            for error in stats['errors']:
                print(f"  - {error}")

        print(f"\n[INFO] Output: {output_dir.resolve()}")
        return 0

    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return 1


def chatgpt_mode():
    print("[INFO] ChatGPT mode - Paste your ChatGPT response below")
    print("[INFO] Press Enter twice when done")
    print("=" * 60)

    lines           = []
    empty_count     = 0

    try:
        while True:
            line = input()

            if not line.strip():
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)
                
    except EOFError:
        pass

    content = '\n'.join(lines)

    if not content.strip():
        print("[ERROR] No content provided")
        return 1

    print("\n" + "=" * 60)
    print("[INFO] Parsing ChatGPT response...")

    try:
        parser      = ChatGPTParser()
        structure   = parser.parse(content)

        if not structure:
            print("[ERROR] No files found in the response")
            print("[INFO] Make sure the response contains code blocks with file names")
            return 1

        print(f"[INFO] Found {len(structure)} elements")

        validator   = StructureValidator()
        output_dir  = Path.cwd()
        result      = validator.validate(structure, output_dir)

        if not result.is_valid:
            print("[ERROR] Validation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        print_tree_preview(structure)

        response = input("\nCreate these files? [y/N] ")
        if response.lower() not in ['y', 'yes']:
            print("[INFO] Cancelled")
            return 0

        print("\n[INFO] Creating files...")
        generator   = FileGenerator(output_dir=output_dir, force=False)
        stats       = generator.generate(structure)

        print(f"\n[OK] Created {stats['directories_created']} directories")
        print(f"[OK] Created {stats['files_created']} files")

        if stats['errors']:
            print(f"[ERROR] {len(stats['errors'])} errors occurred")
            for error in stats['errors']:
                print(f"  - {error}")

        print(f"\n[INFO] Output: {output_dir.resolve()}")
        return 0

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def print_help():
    help_text = """
FileGen v0.1.4 - File generator from Markdown and raw structures

Usage:
    filegen <file.md>                    Create files from Markdown
    filegen --chatgpt                    Create files from ChatGPT response
    filegen --raw [file.txt]             Create files from raw tree structure
    filegen <file.md> -o <dir>           Create in specific directory
    filegen <file.md> --preview          Preview without creating
    filegen <file.md> --force            Overwrite existing files
    filegen --help                       Show this help
    filegen --version                    Show version

Examples:
    filegen structure.md
    filegen structure.md -o my-project
    filegen structure.md --preview
    filegen --chatgpt
    filegen --raw                        # Interactive mode
    filegen --raw structure.txt          # From file (RECOMMENDED)

Raw Structure Mode:
    RECOMMENDED: Save your structure to a file first!
    
    echo "project/
    ├── src/
    │   └── main.py
    └── README.md" > structure.txt
    
    filegen --raw structure.txt
    
    Interactive mode (may have terminal issues with large structures):
    filegen --raw
"""
    print(help_text)


def main():
    args = sys.argv[1:]

    if not args:
        print("[ERROR] No file specified")
        print("Usage: filegen <file.md>")
        print("       filegen --chatgpt")
        print("       filegen --raw")
        print("Help: filegen --help")
        return 1

    if args[0] in ['--help', '-h']:
        print_help()
        return 0

    if args[0] in ['--version', '-v']:
        print(f"FileGen v{__version__}")
        return 0

    if args[0] in ['--chatgpt', '--gpt', '-g']:
        return chatgpt_mode()

    if args[0] in ['--raw', '--tree', '-r']:
        input_file = None
        if len(args) > 1 and not args[1].startswith('-'):
            input_file = Path(args[1])
            if not input_file.exists():
                print(f"[ERROR] File not found: {input_file}")
                return 1
        return raw_structure_mode(input_file)

    md_file         = Path(args[0])
    output_dir      = Path.cwd()
    preview         = False
    force           = False

    i = 1
    while i < len(args):
        if args[i] in ['-o', '--output']:
            if i + 1 < len(args):
                output_dir = Path(args[i + 1])
                i += 2
            else:
                print("[ERROR] -o requires a path")
                return 1
        elif args[i] in ['--preview', '-p']:
            preview = True
            i += 1
        elif args[i] in ['--force', '-f']:
            force = True
            i += 1
        else:
            print(f"[ERROR] Unknown option: {args[i]}")
            return 1

    if not md_file.exists():
        print(f"[ERROR] File not found: {md_file}")
        return 1

    try:
        print(f"[INFO] Reading {md_file.name}")
        parser      = MarkdownParser()
        structure   = parser.parse(md_file)
        print(f"[INFO] Found {len(structure)} elements")

        validator   = StructureValidator()
        result      = validator.validate(structure, output_dir)

        if not result.is_valid:
            print("[ERROR] Validation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        if result.warnings:
            for warning in result.warnings:
                print(f"[WARN] {warning}")

        print_tree_preview(structure)

        if preview:
            print("\n[INFO] Dry-run mode - no files created")
            return 0

        if result.conflicts and not force:
            print(f"\n[WARN] {len(result.conflicts)} file(s) already exist")
            for conflict in result.conflicts[:5]:
                print(f"  - {conflict}")
            if len(result.conflicts) > 5:
                print(f"  ... and {len(result.conflicts) - 5} more")

            response = input("\nOverwrite? [y/N] ")
            if response.lower() not in ['y', 'yes']:
                print("[INFO] Cancelled")
                return 0

        print("\n[INFO] Creating files...")
        generator       = FileGenerator(output_dir=output_dir, force=force)
        stats           = generator.generate(structure)

        print(f"\n[OK] Created {stats['directories_created']} directories")
        print(f"[OK] Created {stats['files_created']} files")

        if stats['files_skipped'] > 0:
            print(f"[SKIP] Skipped {stats['files_skipped']} files")

        if stats['errors']:
            print(f"[ERROR] {len(stats['errors'])} errors occurred")
            for error in stats['errors']:
                print(f"  - {error}")

        print(f"\n[INFO] Output: {output_dir.resolve()}")
        return 0

    except ParsingError as e:
        print(f"[ERROR] Parsing error: {e}")
        return 1
    except ValidationError as e:
        print(f"[ERROR] Validation error: {e}")
        return 1
    except GenerationError as e:
        print(f"[ERROR] Generation error: {e}")
        return 1
    except FileGenError as e:
        print(f"[ERROR] {e}")
        return 1
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted")
        return 130
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())