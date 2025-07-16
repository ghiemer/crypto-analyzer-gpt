from fastapi import HTTPException

class ApiError(HTTPException):
    """Standardisierte Fehlerantwort für GPT-freundliches Handling."""
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(status_code=status,
                         detail={"error": {"code": code, "message": message}})

BAD_ARGUMENT = lambda m: ApiError("BAD_ARGUMENT",  m, 400)
NOT_FOUND    = lambda m: ApiError("NOT_FOUND",     m, 404)
UPSTREAM     = lambda m: ApiError("UPSTREAM_FAIL", m, 502)
RATE_LIMIT   = lambda m: ApiError("RATE_LIMIT",    m, 429)