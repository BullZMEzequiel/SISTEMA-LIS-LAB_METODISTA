from fastapi import HTTPException, status

from app.domain.exceptions import Conflict, DomainError, EntityNotFound, InvalidState, PermissionDenied, ValidationError


def as_http_error(error: DomainError) -> HTTPException:
    if isinstance(error, EntityNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, PermissionDenied):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(error, Conflict | InvalidState):
        code = status.HTTP_409_CONFLICT
    elif isinstance(error, ValidationError):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(error))