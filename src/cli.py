import argparse
import socket
import sys
from data_model import build_data_model

# Cache for hostname resolution to avoid repeated lookups
hostname_cache = {}

def print_src_ip_table(connections, resolve_hostnames=False):
    """Prints a table of connections with source IP, bind, and unbind times."""
    print(f"{'Source IP':<20} {'Bind Timestamp':<35} {'Unbind Timestamp':<35}")
    print(f"{'--------------------':<20} {'-----------------------------------':<35} {'-----------------------------------':<35}")

    sorted_connections = sorted(
        [c for c in connections.values() if c.successful_bind and c.unbind_timestamp and c.bind_timestamp],
        key=lambda c: c.bind_timestamp
    )

    for conn in sorted_connections:
        source_ip = conn.source_ip or "N/A"
        if resolve_hostnames:
            source_ip = resolve_hostname(source_ip)
        bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
        unbind_time = conn.unbind_timestamp.isoformat() if conn.unbind_timestamp else "N/A"
        print(f"{source_ip:<20} {bind_time:<35} {unbind_time:<35}")

def print_open_connections_table(connections, resolve_hostnames=False):
    """Prints a table of open connections with source IP, bind DN, and bind time."""
    print(f"{'Source IP':<20} {'Bind DN':<50} {'Bind Timestamp':<35}")
    print(f"{'--------------------':<20} {'--------------------------------------------------':<50} {'-----------------------------------':<35}")

    sorted_connections = sorted(
        [c for c in connections.values() if c.successful_bind and c.unbind_timestamp is None],
        key=lambda c: c.bind_timestamp
    )

    for conn in sorted_connections:
        source_ip = conn.source_ip or "N/A"
        if resolve_hostnames:
            source_ip = resolve_hostname(source_ip)
        bind_dn = conn.bind_dn or "N/A"
        bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
        print(f"{source_ip:<20} {bind_dn:<50} {bind_time:<35}")

def print_unique_clients(connections, resolve_hostnames=False):
    """Prints a unique list of all client source IPs."""
    print("Unique Client IPs")
    print("-----------------")
    
    unique_ips = sorted(list(set(c.source_ip for c in connections.values() if c.source_ip)))
    
    for ip in unique_ips:
        if resolve_hostnames:
            ip = resolve_hostname(ip)
        print(ip)

def print_unindexed_searches_table(connections):
    """Prints a table of partially unindexed searches."""
    print(f"{'Timestamp':<35} {'Conn':<10} {'Op':<10} {'Base':<30} {'Filter'}")
    print(f"{'-----------------------------------':<35} {'----------':<10} {'----------':<10} {'------------------------------':<30} {'-'*40}")

    unindexed_searches = []
    for conn in connections.values():
        for op in conn.operations.values():
            if op.op_type == 'SRCH' and op.result and op.result.get('details') == 'Partially Unindexed Filter':
                unindexed_searches.append((op.timestamp, conn.conn_num, op.op_num, op.data.get('base', 'N/A'), op.data.get('filter', 'N/A')))

    unindexed_searches.sort(key=lambda x: x[0])

    for ts, conn_num, op_num, base, sfilter in unindexed_searches:
        print(f"{ts.isoformat():<35} {conn_num:<10} {op_num:<10} {base:<30} {sfilter}")

def resolve_hostname(ip_address):
    """Resolves an IP address to a hostname, with caching."""
    if ip_address in hostname_cache:
        return hostname_cache[ip_address]
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        hostname_cache[ip_address] = hostname
        return hostname
    except (socket.herror, socket.gaierror):
        # If resolution fails, cache and return the original IP
        hostname_cache[ip_address] = ip_address
        return ip_address

def main():
    # Parent parser for common arguments that all subcommands will use
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-f', '--file', required=True, help='Path to the log file.')
    parent_parser.add_argument('--debug', action='store_true', help='Enable debug output for parsing errors.')
    parent_parser.add_argument(
        '--filter-client-ip',
        nargs='+',
        metavar='IP_ADDRESS',
        help='Filter output by one or more client IP addresses.'
    )
    parent_parser.add_argument(
        '--resolve-hostnames',
        action='store_true',
        help='Resolve IP addresses to hostnames. This may slow down the query.'
    )

    # Main parser
    parser = argparse.ArgumentParser(description='Analyze 389-ds access logs.')
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # src_ip_table command
    parser_src_ip = subparsers.add_parser(
        'src-ip-table',
        help='Display a table of completed connections with source IP and timestamps.',
        parents=[parent_parser]
    )
    parser_src_ip.set_defaults(func=print_src_ip_table)

    # open_connections command
    parser_open = subparsers.add_parser(
        'open-connections',
        help='Display a table of connections that are still open.',
        parents=[parent_parser]
    )
    parser_open.set_defaults(func=print_open_connections_table)

    # unique_clients command
    parser_unique = subparsers.add_parser(
        'unique-clients',
        help='Display a unique list of all client source IPs.',
        parents=[parent_parser]
    )
    parser_unique.set_defaults(func=print_unique_clients)

    # unindexed_searches command
    parser_unindexed = subparsers.add_parser(
        'unindexed-searches',
        help='Display a table of unindexed searches.',
        parents=[parent_parser]
    )
    parser_unindexed.set_defaults(func=print_unindexed_searches_table)

    args = parser.parse_args()

    connections = build_data_model(args.file, args.debug)

    if args.filter_client_ip:
        connections = {
            conn_num: conn for conn_num, conn in connections.items()
            if conn.source_ip in args.filter_client_ip
        }

    filtered_connections = connections

    if args.command == 'src-ip-table':
        print_src_ip_table(filtered_connections, args.resolve_hostnames)
    elif args.command == 'open-connections':
        print_open_connections_table(filtered_connections, args.resolve_hostnames)
    elif args.command == 'unique-clients':
        print_unique_clients(filtered_connections, args.resolve_hostnames)
    elif args.command == 'unindexed-searches':
        print_unindexed_searches_table(filtered_connections)

if __name__ == '__main__':
    main()


def main_src_ip_table():
    sys.argv.insert(1, 'src-ip-table')
    main()


def main_open_connections():
    sys.argv.insert(1, 'open-connections')
    main()


def main_unique_clients():
    sys.argv.insert(1, 'unique-clients')
    main()


def main_unindexed_searches():
    sys.argv.insert(1, 'unindexed-searches')
    main()

