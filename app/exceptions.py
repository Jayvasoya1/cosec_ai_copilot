"""
Custom exception classes for better error handling and debugging
"""


class CoSecException(Exception):
    """Base exception for all CoSec Copilot errors"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class IntentParsingError(CoSecException):
    """Raised when LLM fails to parse intent"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "INTENT_PARSING_ERROR", details)


class ValidationError(CoSecException):
    """Raised when validation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class MissingParametersError(ValidationError):
    """Raised when required parameters are missing"""
    def __init__(self, missing_params: list, partial: dict = None):
        details = {
            "missing": missing_params,
            "partial": partial or {}
        }
        super().__init__(
            f"Missing required parameters: {', '.join(missing_params)}",
            "MISSING_PARAMETERS",
            details
        )


class SchemaError(CoSecException):
    """Raised when schema is invalid or not found"""
    def __init__(self, message: str, schema_name: str = None):
        details = {"schema": schema_name} if schema_name else {}
        super().__init__(message, "SCHEMA_ERROR", details)


class RouterError(CoSecException):
    """Raised when no handler found for intent"""
    def __init__(self, intent: str):
        super().__init__(
            f"No handler found for intent: {intent}",
            "ROUTER_ERROR",
            {"intent": intent}
        )


class APIBuildError(CoSecException):
    """Raised when API URL building fails"""
    def __init__(self, message: str, params: dict = None):
        super().__init__(message, "API_BUILD_ERROR", {"params": params})


class DeviceAPIError(CoSecException):
    """Raised when device API call fails"""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, "DEVICE_API_ERROR", details)


class ConfigError(CoSecException):
    """Raised when configuration is missing or invalid"""
    def __init__(self, message: str, config_key: str = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, "CONFIG_ERROR", details)
