"""
Exceptions personnalisées pour le module de comptabilité.

Centralise les différentes exceptions qui peuvent être levées par le module.
"""


class AccountingError(Exception):
    """Classe de base pour toutes les exceptions du module de comptabilité."""
    def __init__(self, message: str = "Une erreur s'est produite dans le module de comptabilité"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(AccountingError):
    """Exception levée en cas d'erreur de configuration."""
    def __init__(self, message: str = "Erreur de configuration"):
        super().__init__(f"Erreur de configuration: {message}")


class DatabaseError(AccountingError):
    """Exception levée en cas d'erreur avec la base de données."""
    def __init__(self, message: str = "Erreur de base de données"):
        super().__init__(f"Erreur de base de données: {message}")


class AuthenticationError(AccountingError):
    """Exception levée en cas d'erreur d'authentification."""
    def __init__(self, message: str = "Erreur d'authentification"):
        super().__init__(f"Erreur d'authentification: {message}")


class AuthorizationError(AccountingError):
    """Exception levée en cas d'erreur d'autorisation."""
    def __init__(self, message: str = "Erreur d'autorisation"):
        super().__init__(f"Erreur d'autorisation: {message}")


class ValidationError(AccountingError):
    """Exception levée en cas d'erreur de validation des données."""
    def __init__(self, message: str = "Erreur de validation"):
        super().__init__(f"Erreur de validation: {message}")


class DataError(AccountingError):
    """Exception levée en cas d'erreur liée aux données."""
    def __init__(self, message: str = "Erreur de données"):
        super().__init__(f"Erreur de données: {message}")


class DataFormatError(DataError):
    """Exception levée en cas d'erreur de format de données."""
    def __init__(self, message: str = "Erreur de format de données"):
        super().__init__(f"Erreur de format de données: {message}")


class DataInconsistencyError(DataError):
    """Exception levée en cas d'incohérence dans les données."""
    def __init__(self, message: str = "Incohérence dans les données"):
        super().__init__(f"Incohérence dans les données: {message}")


class ConnectionError(AccountingError):
    """Exception levée en cas d'erreur de connexion à un service externe."""
    def __init__(self, message: str = "Erreur de connexion"):
        super().__init__(f"Erreur de connexion: {message}")


class RateLimitError(ConnectionError):
    """Exception levée en cas de limite de taux atteinte pour une API."""
    def __init__(self, message: str = "Limite de taux atteinte"):
        super().__init__(f"Limite de taux atteinte: {message}")


class IntegrationError(AccountingError):
    """Exception levée en cas d'erreur d'intégration avec un autre module."""
    def __init__(self, message: str = "Erreur d'intégration"):
        super().__init__(f"Erreur d'intégration: {message}")


class ReportGenerationError(AccountingError):
    """Exception levée en cas d'erreur lors de la génération d'un rapport."""
    def __init__(self, message: str = "Erreur lors de la génération du rapport"):
        super().__init__(f"Erreur de génération de rapport: {message}")


class ExportError(AccountingError):
    """Exception levée en cas d'erreur lors de l'exportation de données."""
    def __init__(self, message: str = "Erreur lors de l'exportation"):
        super().__init__(f"Erreur d'exportation: {message}")


class TaskSchedulerError(AccountingError):
    """Exception levée en cas d'erreur avec le planificateur de tâches."""
    def __init__(self, message: str = "Erreur avec le planificateur de tâches"):
        super().__init__(f"Erreur de planification: {message}")


class FileOperationError(AccountingError):
    """Exception levée en cas d'erreur lors d'opérations sur des fichiers."""
    def __init__(self, message: str = "Erreur lors d'opérations sur des fichiers"):
        super().__init__(f"Erreur de fichier: {message}")
