"""
Simple CLI interface for FileGen
"""
import sys
from pathlib import Path

from src.parser.markdown_parser import MarkdownParser
from src.parser.chatgpt_parser import ChatGPTParser
from src.generator.file_generator import FileGenerator
from src.validator.validator import StructureValidator
from src.utils.exceptions import FileGenError, ParsingError, ValidationError, GenerationError

__version__ = "0.1.1"


def print_tree_preview(structure: list) -> None:
    print("\nStructure:")

    tree = {}
    for item in structure:
        path_parts  = item['path'].split('/')
        current     = tree
        for i, part in enumerate(path_parts):
            if part not in current:
                current[part] = {}
            current = current[part]

    def print_tree_recursive(node: dict, prefix: str = "", is_last: bool = True):
        items = list(node.items())
        for i, (name, children) in enumerate(items):
            is_last_item = i == len(items) - 1
            connector = "└── " if is_last_item else "├── "
            print(f"{prefix}{connector}{name}")
            if children:
                extension = "    " if is_last_item else "│   "
                print_tree_recursive(children, prefix + extension, is_last_item)

    print_tree_recursive(tree)


def chatgpt_mode():
    print("[INFO] ChatGPT mode - Paste your ChatGPT response below")
    print("[INFO] Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) when done")
    print("=" * 60)

    lines = []
    try:
        while True:
            line = input()
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
FileGen v0.1.1 - File generator from Markdown

Usage:
    filegen <file.md>                    Create files from Markdown
    filegen --chatgpt                    Create files from ChatGPT response (paste content)
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
"""
    print(help_text)


def main():
    args = sys.argv[1:]

    if not args:
        print("[ERROR] No file specified")
        print("Usage: filegen <file.md>")
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