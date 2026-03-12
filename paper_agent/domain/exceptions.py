"""Domain-level exceptions for Paper Agent."""


class PaperAgentError(Exception):
    """Base exception for all Paper Agent errors."""


class ConfigurationNotFoundError(PaperAgentError):
    """Raised when configuration file or profile cannot be found."""


class ConfigurationValidationError(PaperAgentError):
    """Raised when configuration is invalid or incomplete."""


class NotInitializedError(PaperAgentError):
    """Raised when system has not been initialized yet."""

    def __init__(self) -> None:
        super().__init__("尚未完成初始化。请先执行 paper-agent init。")


class EmptyLibraryError(PaperAgentError):
    """Raised when local paper library is empty."""

    def __init__(self) -> None:
        super().__init__("当前本地论文库为空。请先执行 paper-agent collect。")


class InsufficientDataError(PaperAgentError):
    """Raised when there is not enough data for report/survey generation."""


class SourceUnavailableError(PaperAgentError):
    """Raised when a paper source is unreachable."""


class LLMProviderError(PaperAgentError):
    """Raised when LLM provider call fails."""


class MethodExtractionFailedError(PaperAgentError):
    """Raised when method features cannot be extracted from input."""

    def __init__(self) -> None:
        super().__init__("无法从输入中提取有效方法特征。请提供更具体的方法或技术描述。")
