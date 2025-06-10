import argparse
from data_model import build_data_model

def print_src_ip_table(connections):
    """Prints a table of connections with source IP, bind, and unbind times."""
    print(f"{'Source IP':<20} {'Bind Timestamp':<35} {'Unbind Timestamp':<35}")
    print(f"{'--------------------':<20} {'-----------------------------------':<35} {'-----------------------------------':<35}")

    sorted_connections = sorted(
        [c for c in connections.values() if c.successful_bind and c.unbind_timestamp and c.bind_timestamp],
        key=lambda c: c.bind_timestamp
    )

    for conn in sorted_connections:
        source_ip = conn.source_ip or "N/A"
        bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
        unbind_time = conn.unbind_timestamp.isoformat() if conn.unbind_timestamp else "N/A"
        print(f"{source_ip:<20} {bind_time:<35} {unbind_time:<35}")

def print_open_connections_table(connections):
    """Prints a table of open connections with source IP, bind DN, and bind time."""
    print(f"{'Source IP':<20} {'Bind DN':<50} {'Bind Timestamp':<35}")
    print(f"{'--------------------':<20} {'--------------------------------------------------':<50} {'-----------------------------------':<35}")

    sorted_connections = sorted(
        [c for c in connections.values() if c.successful_bind and c.unbind_timestamp is None],
        key=lambda c: c.bind_timestamp
    )

    for conn in sorted_connections:
        source_ip = conn.source_ip or "N/A"
        bind_dn = conn.bind_dn or "N/A"
        bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
        print(f"{source_ip:<20} {bind_dn:<50} {bind_time:<35}")

def print_unique_clients(connections):
    """Prints a unique list of all client source IPs."""
    print("Unique Client IPs")
    print("-----------------")
    
    unique_ips = sorted(list(set(c.source_ip for c in connections.values() if c.source_ip)))
    
    for ip in unique_ips:
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

def main():
    parser = argparse.ArgumentParser(description='Parse 389-ds access logs and query connection data.')
    parser.add_argument('-f', '--file', required=True, help='Path to the log file.')
    parser.add_argument('--query', choices=['src_ip_table', 'open_connections', 'unique_clients', 'unindexed_searches'], help='The query to run on the log data.')
    parser.add_argument('--debug', action='store_true', help='Enable debug output for parsing errors.')
    args = parser.parse_args()

    connections = build_data_model(args.file, args.debug)

    if args.query == 'src_ip_table':
        print_src_ip_table(connections)
    elif args.query == 'open_connections':
        print_open_connections_table(connections)
    elif args.query == 'unique_clients':
        print_unique_clients(connections)
    elif args.query == 'unindexed_searches':
        print_unindexed_searches_table(connections)

if __name__ == '__main__':
    main()
