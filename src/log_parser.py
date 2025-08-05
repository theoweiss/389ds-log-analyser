# 389ds-log-analyser - A parser and query tool for 389 Directory Server access logs
# Copyright (C) 2024 Thomas Weiss <weiss@puzzle-itc.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import re
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# Import custom exceptions
try:
    from .exceptions import (
        LogParsingError, TimestampParsingError, InvalidLogFormatError,
        LogFileNotFoundError, LogFilePermissionError, FileOperationError
    )
except ImportError:
    from exceptions import (
        LogParsingError, TimestampParsingError, InvalidLogFormatError,
        LogFileNotFoundError, LogFilePermissionError, FileOperationError
    )

# Set up logging
logger = logging.getLogger(__name__)

# Regex to capture the timestamp and the rest of the message from a log line.
LOG_LINE_RE = re.compile(r'^\[(.*?)\] (.*)$')

# Regex to parse the timestamp string into its components.
# Example: 10/Jun/2025:20:50:45.194508+00:00 or 10/Jun/2025:20:50:45 Z
TIMESTAMP_RE = re.compile(
    r'(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})'  # DD/Mon/YYYY:HH:MM:SS
    r'(\.\d+)?'                                     # Optional fractional seconds
    r'\s*([Zz]|[+-]\d{4})$'                          # Timezone (Z, +HHMM, or -HHMM)
)

MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def parse_timestamp(ts_str: str, line_number: Optional[int] = None) -> Optional[datetime]:
    """
    Converts a raw timestamp string into a timezone-aware datetime object.
    
    Args:
        ts_str: The timestamp string to parse
        line_number: Optional line number for error reporting
        
    Returns:
        Parsed datetime object or None if parsing fails
        
    Raises:
        TimestampParsingError: If timestamp format is invalid
    """
    if not ts_str or not isinstance(ts_str, str):
        logger.debug(f"Invalid timestamp input: {repr(ts_str)}")
        return None
    
    try:
        match = TIMESTAMP_RE.match(ts_str.strip())
        if not match:
            logger.debug(f"Timestamp regex match failed for: {ts_str}")
            return None

        day, month_str, year, hour, minute, second, fractional, tz_str = match.groups()

        # Validate month
        month = MONTH_MAP.get(month_str.capitalize())
        if not month:
            raise TimestampParsingError(
                ts_str, 
                line_number=line_number,
                cause=ValueError(f"Invalid month: {month_str}")
            )

        # Parse fractional seconds
        microsecond = 0
        if fractional:
            try:
                # The fractional part includes the dot, e.g., ".123456"
                # Truncate or pad to 6 digits for microseconds.
                sec_frac_str = fractional[1:7]
                microsecond = int(sec_frac_str.ljust(6, '0'))
            except ValueError as e:
                logger.warning(f"Invalid fractional seconds in timestamp {ts_str}: {fractional}")
                # Continue without fractional seconds

        # Create base datetime
        try:
            dt = datetime(int(year), month, int(day), int(hour), int(minute), int(second), microsecond)
        except ValueError as e:
            raise TimestampParsingError(
                ts_str,
                line_number=line_number,
                cause=e
            )

        # Handle timezone
        if tz_str:
            try:
                if tz_str.upper() == 'Z':
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    # Parse offset like +0200 or -0500
                    if len(tz_str) != 5 or tz_str[0] not in '+-':
                        raise ValueError(f"Invalid timezone format: {tz_str}")
                    
                    offset_hours = int(tz_str[1:3])
                    offset_minutes = int(tz_str[3:5])
                    
                    if offset_hours > 23 or offset_minutes > 59:
                        raise ValueError(f"Invalid timezone offset: {tz_str}")
                    
                    offset_sign = -1 if tz_str[0] == '-' else 1
                    offset = timedelta(hours=offset_hours, minutes=offset_minutes) * offset_sign
                    dt = dt.replace(tzinfo=timezone(offset))
            except ValueError as e:
                raise TimestampParsingError(
                    ts_str,
                    line_number=line_number,
                    cause=e
                )
        else:
            # Default to UTC if no timezone is specified.
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
        
    except TimestampParsingError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise TimestampParsingError(
            ts_str,
            line_number=line_number,
            cause=e
        )

