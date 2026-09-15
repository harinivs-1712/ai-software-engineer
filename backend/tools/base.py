from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        pass

    @property
    def risk_level(self) -> str:
        """
        Risk level classification:
        - "safe": Can execute automatically (read-only / pure operations)
        - "restricted": Executes within restricted sandbox (e.g. isolated python runner)
        - "confirmation_required": Requires user confirmation before execution (e.g. write, delete, shell)
        """
        return "safe"

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

    def get_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }