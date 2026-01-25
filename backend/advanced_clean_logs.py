#!/usr/bin/env python3
"""Log file cleaning utility for eNSP console logs.

Removes duplicates, fixes character doubling, and normalizes text
for better AI analysis.
"""

import re
from pathlib import Path
from typing import List, Dict, Set
import sys


def clean_and_normalize_text(text: str) -> str:
    """Clean text by removing control characters and normalizing."""
    try:
        # First try to evaluate if it's a Python string literal (from repr)
        if text.startswith(("'", '"')):
            try:
                text = ast.literal_eval(text)
            except:
                # If that fails, remove quotes manually
                if text.startswith("'") and text.endswith("'"):
                    text = text[1:-1]
                elif text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
    except:
        pass
    
    # Remove ANSI escape sequences (including \x1b[A type)
    text = re.sub(r'\\x1b\[[0-9;]*[A-Za-z]', '', text)
    text = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
    
    # Remove bell characters and other control chars
    text = re.sub(r'\\x07', '', text)
    text = re.sub(r'\x07', '', text)
    text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)  # Other hex escapes
    
    # Normalize line endings
    text = text.replace('\\r\\n', '\n').replace('\\r', '\n').replace('\\n', '\n')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def detect_and_fix_doubling(text: str) -> str:
    """Detect and fix character/word doubling in text."""
    if not text:
        return text
    
    # Handle character-by-character doubling (like "ddiissppllaayy")
    if len(text) >= 4:
        # Check if every character is doubled
        if len(text) % 2 == 0:
            is_char_doubled = True
            for i in range(0, len(text), 2):
                if i + 1 >= len(text) or text[i] != text[i + 1]:
                    is_char_doubled = False
                    break
            
            if is_char_doubled:
                # Remove doubling
                result = ''.join(text[i] for i in range(0, len(text), 2))
                return result
    
    # Handle word/phrase doubling
    words = text.split()
    if len(words) >= 2 and len(words) % 2 == 0:
        mid = len(words) // 2
        first_half = words[:mid]
        second_half = words[mid:]
        if first_half == second_half:
            return ' '.join(first_half)
    
    # Handle sentence/line doubling
    if len(text) >= 20:  # Only check longer texts
        mid = len(text) // 2
        # Look for a natural break point near the middle
        for offset in range(-10, 11):
            split_pos = mid + offset
            if 0 < split_pos < len(text):
                first_part = text[:split_pos].strip()
                second_part = text[split_pos:].strip()
                if first_part == second_part and first_part:
                    return first_part
    
    return text


def is_meaningful_content(text: str) -> bool:
    """Check if the text contains meaningful content (not just whitespace/control chars)."""
    if not text:
        return False
    
    # Remove common whitespace and control characters
    cleaned = re.sub(r'[\s\r\n\t]+', '', text)
    return len(cleaned) > 0


def is_router_prompt(text: str) -> bool:
    """Detect router prompts like <R1>, [R1], R1>, R1#."""
    text = text.strip()
    if not text:
        return False
    
    # Common router prompt patterns
    patterns = [
        r'^<[^>]+>$',  # <R1>
        r'^<[^>]+>.*$',  # <R1> with trailing text
        r'^\[[^\]]+\]$',  # [R1]
        r'^[A-Za-z][A-Za-z0-9\-_]*[>#]$',  # R1>, R1#
        r'^[A-Za-z][A-Za-z0-9\-_]*[>#]\s*$',  # R1> with whitespace
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    
    return False


def clean_log_file_advanced(input_path: Path, output_path: Path = None) -> None:
    """Advanced cleaning of log files."""
    if output_path is None:
        output_path = input_path.with_suffix('.clean.log')
    
    print(f"Processing {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return
    
    lines = content.split('\n')
    cleaned_lines = []
    seen_lines = set()
    last_prompt = ""
    consecutive_prompt_count = 0
    
    stats = {
        'original': len(lines),
        'empty_removed': 0,
        'duplicates_removed': 0,
        'doubled_text_fixed': 0,
        'prompts_deduplicated': 0,
    }
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            stats['empty_removed'] += 1
            continue
        
        # Parse log line format: [timestamp] [device] direction content
        match = re.match(r'\[([^\]]+)\]\s*\[([^\]]+)\]\s*([←→])\s*(.+)$', line)
        if not match:
            # Keep malformed lines as-is for now
            cleaned_lines.append(line)
            continue
        
        timestamp, device, direction, content = match.groups()
        
        # Clean and normalize the content
        original_content = content
        cleaned_content = clean_and_normalize_text(content)
        
        # Fix character/text doubling
        undoubled_content = detect_and_fix_doubling(cleaned_content)
        if undoubled_content != cleaned_content:
            stats['doubled_text_fixed'] += 1
            cleaned_content = undoubled_content
        
        # Skip if no meaningful content remains
        if not is_meaningful_content(cleaned_content):
            stats['empty_removed'] += 1
            continue
        
        # Create a signature for duplicate detection
        signature = f"{device}|{direction}|{cleaned_content.lower()}"
        
        # Handle duplicate prompts specially
        if is_router_prompt(cleaned_content):
            if cleaned_content == last_prompt:
                consecutive_prompt_count += 1
                if consecutive_prompt_count >= 2:  # Allow max 1 duplicate prompt
                    stats['prompts_deduplicated'] += 1
                    continue
            else:
                last_prompt = cleaned_content
                consecutive_prompt_count = 0
        else:
            consecutive_prompt_count = 0
            last_prompt = ""
        
        # General duplicate detection
        if signature in seen_lines:
            stats['duplicates_removed'] += 1
            continue
        
        seen_lines.add(signature)
        
        # Reconstruct the cleaned line
        cleaned_line = f"[{timestamp}] [{device}] {direction} '{cleaned_content}'"
        cleaned_lines.append(cleaned_line)
    
    # Write the cleaned content
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in cleaned_lines:
                f.write(line + '\n')
        
        stats['cleaned'] = len(cleaned_lines)
        total_removed = stats['original'] - stats['cleaned']
        reduction_percent = (total_removed / stats['original'] * 100) if stats['original'] > 0 else 0
        
        print(f"  Original lines: {stats['original']}")
        print(f"  Cleaned lines:  {stats['cleaned']}")
        print(f"  Reduction:      {reduction_percent:.1f}%")
        print(f"  - Empty removed: {stats['empty_removed']}")
        print(f"  - Duplicates removed: {stats['duplicates_removed']}")
        print(f"  - Doubled text fixed: {stats['doubled_text_fixed']}")
        print(f"  - Prompts deduplicated: {stats['prompts_deduplicated']}")
        
        if output_path != input_path:
            print(f"  → Cleaned file: {output_path}")
        else:
            print(f"  → Updated in place")
        
    except Exception as e:
        print(f"Error writing {output_path}: {e}")


def main():
    log_dir = Path("data/logs")
    if not log_dir.exists():
        print(f"Log directory not found: {log_dir}")
        return
    
    # Find all .log files (but not .clean.log files)
    log_files = [f for f in log_dir.glob("*.log") if not f.name.endswith('.clean.log')]
    
    if not log_files:
        print("No log files found")
        return
    
    print(f"Found {len(log_files)} log files to clean")
    print()
    
    for log_file in log_files:
        clean_log_file_advanced(log_file, log_file.with_suffix('.clean.log'))
        print()
    
    print("Log cleaning completed!")
    print("\nOriginal files preserved. Clean versions saved with .clean.log extension.")
    print("To use the clean versions, you can rename them or update your processing code.")


if __name__ == "__main__":
    main()