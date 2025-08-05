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

"""
Custom exception classes for the 389ds log analyser.

This module defines a hierarchy of exceptions that provide better error handling
and more informative error messages for different failure scenarios.
"""

from typing import Optional, Any


class LogAnalyserError(Exception):
    """Base exception class for all 389ds log analyser errors."""
    
    def __init__(self, message: str, details: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.cause = cause
    
    def __str__(self) -> str:
        result = self.message
        if self.details:
            result += f"\nDetails: {self.details}"
        if self.cause:
            result += f"\nCaused by: {self.cause}"
        return result


class FileOperationError(LogAnalyserError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: str, operation: str, 
                 details: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.file_path = file_path
        self.operation = operation


class LogFileNotFoundError(FileOperationError):
    """Raised when a log file cannot be found."""
    
    def __init__(self, file_path: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Log file not found: {file_path}",
            file_path=file_path,
            operation="read",
            details="Check that the file path is correct and the file exists",
            cause=cause
        )


class LogFilePermissionError(FileOperationError):
    """Raised when there are insufficient permissions to read a log file."""
    
    def __init__(self, file_path: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Permission denied accessing log file: {file_path}",
            file_path=file_path,
            operation="read",
            details="Check that you have read permissions for the file",
            cause=cause
        )


class DataModelFileError(FileOperationError):
    """Raised when data model file operations fail."""
    
    def __init__(self, file_path: str, operation: str, 
                 details: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Failed to {operation} data model file: {file_path}",
            file_path=file_path,
            operation=operation,
            details=details,
            cause=cause
        )


class LogParsingError(LogAnalyserError):
    """Raised when log parsing fails."""
    
    def __init__(self, message: str, line_number: Optional[int] = None, 
                 line_content: Optional[str] = None, details: Optional[str] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.line_number = line_number
        self.line_content = line_content
    
    def __str__(self) -> str:
        result = self.message
        if self.line_number is not None:
            result += f" (line {self.line_number})"
        if self.line_content:
            result += f"\nLine content: {self.line_content[:100]}{'...' if len(self.line_content) > 100 else ''}"
        if self.details:
            result += f"\nDetails: {self.details}"
        if self.cause:
            result += f"\nCaused by: {self.cause}"
        return result


class TimestampParsingError(LogParsingError):
    """Raised when timestamp parsing fails."""
    
    def __init__(self, timestamp_str: str, line_number: Optional[int] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Failed to parse timestamp: {timestamp_str}",
            line_number=line_number,
            details="Timestamp format may be unsupported or malformed",
            cause=cause
        )
        self.timestamp_str = timestamp_str


class InvalidLogFormatError(LogParsingError):
    """Raised when log format is invalid or unsupported."""
    
    def __init__(self, line_content: str, line_number: Optional[int] = None,
                 expected_format: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(
            "Invalid log line format",
            line_number=line_number,
            line_content=line_content,
            details=f"Expected format: {expected_format}" if expected_format else None,
            cause=cause
        )


class ValidationError(LogAnalyserError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, parameter: Optional[str] = None,
                 value: Optional[Any] = None, details: Optional[str] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.parameter = parameter
        self.value = value


class InvalidArgumentError(ValidationError):
    """Raised when command-line arguments are invalid."""
    
    def __init__(self, argument: str, value: Any, reason: str,
                 suggestion: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        details = f"Reason: {reason}"
        if suggestion:
            details += f"\nSuggestion: {suggestion}"
        
        super().__init__(
            f"Invalid argument '{argument}': {value}",
            parameter=argument,
            value=value,
            details=details,
            cause=cause
        )


class ConnectionNotFoundError(ValidationError):
    """Raised when a requested connection ID is not found."""
    
    def __init__(self, connection_id: int, available_connections: Optional[list] = None,
                 cause: Optional[Exception] = None) -> None:
        details = None
        if available_connections:
            details = f"Available connection IDs: {', '.join(map(str, sorted(available_connections)))}"
        
        super().__init__(
            f"Connection ID {connection_id} not found",
            parameter="connection_id",
            value=connection_id,
            details=details,
            cause=cause
        )


class NetworkOperationError(LogAnalyserError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, operation: str, target: Optional[str] = None,
                 details: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.operation = operation
        self.target = target


class HostnameResolutionError(NetworkOperationError):
    """Raised when hostname resolution fails."""
    
    def __init__(self, ip_address: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Failed to resolve hostname for IP address: {ip_address}",
            operation="hostname_resolution",
            target=ip_address,
            details="The IP address may not have a reverse DNS entry",
            cause=cause
        )


class DataModelError(LogAnalyserError):
    """Raised when data model operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 details: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.operation = operation


class EmptyLogFileError(DataModelError):
    """Raised when a log file is empty or contains no parseable entries."""
    
    def __init__(self, file_path: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Log file is empty or contains no parseable entries: {file_path}",
            operation="parse_log_file",
            details="Check that the file contains valid 389ds access log entries",
            cause=cause
        )


class CorruptedDataModelError(DataModelError):
    """Raised when a data model file is corrupted or invalid."""
    
    def __init__(self, file_path: str, format_type: str, cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Corrupted or invalid {format_type} data model file: {file_path}",
            operation="load_data_model",
            details=f"The {format_type} file may be corrupted or from an incompatible version",
            cause=cause
        )


class ConfigurationError(LogAnalyserError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, setting: Optional[str] = None,
                 value: Optional[Any] = None, details: Optional[str] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.setting = setting
        self.value = value


class IncompatibleVersionError(ConfigurationError):
    """Raised when trying to load data from an incompatible version."""
    
    def __init__(self, file_version: str, current_version: str,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(
            f"Incompatible data model version: {file_version} (current: {current_version})",
            setting="data_model_version",
            value=file_version,
            details="The data model file was created with a different version of the tool",
            cause=cause
        ) 