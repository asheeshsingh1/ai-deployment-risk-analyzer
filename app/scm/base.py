from abc import ABC, abstractmethod

from app.scm.schemas import CodeChangeRequest


class SCMProvider(ABC):
    @abstractmethod
    def get_change_request(
        self,
        owner: str,
        repository: str,
        change_number: int,
    ) -> CodeChangeRequest:
        raise NotImplementedError

    @abstractmethod
    def add_change_request_comment(
        self,
        owner: str,
        repository: str,
        change_number: int,
        body: str,
    ) -> None:
        raise NotImplementedError
