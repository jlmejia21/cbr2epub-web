"""Utility functions for CBR to EPUB conversion."""
import os
import re
import hashlib


def sanitize_filename(filename):
    """Remove invalid characters from filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def natural_sort_key(filename):
    """Generate sort key for natural sorting (handles numbers in filenames)."""
    parts = re.split(r'(\d+)', filename.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def sort_pages_filenames(filenames):
    """Sort page filenames using natural ordering."""
    return sorted(filenames, key=natural_sort_key)


def get_file_extension(filepath):
    """Get lowercase file extension."""
    return os.path.splitext(filepath)[1].lower()


def file_exists(filepath):
    """Check if file exists and is readable."""
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)


def get_file_size_kb(filepath):
    """Get file size in KB."""
    return os.path.getsize(filepath) // 1024


def calculate_file_hash(filepath, algorithm='md5'):
    """Calculate file hash for integrity verification."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def ensure_dir_exists(directory):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)