from fastapi import HTTPException, status

class ReviewSystemException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class InvalidFileFormatError(ReviewSystemException):
    def __init__(self, detail: str = "Invalid file format"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ScrapingError(ReviewSystemException):
    def __init__(self, detail: str = "Error occurred while scraping data"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class AnalysisError(ReviewSystemException):
    def __init__(self, detail: str = "Error occurred during analysis"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class AuthenticationError(ReviewSystemException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class AuthorizationError(ReviewSystemException):
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail) 