# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-07-01

### Added
- New `connection-details` command and `389ds-connection-details` shortcut to display all operations for one or all connections, including search details.
- Ability to filter for a specific connection using `--conn-id`.
- Hostname persistence in the data model; resolved hostnames are now saved and reused.
- Table formatting improvements to accommodate hostnames.
- Timestamp formatting in `connection-details` output now accurate to the second for readability.

### Changed
- Updated documentation to cover new features and options.
- Expanded and improved test coverage for new features and CLI commands.

## [1.4.0] - 2025-06-30

### Added
- Added command-line completion support via `argcomplete`.
- Added `--filter-bind-dn` to the `open-connections` command to filter by Bind DN.

### Changed
- The `open-connections` command now displays a summary table of open connections grouped by Bind DN.
- The `open-connections` and `unique-clients` commands now display the total count of items in their output.

## [1.3.0] - 2025-06-30

### Added
- Added `--save-json` (`-j`) to save the data model in a human-readable JSON format.
- Updated `--load-datamodel` (`-l`) to automatically detect the file format (pickle or JSON).

### Changed
- Renamed `--save-datamodel` to `--save-pickle` (`-p`) for clarity and consistency.

## [1.0.0] - 2025-06-11

### Added
- Initial release of the 389ds Log Analyser.
- Core parsing logic for 389-ds access logs.
- Data model for connections and operations.
- Subcommand-based CLI for different query modes (`src-ip-table`, `open-connections`, `unique-clients`, `unindexed-searches`).
- Standalone shortcut scripts for each command (e.g., `389ds-src-ip-table`).
- `--filter-client-ip` option to filter results by source IP.
- Unit and integration tests using `pytest`.
- `LICENSE`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md`.

### Changed
- Refactored from a single script to a structured Python package with a `src` layout.
- Replaced Lark parser with a regex-based implementation, removing external dependencies.
- Improved CLI usability by replacing `--query` argument with subcommands.

[1.4.0]: https://github.com/theoweiss/389ds-log-analyser/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/theoweiss/389ds-log-analyser/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/theoweiss/389ds-log-analyser/compare/v1.1.1...v1.2.0
[1.0.0]: https://github.com/theoweiss/389ds-log-analyser/releases/tag/v1.0.0
