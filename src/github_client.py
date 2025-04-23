import logging
import time
import requests
from typing import Dict, Tuple
from utils.api_requests import APIClient
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class GithubAPIClient(APIClient):
    _client_cache: Dict[Tuple[str, str, str, str], 'GithubAPIClient'] = {}

    def __init__(self, base_url, access_token):
        super().__init__(base_url)
        self.url = base_url
        self.access_token = access_token

    @classmethod
    def get_client(cls, base_url, access_token):
        key = (base_url, access_token)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(base_url, access_token)
        cls._client_cache[key] = client
        return client

    def get_access_token(self):
        return self.access_token

    def get_auth_headers(self):
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None


class GithubClient:
    def __init__(self, base_url, access_token):
        self.api_client = GithubAPIClient.get_client(base_url, access_token)

    def get_issues(self, repo, state='open'):
        url = f"{self.api_client.url}/repos/{repo}/issues"
        headers = self.api_client.get_auth_headers()
        params = {'state': state}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch issues: {response.status_code} - {response.text}")
            return None

    def get_user(self):
        url = f"{self.api_client.url}/user"
        headers = self.api_client.get_auth_headers()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch user: {response.status_code} - {response.text}")
            return None
