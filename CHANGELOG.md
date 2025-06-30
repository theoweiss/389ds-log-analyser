# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-06-30

### Added
- Added `--save-datamodel` (`-s`) to save the parsed data model to a file.
- Added `--load-datamodel` (`-l`) to load a data model from a file, bypassing log parsing.

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

[1.2.0]: https://github.com/theoweiss/389ds-log-analyser/compare/v1.1.1...v1.2.0
[1.0.0]: https://github.com/theoweiss/389ds-log-analyser/releases/tag/v1.0.0
