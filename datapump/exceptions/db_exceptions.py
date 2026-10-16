"""Custom exception classes for database operations in DataPump.

This module defines a hierarchy of custom exceptions used to handle
database connection issues, query errors, data integrity violations,
and unexpected database behaviors throughout the application.
"""


class DatabaseError(Exception):
    """Base exception class for all database-related errors in DataPump.

    Attributes:
        __module__: The module name override for the exception.
    """

    __module__ = "DataPump"
    pass


class DatabaseConnectionPoolTimeout(DatabaseError):
    """Exception raised when a connection pool operation times out."""

    def __init__(self, message: str = "Connection pool timeout!"):
        """Initializes the DatabaseConnectionPoolTimeout exception.

        Args:
            message: Explanation of the timeout error.
        """
        self.message = message
        super().__init__(self.message)


class DatabaseConnectionPoolClosed(DatabaseError):
    """Exception raised when attempting to interact with a closed connection pool."""

    def __init__(self, message: str = "Connection pool closed!"):
        """Initializes the DatabaseConnectionPoolClosed exception.

        Args:
            message: Explanation of the closed pool error.
        """
        self.message = message
        super().__init__(self.message)


class DatabaseDataError(DatabaseError):
    """Exception raised when invalid data is provided for database operations."""

    def __init__(
        self,
        message: str = "Invalid data provided! Try again with valid data...",
    ):
        """Initializes the DatabaseDataError exception.

        Args:
            message: Explanation of the data error.
        """
        self.message = message
        super().__init__(self.message)


class DatabaseIntegrityError(DatabaseError):
    """Exception raised when data violates database integrity constraints."""

    def __init__(
        self,
        message: str = (
            "Provided data doesn't holds database intgrity! Try agin with valid data..."
        ),
    ):
        """Initializes the DatabaseIntegrityError exception.

        Args:
            message: Explanation of the integrity error.
        """
        self.message = message
        super().__init__(self.message)


class DatabaseProgrammingError(DatabaseError):
    """Exception raised for syntax or programming errors in SQL queries."""

    def __init__(
        self,
        message: str = (
            "Syntax error in SQL! Please take a proper look at your SQL query..."
        ),
    ):
        """Initializes the DatabaseProgrammingError exception.

        Args:
            message: Explanation of the programming error.
        """
        self.message = message
        super().__init__(message)


class DatabaseUnexpectedError(DatabaseError):
    """Exception raised for unhandled or unexpected database errors."""

    def __init__(
        self,
        message: str = (
            "Unexpected error occured in database! Please try again later..."
        ),
    ):
        """Initializes the DatabaseUnexpectedError exception.

        Args:
            message: Explanation of the unexpected error.
        """
        self.message = message
        super().__init__(self.message)