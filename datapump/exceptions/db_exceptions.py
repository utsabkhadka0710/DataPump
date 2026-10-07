class DatabaseError(Exception):
    __module__ = "DataPump"
    pass

class DatabaseConnectionPoolTimeout(DatabaseError):
    def __init__(self, message: str="Connection pool timeout!"):
        self.message = message
        super().__init__(self.message)

class DatabaseConnectionPoolClosed(DatabaseError):
    def __init__(self, message: str="Connection pool closed!"):
        self.message = message
        super().__init__(self.message)

class DatabaseDataError(DatabaseError):
    def __init__(self, message: str="Invalid data provided! Try again with valid data..."):
        self.message = message
        super().__init__(self.message)

class DatabaseIntegrityError(DatabaseError):
    def __init__(self, message: str="Provided data doesn't holds database intgrity! Try agin with valid data..."):
        self.message = message
        super().__init__(self.message)

class DatabaseProgrammingError(DatabaseError):
    def __init__(self, message: str="Syntax error in SQL! Please take a proper look at your SQL query..."):
        self.message = message
        super().__init__(message)

class DatabaseUnexpectedError(DatabaseError):
    def __init__(self, message: str="Unexpected error occured in database! Please try again later..."):
        self.message = message
        super().__init__(self.message)
