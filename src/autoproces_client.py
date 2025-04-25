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

    def create_epic(self, node_data):
        return {'status': 201, 'data': {'id': 'test-id'}}
        """
        Create an epic in OS2 Autoproces with the given node data.
        :param node_data: The data to create the epic with, obtained from GitHub API.
        """
        # return {'id': 100, 'status': 200, 'data': 'test'}
        url = f"{self.api_client.base_url}/processes"
        headers = self.api_client.get_auth_headers()

        # Extract the text value of the field with field.name = "Teknologi" if it exists
        technologies = [
            node.get("text") for node in node_data.get('fieldValues', {}).get('nodes', [])
            if node.get("field", {}).get("name") == "Teknologi"
        ]

        # Extract description and truncate if necessary
        description = node_data.get('body', '')
        if len(description) > 140:
            description = description[:137] + '...'

        # Extract the run period from danish format
        def switch(run_period):
            mapping = {
                "Løbende kørsel": "ONDEMAND",
                "Engangskørsel": "ONCE",
                "Dagligt": "DAILY",
                "Ugentligt": "WEEKLY",
                "Månedligt": "MONTHLY",
                "Hvert kvartal": "QUATERLY",
                "Årligt": "YEARLY"
            }
            return mapping.get(run_period)
        runperiod = switch(node_data.get('runPeriod', 'ONDEMAND'))

        # Create data payload
        data = {
            "title": node_data.get('content', {}).get('title'),
            "visibility": "PUBLIC",
            "shortDescription": description,
            "phase": "OPERATION",
            "status": "INPROGRESS",
            "technologies": technologies,
            "runPeriod": runperiod
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return {'status': 201, 'data': response.json()}
        else:
            logger.error(f"Failed to create epic: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}

    def update_epic(self, os2_autoproces_id, changes):
        return {'status': 200, 'data': 'test'}
        """"
        Update an epic in OS2 Autoproces with the given changes.
        :param os2_autoproces_id: The ID of the epic to update.
        :param changes: A list of changes to apply to the epic.
                        Each change should be a dictionary with 'field_name' and 'to' keys.
        """
        url = f"{self.api_client.base_url}/processes"
        headers = self.api_client.get_auth_headers()
        data = {
            "id": os2_autoproces_id
        }

        # TODO: Create map between field names and OS2 Autoproces field names
        for change in changes:
            data[change['field_name']] = change['to']

        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return {'status': 200, 'data': response.json()}
        else:
            logger.error(f"Failed to update epic: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}
