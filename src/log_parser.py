import argparse
import re
from lark import Lark, Transformer, v_args
from datetime import datetime, timezone, timedelta

# A much simpler grammar that only extracts the core components.
# The detailed key-value parsing is handled in Python.
log_grammar = r"""
    ?start: log_line

    log_line: "[" timestamp "]" message

    message: /.+/

    timestamp: DAY "/" MONTH "/" YEAR ":" HOUR ":" MINUTE ":" SECOND FRACTIONAL? (Z | TIMEZONE)

    FRACTIONAL: /\.\d+/

    %import common.INT
    %import common.WS
    %ignore WS

    DAY: INT
    MONTH: WORD
    YEAR: INT
    HOUR: INT
    MINUTE: INT
    SECOND: INT
    TIMEZONE: /[+-]\d{4}/
    Z: "Z"
    %import common.WORD
"""

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

@v_args(inline=True)
class LogTransformer(Transformer):
    def log_line(self, timestamp, message):
        parsed_message = parse_key_value_message(str(message))
        parsed_message['timestamp'] = timestamp
        return parsed_message

    def message(self, *parts):
        return " ".join(str(p) for p in parts)

    def timestamp(self, day, month_str, year, hour, minute, second, fractional=None, tz=None):
        """Converts parsed timestamp parts into a datetime object."""
        month = int(datetime.strptime(month_str, '%b').month)
        
        microsecond = 0
        if fractional:
            # The fractional part includes the dot, e.g., ".123456789"
            # We need to truncate to 6 digits for microseconds.
            sec_frac_str = fractional[1:7]
            microsecond = int(sec_frac_str.ljust(6, '0'))

        dt = datetime(int(year), month, int(day), int(hour), int(minute), int(second), microsecond)

        if tz:
            if tz == 'Z':
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                offset_hours = int(tz[1:3])
                offset_minutes = int(tz[3:5])
                offset_sign = -1 if tz[0] == '-' else 1
                offset = timedelta(hours=offset_hours, minutes=offset_minutes) * offset_sign
                dt = dt.replace(tzinfo=timezone(offset))
        else:
            # Per RFCs, if timezone is not specified, it should be treated as local time.
            # However, in the context of server logs, assuming UTC is a safer default.
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

def main():
    parser = argparse.ArgumentParser(description="Parse 389-ds access logs.")
    parser.add_argument("-f", "--file", help="Path to the log file to parse.")
    parser.add_argument("-l", "--line", help="A single log line to parse.")
    args = parser.parse_args()

    log_parser = Lark(log_grammar, parser='lalr', transformer=LogTransformer())

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                try:
                    parsed = log_parser.parse(line.strip())
                    print(parsed)
                except Exception as e:
                    print(f"Error parsing line: {line.strip()}\n{e}")
    elif args.line:
        try:
            parsed = log_parser.parse(args.line.strip())
            print(parsed)
        except Exception as e:
            print(f"Error parsing line: {args.line.strip()}\n{e}")

if __name__ == "__main__":
    main()
