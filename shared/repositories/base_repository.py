"""Base repository for JSON data operations.

This module provides an abstract base class for data access operations
with consistent error handling and file I/O patterns.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from shared.utils.path_utils import ensure_parent_directory


class BaseRepository(ABC):
    """Abstract base class for JSON-based data repositories."""

    def __init__(self, base_path: str):
        """Initialize the repository.

        Args:
            base_path: Base directory path for data storage
        """
        self.base_path = base_path

    def save(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Save data to JSON file.

        Args:
            filepath: Full path to save file
            data: Dictionary to save as JSON

        Returns:
            True if successful, False otherwise
        """
        try:
            ensure_parent_directory(filepath)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving file {filepath}: {str(e)}")
            return False

    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file.

        Args:
            filepath: Full path to load file

        Returns:
            Dictionary with file contents, or None if error
        """
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading file {filepath}: {str(e)}")
            return None

    def exists(self, filepath: str) -> bool:
        """Check if a file exists.

        Args:
            filepath: Full path to check

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(filepath)

    def delete(self, filepath: str) -> bool:
        """Delete a file.

        Args:
            filepath: Full path to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filepath}: {str(e)}")
            return False

    def list_all_files(self, directory: str, extension: str = ".json") -> List[str]:
        """List all files in a directory with a specific extension.

        Args:
            directory: Directory to search
            extension: File extension to filter (default: .json)

        Returns:
            List of file paths
        """
        if not os.path.exists(directory):
            return []

        try:
            files = []
            for filename in os.listdir(directory):
                if filename.endswith(extension):
                    files.append(os.path.join(directory, filename))
            return sorted(files)
        except Exception as e:
            print(f"Error listing files in {directory}: {str(e)}")
            return []

    def list_subdirectories(self, directory: str) -> List[str]:
        """List all subdirectories in a directory.

        Args:
            directory: Directory to search

        Returns:
            List of subdirectory names (not full paths)
        """
        if not os.path.exists(directory):
            return []

        try:
            return sorted([
                d for d in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, d))
            ])
        except Exception as e:
            print(f"Error listing subdirectories in {directory}: {str(e)}")
            return []
