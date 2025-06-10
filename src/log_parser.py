import argparse
from lark import Lark, Transformer, v_args
from datetime import datetime, timezone, timedelta

log_grammar = r"""
    ?start: log_line

    log_line: timestamped_log | misc_info_log

    timestamped_log: _LBRACKET timestamp _RBRACKET log_body

    log_body: conn_op_log | conn_only_log | conn_log_line

    conn_op_log: _CONN_EQ INT _OP_EQ INT ( (OPERATION_TYPE data_pairs (extra_text)?) | op_info )

    conn_only_log: _CONN_EQ INT conn_info
    conn_log_line: _DASH conn_info

    misc_info_log: any_text_tokens


    
    op_info: any_text_tokens
    conn_info: any_text_tokens

    any_text_tokens: (WORD | CNAME | SIGNED_NUMBER | QUOTED_STRING | _DASH | _EQ | "/" | "." | ":" | "(" | ")" | ",")+

    extra_text: _DASH any_text_tokens

    data_pairs: (data_pair)*
    data_pair: KEY _EQ value
    value: QUOTED_STRING | unquoted_value
    unquoted_value: (SIGNED_NUMBER | WORD)+

    KEY: CNAME

    timestamp: DAY "/" MONTH "/" YEAR ":" HOUR ":" MINUTE ":" SECOND (_DOT INT)? (Z | TIMEZONE)

    _LBRACKET: "["
    _RBRACKET: "]"
    _CONN_EQ: "conn="
    _OP_EQ: "op="
    _EQ: "="
    _DASH: "-"
    _DOT: "."

    OPERATION_TYPE.2: "BIND" | "RESULT" | "SRCH" | "UNBIND"

    %import common.WORD
    %import common.CNAME
    %import common.INT
    QUOTED_STRING: /"[^"]*"/
    %import common.SIGNED_NUMBER
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
"""

@v_args(inline=True)
class LogTransformer(Transformer):
    def log_line(self, line):
        return line

    def timestamped_log(self, timestamp, log_body):
        if log_body:
            log_body['timestamp'] = timestamp
        return log_body

    def log_body(self, data):
        return data

    def conn_op_log(self, conn, op, *args):
        first_arg = args[0]
        # Check if the first argument is a recognized OPERATION_TYPE
        if str(first_arg) in ("BIND", "RESULT", "SRCH", "UNBIND"):
            # This is conn_op_log_structured
            operation_type, data_pairs, *rest = args
            extra_text = rest[0] if rest else None
            result = {
                "conn": int(conn),
                "op": int(op),
                "type": str(operation_type),
                "data": data_pairs, # FIX: data_pairs is already a dict
            }
            if extra_text:
                result["extra_text"] = extra_text
            return result
        else:
            # This is conn_op_log_info
            op_info = first_arg
            return {"conn": int(conn), "op": int(op), "type": "INFO", "data": str(op_info).strip()}

    def conn_only_log(self, conn, conn_info):
        return {"conn": int(conn), "type": "INFO", "data": str(conn_info).strip()}

    def conn_log_line(self, conn_info):
        return {"type": "INFO", "data": str(conn_info).strip()}

    def misc_info_log(self, text):
        return {"type": "INFO", "data": str(text).strip()}

    def op_info(self, text):
        return str(text).strip()

    def conn_info(self, text):
        return str(text).strip()

    def any_text_tokens(self, *items):
        return " ".join(str(i).strip('"') for i in items)



    def extra_text(self, text):
        return str(text).strip()

    def data_pairs(self, *pairs):
        return dict(pairs)

    def data_pair(self, key, value):
        return (str(key), value)

    def unquoted_value(self, *items):
        if len(items) == 1:
            item_value = str(items[0])
            try:
                return int(item_value)
            except ValueError:
                try:
                    return float(item_value)
                except ValueError:
                    return item_value
        return " ".join(str(i) for i in items)

    def value(self, v):
        if hasattr(v, 'type') and v.type == 'QUOTED_STRING':
            return v[1:-1]
        return v

    def KEY(self, k):
        return str(k)

    def OPERATION_TYPE(self, op_type):
        return str(op_type)

    def timestamp(self, *args):
        day, month, year, hour, minute, second = args[:6]
        
        if len(args) == 7:
            nano = None
            zone = args[6]
        elif len(args) == 8:
            nano = args[6]
            zone = args[7]
        else:
            # This case should not happen based on the grammar
            nano = None
            zone = None

        month_map = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }
        month_num = month_map[month]
        
        nanosecond = int(str(nano).ljust(9, '0')) if nano else 0

        tz = timezone.utc
        if zone:
            if zone == "Z":
                pass # tz is already UTC
            else:
                offset = int(zone)
                tz = timezone(timedelta(hours=offset // 100, minutes=offset % 100))

        return datetime(int(year), month_num, int(day), int(hour), int(minute), int(second), nanosecond // 1000, tzinfo=tz)

    def __default__(self, data, children, meta):
        return children if children else data

def parse_log_line(line, parser):
    try:
        return parser.parse(line)
    except Exception as e:
        return {"error": str(e), "line": line.strip()}

def main():
    arg_parser = argparse.ArgumentParser(description="Parse 389-ds access logs.")
    arg_parser.add_argument("-f", "--file", help="Path to the log file.", type=str)
    arg_parser.add_argument("-l", "--line", help="A single log line to parse.", type=str)
    args = arg_parser.parse_args()

    log_parser = Lark(log_grammar, parser="lalr", lexer="contextual")
    transformer = LogTransformer()

    def process_line(line):
        parsed = parse_log_line(line, log_parser)
        if isinstance(parsed, dict) and "error" in parsed:
            print(parsed)
        else:
            transformed = transformer.transform(parsed)
            print(transformed)

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                if line.strip():
                    process_line(line.strip())
    elif args.line:
        process_line(args.line.strip())
    else:
        print("Please provide a log file with -f or a log line with -l.")

if __name__ == "__main__":
    main()
