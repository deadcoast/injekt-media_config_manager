"""Exception hierarchy for Injekt CLI."""


class InjektError(Exception):
    """Base exception for Injekt CLI."""
    pass


class PackageNotFoundError(InjektError):
    """Package does not exist."""
    pass


class ValidationError(InjektError):
    """Configuration validation failed."""
    pass


class InstallationError(InjektError):
    """Installation operation failed."""
    pass


class BackupError(InjektError):
    """Backup operation failed."""
    pass


class PathResolutionError(InjektError):
    """Path detection or resolution failed."""
    pass


class ConflictError(InjektError):
    """File conflict detected."""
    pass


class DependencyError(InjektError):
    """Dependency resolution failed."""
    pass