def parse_key_value_message(message: str, line_number: Optional[int] = None) -> Dict[str, Any]:
    """
    Parses a message string for key-value pairs, operation type, and extra text.
    It robustly handles logs where the operation type is mixed with key-value pairs.
    
    Args:
        message: The message part of the log line
        line_number: Optional line number for error reporting
        
    Returns:
        Dictionary containing parsed data
        
    Raises:
        LogParsingError: If message parsing fails critically
    """
    if not message or not isinstance(message, str):
        logger.debug(f"Invalid message input: {repr(message)}")
        return {'type': 'INFO', 'extra_text': message or ''}
    
    try:
        # This regex is the core of the message parsing.
        # It finds key-value pairs, where values can be unquoted, quoted, or numeric.
        kv_pattern = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
        data: Dict[str, Any] = {}
        
        # Find all k-v pairs and the text that is NOT a k-v pair
        last_end = 0
        non_kv_parts = []
        
        for match in kv_pattern.finditer(message):
            # Text before this match is a non-kv part
            non_kv_parts.append(message[last_end:match.start()])
            
            key = match.group(1)
            value = match.group(2)
            
            # Strip quotes from quoted values
            if value.startswith('"') and value.endswith('"'):
                try:
                    # Handle escaped quotes in quoted values
                    value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                except Exception as e:
                    logger.warning(f"Error processing quoted value {value}: {e}")
                    value = value[1:-1]  # Fallback to simple quote removal

            data[key] = value
            last_end = match.end()
        
        # Append any remaining text after the last k-v pair
        non_kv_parts.append(message[last_end:])
        
        # Join the non-k-v parts and clean them up. This is our "extra text".
        extra_text = " ".join(non_kv_parts).strip()
        
        # The first word of the extra text is likely the operation type (e.g., BIND, Disconnect).
        if extra_text:
            parts = extra_text.split(' ', 1)
            op_type = parts[0]
            
            # Handle cases like "Disconnect -"
            if op_type.endswith('-'):
                op_type = op_type[:-1].strip()

            # Map 'closed' to the canonical 'Disconnect' type
            if op_type == "closed":
                op_type = "Disconnect"

            if op_type in ["BIND", "RESULT", "SRCH", "UNBIND", "EXT", "Disconnect", "ADD", "DEL", "MOD", "MODRDN", "CMP"]:
                data['type'] = op_type
                # The rest of the text is stored as extra_text
                if len(parts) > 1:
                    data['extra_text'] = parts[1].lstrip('- ')
            else:
                # Not a known op_type, check for special informational text patterns
                conn_info_match = re.search(r'connection from (\S+) to (\S+)', extra_text)
                if conn_info_match:
                    data['type'] = 'CONNECTION_INFO'
                    data['source_ip'] = conn_info_match.group(1)
                    data['destination_ip'] = conn_info_match.group(2)
                    data['extra_text'] = extra_text
                else:
                    # Just generic info
                    data['type'] = 'INFO'
                    data['extra_text'] = extra_text
        else:
            # No extra text was found, so this is a log line with only key-value pairs.
            # We'll infer the type if possible, otherwise default to INFO.
            if 'err' in data and 'tag' in data and 'nentries' in data:
                 data['type'] = 'RESULT'
            else:
                 data['type'] = 'INFO'
        
        # Try to convert numeric-like strings to integers.
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    if value.isdigit():
                        data[key] = int(value)
                    elif value.startswith('-') and value[1:].isdigit():
                        data[key] = int(value)
                    elif '.' in value:
                        # Try to parse as float for timing values
                        try:
                            float_val = float(value)
                            # Only convert if it's a reasonable float (not too long)
                            if len(value) < 20:
                                data[key] = float_val
                        except ValueError:
                            pass  # Keep as string
                except ValueError as e:
                    logger.debug(f"Failed to convert {key}={value} to number: {e}")
                    # Keep original string value

        return data
        
    except Exception as e:
        # Log the error but don't fail completely
        logger.warning(f"Error parsing message (line {line_number}): {e}")
        logger.debug(f"Problematic message: {message[:200]}")
        
        # Return a basic structure to allow parsing to continue
        return {
            'type': 'INFO',
            'extra_text': message,
            'parse_error': str(e)
        }

