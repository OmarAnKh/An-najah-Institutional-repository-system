from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from global_config import global_config
from .abstract_classes import ABCClient


class AbstractOpenSearchFactory(ABC):
    """Abstract factory for producing configured OpenSearch clients."""

    def __init__(self, *, host: str, port: int) -> None:
        self.host = host
        self.port = port

    @abstractmethod
    def create(self) -> OpenSearch:
        """Instantiate and return a configured OpenSearch client."""


class LocalOpenSearchFactory(AbstractOpenSearchFactory):
    """Factory that creates a plain (non-AWS) OpenSearch client."""

    def __init__(
        self, *, host: str, port: int, use_ssl: bool, verify_certs: bool
    ) -> None:
        super().__init__(host=host, port=port)
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs

    def create(self) -> OpenSearch:
        """
            local OpenSearch deployments may have SSL disabled and may not use valid certificates.
        Returns:
            OpenSearch: Configured OpenSearch client instance
        """
        return OpenSearch(
            hosts=[{"host": self.host, "port": self.port}],
            use_ssl=self.use_ssl,
            verify_certs=self.verify_certs,
        )


class AwsOpenSearchFactory(AbstractOpenSearchFactory):
    """Factory that creates an AWS-managed OpenSearch client signed with IAM."""

    def __init__(self, *, host: str, port: int, region: str) -> None:
        super().__init__(host=host, port=port)
        self.region = region

    def create(self) -> OpenSearch:
        """
            AWS OpenSearch Service requires requests to be signed with AWS credentials.
        Raises:
            RuntimeError: If AWS credentials cannot be resolved.

        Returns:
            OpenSearch: Configured OpenSearch client instance
        """
        session = boto3.Session()
        credentials = session.get_credentials()
        service = "es"

        if credentials is None:
            raise RuntimeError(
                "AWS credentials could not be resolved for OpenSearch client"
            )

        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            service,
            session_token=credentials.token,
        )

        return OpenSearch(
            hosts=[{"host": self.host, "port": self.port}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )


class OpenSearchClient(ABCClient):
    """Concrete client that delegates creation to environment-specific factories."""

    _clients: dict[str, OpenSearch] = {}

    def __init__(
        self,
        use_ssl: bool | None = None,
        verify_certs: bool | None = None,
        mode: Literal["local", "aws"] | None = None,
    ) -> None:
        self.mode = (mode or global_config.opensearch_client_mode or "local").lower()
        if self.mode not in {"local", "aws"}:
            raise ValueError(
                "Invalid OpenSearch client mode. Expected 'local' or 'aws', "
                f"received '{self.mode}'."
            )

        # Local deployments often disable SSL; AWS always requires it.
        self.use_ssl = (
            True
            if self.mode == "aws"
            else (bool(use_ssl) if use_ssl is not None else False)
        )
        self.verify_certs = (
            True
            if self.mode == "aws"
            else (bool(verify_certs) if verify_certs is not None else False)
        )

    def _factory(self) -> AbstractOpenSearchFactory:
        """
                Determine and instantiate the appropriate factory based on the client mode.
        Returns:
            AbstractOpenSearchFactory: Factory instance configured for the current mode
        """
        common_kwargs = {
            "host": global_config.opensearch_host,
            "port": global_config.opensearch_port,
        }

        if self.mode == "aws":
            return AwsOpenSearchFactory(
                region=global_config.aws_region, **common_kwargs
            )

        return LocalOpenSearchFactory(
            use_ssl=self.use_ssl,
            verify_certs=self.verify_certs,
            **common_kwargs,
        )

    def get_client(self) -> OpenSearch:
        """
                Retrieve a cached OpenSearch client instance or create a new one if necessary.
        Returns:
            OpenSearch: Configured OpenSearch client instance
        """
        cache_key = f"{self.mode}:{int(self.use_ssl)}:{int(self.verify_certs)}"
        if cache_key not in self.__class__._clients:
            factory = self._factory()
            self.__class__._clients[cache_key] = factory.create()

        return self.__class__._clients[cache_key]
