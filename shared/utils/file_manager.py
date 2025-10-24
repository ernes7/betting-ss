"""File I/O operations for JSON data."""

import json
from pathlib import Path
from typing import Any


class FileManager:
    """Manages file I/O operations for JSON data."""

    @staticmethod
    def save_json(filepath: str, data: dict, ensure_dir: bool = True):
        """Save data to JSON file.

        Args:
            filepath: Path to save the JSON file
            data: Dictionary data to save
            ensure_dir: Create parent directories if they don't exist
        """
        path = Path(filepath)
        if ensure_dir:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_json(filepath: str) -> dict[str, Any] | None:
        """Load JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            Dictionary data or None if file doesn't exist
        """
        path = Path(filepath)
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file {filepath}: {str(e)}")
            return None

    @staticmethod
    def load_all_json_in_dir(directory: str) -> dict[str, dict]:
        """Load all JSON files in a directory.

        Args:
            directory: Directory path to search

        Returns:
            Dictionary mapping filenames (without .json) to their contents
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Warning: Directory {directory} not found")
            return {}

        result = {}
        for json_file in dir_path.glob("*.json"):
            if json_file.name.startswith("."):  # Skip metadata files
                continue
            file_stem = json_file.stem
            data = FileManager.load_json(str(json_file))
            if data:
                result[file_stem] = data

        return result
