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
import argcomplete
import socket
import sys
import os
import logging
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Optional, Dict, Any, List

# Import custom exceptions
from exceptions import (
    LogAnalyserError, LogFileNotFoundError,
    LogFilePermissionError, DataModelFileError, ValidationError,
    InvalidArgumentError, ConnectionNotFoundError, NetworkOperationError,
    HostnameResolutionError, DataModelError, EmptyLogFileError
)

from data_model import LogDataModel, build_data_model

# Set up logging
logger = logging.getLogger(__name__)

# Cache for hostname resolution to avoid repeated lookups
hostname_cache: Dict[str, str] = {}

def setup_logging(debug: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def validate_file_path(file_path: str, must_exist: bool = True) -> str:
    """
    Validate a file path argument.
    
    Args:
        file_path: The file path to validate
        must_exist: Whether the file must already exist
        
    Returns:
        The validated file path
        
    Raises:
        InvalidArgumentError: If the file path is invalid
    """
    if not file_path:
        raise InvalidArgumentError(
            "file",
            file_path,
            "File path cannot be empty",
            suggestion="Provide a valid file path"
        )
    
    if must_exist:
        if not os.path.exists(file_path):
            raise LogFileNotFoundError(file_path)
        
        if not os.path.isfile(file_path):
            raise InvalidArgumentError(
                "file",
                file_path,
                "Path is not a regular file",
                suggestion="Provide a path to a regular file, not a directory"
            )
        
        if not os.access(file_path, os.R_OK):
            raise LogFilePermissionError(file_path)
    
    return file_path

def validate_connection_id(conn_id: int, available_connections: Dict[int, Any]) -> int:
    """
    Validate a connection ID argument.
    
    Args:
        conn_id: The connection ID to validate
        available_connections: Dictionary of available connections
        
    Returns:
        The validated connection ID
        
    Raises:
        ConnectionNotFoundError: If connection ID is not found
    """
    if conn_id not in available_connections:
        raise ConnectionNotFoundError(
            conn_id,
            available_connections=list(available_connections.keys())
        )
    
    return conn_id

def validate_ip_addresses(ip_addresses: List[str]) -> List[str]:
    """
    Validate IP address arguments.
    
    Args:
        ip_addresses: List of IP addresses to validate
        
    Returns:
        List of validated IP addresses
        
    Raises:
        InvalidArgumentError: If any IP address is invalid
    """
    import ipaddress
    
    validated_ips = []
    for ip in ip_addresses:
        try:
            # This will raise ValueError for invalid IPs
            ipaddress.ip_address(ip)
            validated_ips.append(ip)
        except ValueError:
            # Allow special values like "local"
            if ip.lower() in ['local', 'localhost']:
                validated_ips.append(ip)
            else:
                raise InvalidArgumentError(
                    "filter-client-ip",
                    ip,
                    "Invalid IP address format",
                    suggestion="Provide a valid IPv4 or IPv6 address"
                )
    
    return validated_ips

def validate_operation_types(op_type_filter: str) -> tuple[List[str], List[str]]:
    """
    Validate operation type filter argument.
    
    Args:
        op_type_filter: Operation type filter string (e.g., "ADD,SRCH" or "!BIND")
        
    Returns:
        Tuple of (include_types, exclude_types) lists
        
    Raises:
        InvalidArgumentError: If any operation type is invalid
    """
    # Valid operation types based on log_parser.py
    valid_op_types = {"BIND", "RESULT", "SRCH", "UNBIND", "EXT", "Disconnect", "ADD", "DEL", "MOD", "MODRDN", "CMP"}
    
    include_types = []
    exclude_types = []
    
    # Split by comma and process each type
    for op_type in op_type_filter.split(','):
        op_type = op_type.strip()
        
        if not op_type:
            continue
            
        # Check for negation
        if op_type.startswith('!'):
            op_type_clean = op_type[1:].strip()
            if not op_type_clean:
                raise InvalidArgumentError(
                    "filter-op-type",
                    op_type,
                    "Empty operation type after negation",
                    suggestion="Provide a valid operation type after '!', e.g., '!BIND'"
                )
            
            if op_type_clean not in valid_op_types:
                raise InvalidArgumentError(
                    "filter-op-type",
                    op_type_clean,
                    "Invalid operation type",
                    suggestion=f"Valid types: {', '.join(sorted(valid_op_types))}"
                )
            
            exclude_types.append(op_type_clean)
        else:
            if op_type not in valid_op_types:
                raise InvalidArgumentError(
                    "filter-op-type",
                    op_type,
                    "Invalid operation type",
                    suggestion=f"Valid types: {', '.join(sorted(valid_op_types))}"
                )
            
            include_types.append(op_type)
    
    # Validate that we don't have conflicting include/exclude for the same type
    conflicting = set(include_types) & set(exclude_types)
    if conflicting:
        raise InvalidArgumentError(
            "filter-op-type",
            op_type_filter,
            f"Conflicting include/exclude for operation types: {', '.join(conflicting)}",
            suggestion="Either include or exclude a type, but not both"
        )
    
    return include_types, exclude_types

def get_display_ip(conn: Any, resolve_hostnames: bool = False) -> str:
    """Gets the display string for a connection's source IP, using hostname if available/requested."""
    if resolve_hostnames:
        # Use persisted hostname if available
        if conn.source_hostname:
            return conn.source_hostname
        # Otherwise, resolve the IP (uses cache)
        if conn.source_ip:
            try:
                return resolve_hostname(conn.source_ip)
            except HostnameResolutionError:
                # Fall back to IP address if resolution fails
                return conn.source_ip or "N/A"
    return conn.source_ip or "N/A"

def print_src_ip_table(connections: Dict[int, Any], resolve_hostnames: bool = False) -> None:
    """Prints a table of completed connections with source IP and timestamps."""
    try:
        print(f"{'Source IP/Hostname':<40} {'Bind Timestamp':<35} {'Unbind Timestamp':<35}")
        print(f"{'----------------------------------------':<40} {'-----------------------------------':<35} {'-----------------------------------':<35}")

        completed_connections = [
            c for c in connections.values() 
            if c.successful_bind and c.unbind_timestamp is not None
        ]
        
        if not completed_connections:
            print("No completed connections found.")
            return

        # Sort by bind timestamp
        completed_connections.sort(key=lambda c: c.bind_timestamp or c.unbind_timestamp)

        for conn in completed_connections:
            try:
                display_name = get_display_ip(conn, resolve_hostnames)
                bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
                unbind_time = conn.unbind_timestamp.isoformat() if conn.unbind_timestamp else "N/A"
                print(f"{display_name:<40} {bind_time:<35} {unbind_time:<35}")
            except Exception as e:
                logger.warning(f"Error displaying connection {conn.conn_num}: {e}")
                continue

        print(f"\nTotal completed connections: {len(completed_connections)}")
        
    except Exception as e:
        raise DataModelError(
            "Failed to generate source IP table",
            operation="print_src_ip_table",
            cause=e
        )

def print_unique_clients(connections: Dict[int, Any], resolve_hostnames: bool = False) -> None:
    """Prints a sorted list of unique client source IPs."""
    try:
        unique_ips = set()
        for conn in connections.values():
            if conn.source_ip:
                unique_ips.add(conn.source_ip)

        if not unique_ips:
            print("No client connections found.")
            return

        if resolve_hostnames:
            print("Unique Client Hostnames")
            print("-----------------------")
            unique_hostnames = set()
            for ip in unique_ips:
                try:
                    hostname = resolve_hostname(ip)
                    unique_hostnames.add(hostname)
                except HostnameResolutionError:
                    unique_hostnames.add(ip)
            
            for hostname in sorted(unique_hostnames):
                print(hostname)
            print(f"\nTotal unique clients: {len(unique_hostnames)}")
        else:
            print("Unique Client IPs")
            print("-----------------")
            for ip in sorted(unique_ips):
                print(ip)
            print(f"\nTotal unique clients: {len(unique_ips)}")
            
    except Exception as e:
        raise DataModelError(
            "Failed to generate unique clients list",
            operation="print_unique_clients",
            cause=e
        )

def print_open_connections_table(connections: Dict[int, Any], resolve_hostnames: bool = False, filter_bind_dn: Optional[List[str]] = None) -> None:
    """Prints a table of open connections with source IP, bind DN, and bind time."""
    try:
        print(f"{'Source IP/Hostname':<40} {'Bind DN':<50} {'Bind Timestamp':<35}")
        print(f"{'----------------------------------------':<40} {'--------------------------------------------------':<50} {'-----------------------------------':<35}")

        open_connections = sorted(
            [c for c in connections.values() if c.successful_bind and c.unbind_timestamp is None],
            key=lambda c: c.bind_timestamp
        )

        if not open_connections:
            print("No open connections found.")
            return

        # Create summary before filtering
        bind_dn_counts: Dict[str, int] = {}
        for conn in open_connections:
            dn = conn.bind_dn or "Anonymous"
            bind_dn_counts[dn] = bind_dn_counts.get(dn, 0) + 1

        # Filter connections for table view if filter is provided
        if filter_bind_dn:
            connections_to_print = [c for c in open_connections if c.bind_dn in filter_bind_dn]
        else:
            connections_to_print = open_connections

        for conn in connections_to_print:
            try:
                display_name = get_display_ip(conn, resolve_hostnames)
                bind_dn = conn.bind_dn or "N/A"
                bind_time = conn.bind_timestamp.isoformat() if conn.bind_timestamp else "N/A"
                print(f"{display_name:<40} {bind_dn:<50} {bind_time:<35}")
            except Exception as e:
                logger.warning(f"Error displaying connection {conn.conn_num}: {e}")
                continue

        print(f"\nTotal open connections displayed: {len(connections_to_print)}")

        # Print summary table
        print("\nSummary of Open Connections by Bind DN:")
        print(f"{'Bind DN':<70} {'Count'}")
        print(f"{'----------------------------------------------------------------------':<70} {'-----'}")
        for dn, count in sorted(bind_dn_counts.items()):
            print(f"{dn:<70} {count}")
            
    except Exception as e:
        raise DataModelError(
            "Failed to generate open connections table",
            operation="print_open_connections_table",
            cause=e
        )

def format_result_info(result: Optional[Any]) -> str:
    """Formats result information showing err and nentries values."""
    if result is None or not isinstance(result, dict):
        return "N/A"
    
    err = result.get('err', 'N/A')
    nentries = result.get('nentries', 'N/A')
    
    return f"err={err} nentries={nentries}"

def operation_matches_filters(operation: Any, filter_err: Optional[int] = None, filter_nentries: Optional[int] = None, filter_op_include: Optional[List[str]] = None, filter_op_exclude: Optional[List[str]] = None) -> bool:
    """Check if an operation matches the specified filter criteria."""
    if filter_err is None and filter_nentries is None and filter_op_include is None and filter_op_exclude is None:
        return True
    
    # Check operation type filters first (no need for result data)
    if filter_op_include is not None or filter_op_exclude is not None:
        op_type = getattr(operation, 'op_type', None)
        
        # If include filter is specified, operation type must be in the list
        if filter_op_include and op_type not in filter_op_include:
            return False
            
        # If exclude filter is specified, operation type must not be in the list
        if filter_op_exclude and op_type in filter_op_exclude:
            return False
    
    # Skip operations without result data if err/nentries filters are specified
    if (filter_err is not None or filter_nentries is not None):
        if not operation.result or not isinstance(operation.result, dict):
            return False
    
    # Check err filter
    if filter_err is not None:
        op_err = operation.result.get('err')
        if op_err != filter_err:
            return False
    
    # Check nentries filter
    if filter_nentries is not None:
        op_nentries = operation.result.get('nentries')
        if op_nentries != filter_nentries:
            return False
    
    return True

def print_connection_details(connections: Dict[int, Any], resolve_hostnames: bool = False, conn_id: Optional[int] = None, filter_err: Optional[int] = None, filter_nentries: Optional[int] = None, filter_op_include: Optional[List[str]] = None, filter_op_exclude: Optional[List[str]] = None) -> None:
    """Prints detailed operations for one or all connections.
    
    Args:
        connections: Dictionary of connection objects
        resolve_hostnames: Whether to resolve IP addresses to hostnames
        conn_id: Optional specific connection ID to display
        filter_err: Optional error code filter (e.g., 0 for success, 49 for access denied)
        filter_nentries: Optional number of entries filter (e.g., 0 for no results, >0 for successful searches)
        filter_op_include: Optional list of operation types to include
        filter_op_exclude: Optional list of operation types to exclude
    """
    try:
        # If a specific connection ID is provided, filter for it
        if conn_id is not None:
            validate_connection_id(conn_id, connections)
            connections_to_print = {conn_id: connections[conn_id]}
        else:
            connections_to_print = connections

        if not connections_to_print:
            print("No connections found.")
            return

        # Sort connections by their number for consistent output
        sorted_conn_keys = sorted(connections_to_print.keys())

        for key in sorted_conn_keys:
            conn = connections_to_print[key]
            try:
                # Sort operations by timestamp or operation number as a fallback
                sorted_ops = sorted(
                    conn.operations.values(), 
                    key=lambda op: (op.timestamp, op.op_num) if op.timestamp else (None, op.op_num)
                )

                # Apply filters if specified
                if filter_err is not None or filter_nentries is not None or filter_op_include is not None or filter_op_exclude is not None:
                    filtered_ops = [op for op in sorted_ops if operation_matches_filters(op, filter_err, filter_nentries, filter_op_include, filter_op_exclude)]
                else:
                    filtered_ops = sorted_ops

                # Skip connections with no matching operations when filtering
                if not filtered_ops:
                    if filter_err is None and filter_nentries is None and filter_op_include is None and filter_op_exclude is None:
                        # Only show "no operations" message when not filtering
                        display_name = get_display_ip(conn, resolve_hostnames)
                        print(f"\n--- Connection: {conn.conn_num} | Source: {display_name} | Bind DN: {conn.bind_dn or 'N/A'} ---")
                        print("  No operations found for this connection.")
                    continue

                # Only print connection header if we have operations to show
                display_name = get_display_ip(conn, resolve_hostnames)
                print(f"\n--- Connection: {conn.conn_num} | Source: {display_name} | Bind DN: {conn.bind_dn or 'N/A'} ---")

                for op in filtered_ops:
                    try:
                        # Format timestamp to be more readable
                        ts = op.timestamp.strftime('%Y-%m-%d %H:%M:%S') if op.timestamp else "N/A"
                        
                        # Format result information
                        result_info = format_result_info(op.result)

                        if op.op_type == 'SRCH':
                            base = op.data.get('base', 'N/A')
                            sfilter = op.data.get('filter', 'N/A')
                            attrs = op.data.get('attrs', 'N/A')
                            print(f"  Op: {op.op_num if op.op_num is not None else '-':<5} | Type: {op.op_type:<8} | Timestamp: {ts} | Result: {result_info:<20} | Base: {base} | Filter: {sfilter} | Attrs: {attrs}")
                        else:
                            print(f"  Op: {op.op_num if op.op_num is not None else '-':<5} | Type: {op.op_type:<8} | Timestamp: {ts} | Result: {result_info:<20}")
                    except Exception as e:
                        logger.warning(f"Error displaying operation {op.op_num} for connection {conn.conn_num}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error displaying connection {key}: {e}")
                continue
                
    except ConnectionNotFoundError:
        # Re-raise connection not found errors
        raise
    except Exception as e:
        raise DataModelError(
            "Failed to generate connection details",
            operation="print_connection_details",
            cause=e
        )

def print_unindexed_searches_table(connections: Dict[int, Any]) -> None:
    """Prints a table of partially unindexed searches."""
    try:
        print(f"{'Timestamp':<35} {'Conn':<10} {'Op':<10} {'Base':<30} {'Filter'}")
        print(f"{'-----------------------------------':<35} {'----------':<10} {'----------':<10} {'------------------------------':<30} {'-'*40}")

        unindexed_searches: List[Any] = []
        for conn in connections.values():
            for op in conn.operations.values():
                if (op.op_type == 'SRCH' and 
                    op.result and 
                    isinstance(op.result, dict) and
                    op.result.get('details') == 'Partially Unindexed Filter'):
                    unindexed_searches.append((
                        op.timestamp, 
                        conn.conn_num, 
                        op.op_num, 
                        op.data.get('base', 'N/A'), 
                        op.data.get('filter', 'N/A')
                    ))

        if not unindexed_searches:
            print("No unindexed searches found.")
            return

        unindexed_searches.sort(key=lambda x: x[0] if x[0] else datetime.min)

        for ts, conn_num, op_num, base, sfilter in unindexed_searches:
            try:
                timestamp_str = ts.isoformat() if ts else "N/A"
                print(f"{timestamp_str:<35} {conn_num:<10} {op_num:<10} {base:<30} {sfilter}")
            except Exception as e:
                logger.warning(f"Error displaying unindexed search for connection {conn_num}, operation {op_num}: {e}")
                continue

        print(f"\nTotal unindexed searches found: {len(unindexed_searches)}")
        
    except Exception as e:
        raise DataModelError(
            "Failed to generate unindexed searches table",
            operation="print_unindexed_searches_table",
            cause=e
        )

def resolve_hostname(ip_address: str) -> str:
    """Resolves an IP address to a hostname, with caching."""
    if not ip_address:
        raise HostnameResolutionError("Empty IP address")
    
    if ip_address in hostname_cache:
        return hostname_cache[ip_address]
    
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        hostname_cache[ip_address] = hostname
        logger.debug(f"Resolved {ip_address} to {hostname}")
        return hostname
    except (socket.herror, socket.gaierror) as e:
        # Cache the failure to avoid repeated lookups
        hostname_cache[ip_address] = ip_address
        raise HostnameResolutionError(ip_address, cause=e)
    except Exception as e:
        hostname_cache[ip_address] = ip_address
        raise NetworkOperationError(
            f"Unexpected error resolving hostname for {ip_address}",
            operation="hostname_resolution",
            target=ip_address,
            cause=e
        )

def load_or_build_data_model(args: argparse.Namespace) -> LogDataModel:
    """
    Load data model from file or build from log file.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        LogDataModel instance
        
    Raises:
        Various custom exceptions based on the failure mode
    """
    try:
        if args.load_datamodel:
            validate_file_path(args.load_datamodel, must_exist=True)
            logger.info(f"Loading data model from: {args.load_datamodel}")
            return LogDataModel.load(args.load_datamodel)
        else:
            validate_file_path(args.file, must_exist=True)
            logger.info(f"Building data model from log file: {args.file}")
            data_model = build_data_model(args.file, args.debug)
            
            if not data_model.connections:
                raise EmptyLogFileError(args.file)
            
            return data_model
            
    except (LogFileNotFoundError, LogFilePermissionError, DataModelFileError, EmptyLogFileError):
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        raise DataModelError(
            "Failed to load or build data model",
            operation="load_or_build",
            cause=e
        )

def save_data_model_if_requested(data_model: LogDataModel, args: argparse.Namespace) -> None:
    """
    Save data model if save options are specified.
    
    Args:
        data_model: The data model to save
        args: Parsed command line arguments
    """
    try:
        if args.save_pickle:
            logger.info(f"Saving data model to {args.save_pickle}...")
            data_model.save(args.save_pickle)
            print(f"Data model saved to {args.save_pickle}")

        if args.save_json:
            logger.info(f"Saving data model to {args.save_json} as JSON...")
            data_model.save_json(args.save_json)
            print(f"Data model saved as JSON to {args.save_json}")
            
    except DataModelFileError:
        # Re-raise file operation errors
        raise
    except Exception as e:
        raise DataModelError(
            "Failed to save data model",
            operation="save",
            cause=e
        )

def resolve_hostnames_if_requested(data_model: LogDataModel, resolve_hostnames: bool) -> None:
    """
    Resolve hostnames for all connections if requested.
    
    Args:
        data_model: The data model to update
        resolve_hostnames: Whether to resolve hostnames
    """
    if not resolve_hostnames:
        return
    
    try:
        print("Resolving hostnames for all connections...")
        resolved_count = 0
        failed_count = 0
        
        for conn in data_model.connections.values():
            if conn.source_ip and not conn.source_hostname:
                try:
                    conn.source_hostname = resolve_hostname(conn.source_ip)
                    resolved_count += 1
                except HostnameResolutionError:
                    failed_count += 1
                    # Keep the IP address as fallback
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error resolving hostname for {conn.source_ip}: {e}")
                    failed_count += 1
                    continue
        
        print(f"Done. Resolved {resolved_count} hostnames, {failed_count} failed.")
        
    except Exception as e:
        # Don't fail completely if hostname resolution has issues
        logger.warning(f"Error during hostname resolution: {e}")
        print("Warning: Hostname resolution encountered errors. Continuing with IP addresses.")

def main() -> None:
    """Main CLI entry point."""
    # Parent parser for common arguments that all subcommands will use
    parent_parser = argparse.ArgumentParser(add_help=False)
    input_group = parent_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-f', '--file', help='Path to the log file.')
    input_group.add_argument('-l', '--load-datamodel', help='Path to a persisted data model file to load.')
    parent_parser.add_argument('-p', '--save-pickle', help='Path to save the data model in pickle format.')
    parent_parser.add_argument('-j', '--save-json', help='Path to save the data model in JSON format.')
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
    parser = argparse.ArgumentParser(
        description="389-ds Log Analyser",
        prog="389ds-log-analyser"
    )
    
    try:
        pkg_version = version("389ds-log-analyser")
    except PackageNotFoundError:
        pkg_version = "dev"
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {pkg_version}'
    )
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
    parser_open.add_argument(
        '--filter-bind-dn',
        nargs='+',
        metavar='BIND_DN',
        help='Filter open connections by one or more Bind DNs.'
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

    # connection-details command
    parser_details = subparsers.add_parser(
        'connection-details',
        help='Display detailed operations for connections.',
        parents=[parent_parser]
    )
    parser_details.add_argument(
        '--conn-id',
        type=int,
        help='Display details for a specific connection ID.'
    )
    parser_details.add_argument(
        '--filter-err',
        type=int,
        help='Filter operations by error code (e.g., 0 for success, 49 for access denied).'
    )
    parser_details.add_argument(
        '--filter-nentries',
        type=int,
        help='Filter operations by number of entries returned (e.g., 0 for no results, >0 for successful searches).'
    )
    parser_details.add_argument(
        '--filter-op-type',
        metavar='OP_TYPE',
        help='Filter operations by type. Supports comma-separated values (ADD,SRCH,MOD) and negation with ! prefix (!BIND). Valid types: BIND, SRCH, ADD, MOD, DEL, MODRDN, CMP, EXT, UNBIND, Disconnect.'
    )
    parser_details.set_defaults(func=print_connection_details)

    argcomplete.autocomplete(parser)

    try:
        args = parser.parse_args()
        
        # Set up logging
        setup_logging(args.debug)
        
        # Validate arguments
        if args.filter_client_ip:
            args.filter_client_ip = validate_ip_addresses(args.filter_client_ip)
        
        # Parse and validate operation type filter
        filter_op_include = None
        filter_op_exclude = None
        if hasattr(args, 'filter_op_type') and args.filter_op_type:
            filter_op_include, filter_op_exclude = validate_operation_types(args.filter_op_type)
        
        # Load or build data model
        data_model = load_or_build_data_model(args)
        
        # Resolve hostnames if requested
        resolve_hostnames_if_requested(data_model, args.resolve_hostnames)
        
        # Save data model if requested
        save_data_model_if_requested(data_model, args)
        
        # Filter connections by client IP if specified
        connections = data_model.connections
        if args.filter_client_ip:
            connections = {
                conn_num: conn for conn_num, conn in connections.items()
                if conn.source_ip in args.filter_client_ip
            }
            
            if not connections:
                print(f"No connections found from the specified IP address(es): {', '.join(args.filter_client_ip)}")
                return

        # Execute the appropriate command
        if args.command == 'src-ip-table':
            print_src_ip_table(connections, args.resolve_hostnames)
        elif args.command == 'open-connections':
            print_open_connections_table(connections, args.resolve_hostnames, args.filter_bind_dn)
        elif args.command == 'unique-clients':
            print_unique_clients(connections, args.resolve_hostnames)
        elif args.command == 'unindexed-searches':
            print_unindexed_searches_table(connections)
        elif args.command == 'connection-details':
            print_connection_details(
                connections, 
                args.resolve_hostnames, 
                conn_id=getattr(args, 'conn_id', None),
                filter_err=getattr(args, 'filter_err', None),
                filter_nentries=getattr(args, 'filter_nentries', None),
                filter_op_include=filter_op_include,
                filter_op_exclude=filter_op_exclude
            )
        
    except (LogFileNotFoundError, LogFilePermissionError) as e:
        print(f"File Error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        sys.exit(1)
        
    except (DataModelFileError, DataModelError) as e:
        print(f"Data Model Error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        sys.exit(1)
        
    except (ValidationError, InvalidArgumentError, ConnectionNotFoundError) as e:
        print(f"Validation Error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        sys.exit(1)
        
    except (NetworkOperationError, HostnameResolutionError) as e:
        print(f"Network Error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        sys.exit(1)
        
    except LogAnalyserError as e:
        print(f"Error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.debug if 'args' in locals() else False:
            logger.exception("Detailed error information:")
        else:
            print("Use --debug for more detailed error information.")
        sys.exit(1)

def main_src_ip_table() -> None:
    sys.argv.insert(1, 'src-ip-table')
    main()

def main_open_connections() -> None:
    sys.argv.insert(1, 'open-connections')
    main()

def main_unique_clients() -> None:
    sys.argv.insert(1, 'unique-clients')
    main()

def main_unindexed_searches() -> None:
    sys.argv.insert(1, 'unindexed-searches')
    main()

def main_connection_details() -> None:
    sys.argv.insert(1, 'connection-details')
    main()

if __name__ == '__main__':
    main()

