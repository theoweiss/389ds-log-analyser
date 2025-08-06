# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.0] - 2025-01-19

### Added
- Operation type filtering with `--filter-op-type` option for `connection-details` command
- Support for comma-separated operation types (e.g., `ADD,SRCH,MOD`)
- Negation support with `!` prefix to exclude operation types (e.g., `!BIND`)
- Comprehensive validation with helpful error messages for invalid operation types
- Advanced filtering combinations with existing filters (`--filter-err`, `--filter-nentries`)

### Enhanced
- Updated README with extensive documentation and examples for operation type filtering
- Added operation type analysis examples for authentication monitoring and write operation tracking
- Improved CLI help text with detailed operation type filter syntax examples

## [1.6.2] - 2025-01-18

### Added
- Result column in `connection-details` command output showing operation results (`err` and `nentries` values)
- Enhanced operation tracking with RESULT information from 389DS access logs

### Changed
- Improved `connection-details` output format with 4th column displaying operation success/failure status and entry counts

## [1.6.1] - 2025-08-05

### Fixed
- Missing modules in package configuration (exceptions, logging_config)
- ModuleNotFoundError in CI installation tests for Python 3.9/3.10
- Package installation compatibility across different Python versions
- Import resolution issues in installed package context

## [1.6.0] - 2025-08-05

### Added
- Custom exception hierarchy with detailed error messages and context (`exceptions.py`)
- Centralized logging configuration with colored console output (`logging_config.py`)
- Enhanced error handling with structured exception classes
- Improved user feedback with detailed error descriptions and suggestions
- Performance logging capabilities for operation timing
- Rotating log file support with automatic cleanup

### Changed
- Improved CLI error handling with proper exit codes and validation messages
- Enhanced error message consistency across all commands
- Better structured logging output with color-coded levels
- Refined validation error messages for better user experience

### Fixed
- Test validation for CLI error scenarios and edge cases
- Proper error code handling in connection-details command validation
- Improved exception handling throughout the codebase

## [1.5.0] - 2025-07-01

### Added
- Full type annotation support for Python 3.8+
- Enhanced documentation and examples
- Better error handling and debug mode
- Comprehensive test coverage (24+ tests)

### Changed
- Relicensed from MIT to GPL v3
- Updated minimum Python version requirement to 3.8
- Improved code organization and maintainability

### Security
- Added GPL v3 license headers to all source files
- Enhanced copyright and license information

## [1.4.0] - 2025-06-30

### Added
- Data model persistence in JSON and pickle formats
- Hostname resolution with caching for better readability
- Advanced filtering by client IP addresses and bind DNs
- Command-line completion support via argcomplete
- Standalone command scripts for convenience

### Changed
- Improved performance for large log files through data model caching
- Enhanced output formatting and table display
- Better error messages and user feedback

### Fixed
- Parsing issues with various timestamp formats
- Memory usage optimization for large datasets

## [1.3.0] - 2025-06-30

### Added
- `connection-details` command for detailed operation tracing
- Support for filtering open connections by bind DN
- Summary statistics for open connections grouped by bind DN
- Enhanced debug mode with detailed parsing information

### Changed
- Improved CLI argument parsing and validation
- Better handling of malformed log entries
- Enhanced documentation with more examples

### Fixed
- Issues with parsing certain LDAP operation types
- Timezone handling in timestamp parsing

## [1.2.0] - 2025-06-30

### Added
- `unindexed-searches` command for performance analysis
- Support for resolving IP addresses to hostnames
- Filtering capabilities for analysis commands
- Comprehensive test suite

### Changed
- Refactored log parsing logic for better maintainability
- Improved error handling and user feedback
- Enhanced CLI help and documentation

### Fixed
- Parsing edge cases with quoted values in log entries
- Handling of incomplete or truncated log lines

## [1.1.1] - 2025-06-13

### Fixed
- Correct packaging configuration and dependencies
- Added installation validation test

## [1.1.0] - 2025-06-13

### Added
- `open-connections` command to monitor active sessions
- `unique-clients` command to list all connecting IP addresses
- Support for multiple output formats
- Basic filtering and sorting capabilities

### Changed
- Improved log parsing accuracy and performance
- Better handling of various log formats
- Enhanced command-line interface

### Fixed
- Issues with connection state tracking
- Timestamp parsing for different locale settings

## [1.0.0] - 2025-06-11

### Added
- Initial release of 389ds-log-analyser
- `src-ip-table` command for analyzing completed connections
- Basic log parsing for 389 Directory Server access logs
- Command-line interface with argparse
- Support for analyzing connection lifecycles
- MIT license

### Features
- Parse 389ds access logs and extract connection information
- Track BIND and UNBIND operations
- Display tables of connection data with timestamps
- Basic error handling and validation

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backwards compatible manner  
- **PATCH** version when making backwards compatible bug fixes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information about contributing to this project.

## License

Starting with version 1.5.0, this project is licensed under the GNU General Public License v3.0.
Previous versions (1.0.0 - 1.4.0) were licensed under the MIT License.
