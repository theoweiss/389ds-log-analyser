import argparse
import re
from datetime import datetime, timezone, timedelta

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

def parse_timestamp(ts_str):
    """Converts a raw timestamp string into a timezone-aware datetime object."""
    match = TIMESTAMP_RE.match(ts_str)
    if not match:
        return None

    day, month_str, year, hour, minute, second, fractional, tz_str = match.groups()

    month = MONTH_MAP.get(month_str.capitalize())
    if not month:
        return None

    microsecond = 0
    if fractional:
        # The fractional part includes the dot, e.g., ".123456"
        # Truncate or pad to 6 digits for microseconds.
        sec_frac_str = fractional[1:7]
        microsecond = int(sec_frac_str.ljust(6, '0'))

    dt = datetime(int(year), month, int(day), int(hour), int(minute), int(second), microsecond)

    if tz_str:
        if tz_str.upper() == 'Z':
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            offset_hours = int(tz_str[1:3])
            offset_minutes = int(tz_str[3:5])
            offset_sign = -1 if tz_str[0] == '-' else 1
            offset = timedelta(hours=offset_hours, minutes=offset_minutes) * offset_sign
            dt = dt.replace(tzinfo=timezone(offset))
    else:
        # Default to UTC if no timezone is specified.
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt

def parse_key_value_message(message):
    """
    Parses a message string for key-value pairs, operation type, and extra text.
    It robustly handles logs where the operation type is mixed with key-value pairs.
    """
    # This regex is the core of the message parsing.
    # It finds key-value pairs, where values can be unquoted, quoted, or numeric.
    kv_pattern = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
    data = {}
    
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
            value = value[1:-1]

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

        if op_type in ["BIND", "RESULT", "SRCH", "UNBIND", "EXT", "Disconnect", "ADD", "DEL"]:
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
            if value.isdigit():
                data[key] = int(value)
            elif value.startswith('-') and value[1:].isdigit():
                data[key] = int(value)

    return data

def parse_log_line(line):
    """
    Parses a single log line into a structured dictionary.
    Returns None if the line format is invalid.
    """
    match = LOG_LINE_RE.match(line)
    if not match:
        return None

    timestamp_str, message_str = match.groups()

    timestamp = parse_timestamp(timestamp_str)
    if not timestamp:
        return None # Failed to parse timestamp

    parsed_message = parse_key_value_message(message_str)
    parsed_message['timestamp'] = timestamp
    
    return parsed_message

def main():
    parser = argparse.ArgumentParser(description="Parse 389-ds access logs.")
    parser.add_argument("-f", "--file", help="Path to the log file to parse.")
    parser.add_argument("-l", "--line", help="A single log line to parse.")
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = parse_log_line(line)
                    if parsed:
                        print(parsed)
                except Exception as e:
                    print(f"Error parsing line: {line}\n{e}")
    elif args.line:
        line = args.line.strip()
        if line:
            try:
                parsed = parse_log_line(line)
                if parsed:
                    print(parsed)
            except Exception as e:
                print(f"Error parsing line: {line}\n{e}")

if __name__ == "__main__":
    main()
