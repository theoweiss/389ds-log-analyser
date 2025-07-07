# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive type annotations for all modules
- Enhanced documentation with detailed examples and troubleshooting
- Contributing guidelines and development setup instructions
- API documentation for programmatic usage
- Performance optimization examples and workflows

### Changed
- License changed from MIT to GNU General Public License v3.0
- Updated README with comprehensive feature overview and usage examples
- Improved error handling and debug output
- Enhanced CLI help text and command descriptions

### Fixed
- Missing `if __name__ == '__main__':` block in cli.py that prevented module execution
- Type safety improvements throughout codebase

## [1.5.0] - 2024-12-XX

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

## [1.4.0] - 2024-XX-XX

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

## [1.3.0] - 2024-XX-XX

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

## [1.2.0] - 2024-XX-XX

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

## [1.1.0] - 2024-XX-XX

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

## [1.0.0] - 2024-XX-XX

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
