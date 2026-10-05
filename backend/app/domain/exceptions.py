class DomainError(Exception):
    """Base para rechazos por reglas de negocio del LIS."""


class EntityNotFound(DomainError):
    pass


class PermissionDenied(DomainError):
    pass


class InvalidState(DomainError):
    pass


class ValidationError(DomainError):
    pass


class Conflict(DomainError):
    pass