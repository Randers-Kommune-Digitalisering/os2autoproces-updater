import logging
import time
import requests
from typing import Dict, Tuple

from utils.api_requests import APIClient
from datetime import timedelta

logger = logging.getLogger(__name__)


class AutoprocesAPIClient(APIClient):
    _client_cache: Dict[Tuple[str, str, str, str], 'AutoprocesAPIClient'] = {}

    def __init__(self, base_url, api_key):
        super().__init__(base_url)
        self.base_url = base_url
        self.api_key = api_key
        self.access_token = None

    @classmethod
    def get_client(cls, base_url, api_key):
        key = (base_url, api_key)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(base_url, api_key)
        cls._client_cache[key] = client
        return client

    def request_access_token(self):
        token_url = f"{self.base_url}/auth"
        headers = {
            "ApiKey": self.api_key,
            "Content-Type": "application/hal+json"
        }
        logger.info(f"Requesting access token from {token_url} with headers: {headers}")
        try:
            if not token_url.startswith("https://"):
                token_url = "https://" + token_url
            response = requests.post(token_url, headers=headers, timeout=20)
            response.raise_for_status()
            self.access_token = response.headers.get('X-CSRF-TOKEN')
            self.access_token_expiry = time.time() + timedelta(hours=6).total_seconds()  # Assuming the token is valid for 6 hours
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to request access token: {e}")
            return None

    def get_access_token(self):
        if self.access_token and self.access_token_expiry:
            if time.time() < self.access_token_expiry:
                return self.access_token
        return self.request_access_token()

    def get_auth_headers(self):
        token = self.get_access_token()
        if token:
            return {"X-CSRF-TOKEN": token}
        return None


class AutoprocesClient:
    def __init__(self, base_url, api_key):
        self.api_client = AutoprocesAPIClient.get_client(base_url=base_url, api_key=api_key)

    def get_access_token(self):
        return self.api_client.get_auth_headers()