def parse_log_line(line: str, line_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Parses a single log line into a structured dictionary.
    
    Args:
        line: The log line to parse
        line_number: Optional line number for error reporting
        
    Returns:
        Dictionary containing parsed data or None if line format is invalid
        
    Raises:
        InvalidLogFormatError: If the log line format is completely invalid
        TimestampParsingError: If timestamp parsing fails
    """
    if not line or not isinstance(line, str):
        return None
    
    line = line.strip()
    if not line:
        return None
    
    try:
        match = LOG_LINE_RE.match(line)
        if not match:
            logger.debug(f"Log line regex match failed (line {line_number}): {line[:100]}")
            return None

        timestamp_str, message_str = match.groups()

        # Parse timestamp - this may raise TimestampParsingError
        timestamp = parse_timestamp(timestamp_str, line_number)
        if not timestamp:
            logger.debug(f"Timestamp parsing failed (line {line_number}): {timestamp_str}")
            return None

        # Parse message - this handles its own errors gracefully
        parsed_message = parse_key_value_message(message_str, line_number)
        parsed_message['timestamp'] = timestamp
        
        return parsed_message
        
    except (TimestampParsingError, InvalidLogFormatError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.debug(f"Unexpected error parsing line {line_number}: {e}")
        return None

def validate_log_file(file_path: str) -> None:
    """
    Validates that a log file exists and is readable.
    
    Args:
        file_path: Path to the log file
        
    Raises:
        LogFileNotFoundError: If file doesn't exist
        LogFilePermissionError: If file isn't readable
        FileOperationError: For other file system errors
    """
    if not file_path:
        raise FileOperationError(
            "No file path provided",
            file_path="",
            operation="validate"
        )
    
    if not os.path.exists(file_path):
        raise LogFileNotFoundError(file_path)
    
    if not os.path.isfile(file_path):
        raise FileOperationError(
            f"Path is not a file: {file_path}",
            file_path=file_path,
            operation="validate",
            details="Path exists but is not a regular file (may be a directory or special file)"
        )
    
    if not os.access(file_path, os.R_OK):
        raise LogFilePermissionError(file_path)
    
    # Check if file is empty
    try:
        if os.path.getsize(file_path) == 0:
            logger.warning(f"Log file is empty: {file_path}")
    except OSError as e:
        raise FileOperationError(
            f"Cannot get file size: {file_path}",
            file_path=file_path,
            operation="validate",
            cause=e
        )

def main() -> None:
    """Main function for command-line usage of the log parser."""
    parser = argparse.ArgumentParser(description="Parse 389-ds access logs.")
    parser.add_argument("-f", "--file", help="Path to the log file to parse.")
    parser.add_argument("-l", "--line", help="A single log line to parse.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        if args.file:
            # Validate file first
            validate_log_file(args.file)
            
            line_count = 0
            parsed_count = 0
            error_count = 0
            
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    for line_number, line in enumerate(f, 1):
                        line_count += 1
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            parsed = parse_log_line(line, line_number)
                            if parsed:
                                parsed_count += 1
                                print(f"Line {line_number}: {parsed}")
                            else:
                                if args.debug:
                                    print(f"Line {line_number}: Failed to parse")
                        except (TimestampParsingError, InvalidLogFormatError) as e:
                            error_count += 1
                            print(f"Line {line_number}: Parse error - {e}")
                        except Exception as e:
                            error_count += 1
                            print(f"Line {line_number}: Unexpected error - {e}")
                            if args.debug:
                                logger.exception("Detailed error information:")
                
                print(f"\nSummary: Processed {line_count} lines, parsed {parsed_count}, errors: {error_count}")
                
            except UnicodeDecodeError as e:
                raise LogParsingError(
                    f"File encoding error in {args.file}",
                    details="File may not be UTF-8 encoded or may be corrupted",
                    cause=e
                )
            except OSError as e:
                raise FileOperationError(
                    f"Error reading file: {args.file}",
                    file_path=args.file,
                    operation="read",
                    cause=e
                )
                
        elif args.line:
            line = args.line.strip()
            if line:
                try:
                    parsed = parse_log_line(line)
                    if parsed:
                        print("Parsed successfully:")
                        print(parsed)
                    else:
                        print("Failed to parse line")
                except (TimestampParsingError, InvalidLogFormatError) as e:
                    print(f"Parse error: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    if args.debug:
                        logger.exception("Detailed error information:")
        else:
            parser.print_help()
            
    except (LogFileNotFoundError, LogFilePermissionError, FileOperationError, LogParsingError) as e:
        print(f"Error: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.debug:
            logger.exception("Detailed error information:")
        exit(1)

if __name__ == "__main__":
    main()
