import logging
import time
import requests
from typing import Dict, Tuple

from utils.api_requests import APIClient
from autoproces_maps import getRunPeriod, getTechnology, getAutoprocesFieldName
from datetime import timedelta

logger = logging.getLogger(__name__)


class AutoprocesAPIClient(APIClient):
    _client_cache: Dict[Tuple[str, str, str, str], 'AutoprocesAPIClient'] = {}

    def __init__(self, base_url, xapi_url, api_key):
        super().__init__(base_url)
        self.base_url = base_url
        self.xapi_url = xapi_url
        self.api_key = api_key
        self.access_token = None
        self.session_cookie = None

    @classmethod
    def get_client(cls, base_url, xapi_url, api_key):
        key = (base_url, xapi_url, api_key)
        if key in cls._client_cache:
            return cls._client_cache[key]
        client = cls(base_url, xapi_url, api_key)
        cls._client_cache[key] = client
        return client

    def request_access_token(self):
        token_url = f"{self.xapi_url}/auth"
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
            self.session_cookie = response.cookies.get('SESSION')  # Save the SESSION cookie
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
            headers = {"X-CSRF-TOKEN": token, "Content-Type": "application/hal+json"}
            if self.session_cookie:
                headers["Cookie"] = f"SESSION={self.session_cookie}"
            return headers
        return None


class AutoprocesClient:
    def __init__(self, base_url, xapi_url, api_key):
        self.api_client = AutoprocesAPIClient.get_client(base_url=base_url, xapi_url=xapi_url, api_key=api_key)
        self.technologies = None

    def get_access_token(self):
        return self.api_client.get_auth_headers()

    def create_epic(self, node_data):
        """
        Create an epic in OS2 Autoproces with the given node data.
        :param node_data: The data to create the epic with, obtained from GitHub API.
        """
        url = f"{self.api_client.base_url}/processes"
        headers = self.api_client.get_auth_headers()
        logger.info("Creating new epic in OS2 Autoproces")

        # Extract the text value of the field with field.name = "Teknologi" if it exists, otherwise use "Ukendt"
        technologies = [
            node.get("name", "Ukendt") for node in node_data.get('fieldValues', {}).get('nodes', [])
            if node.get("field", {}).get("name") == "Teknologi"
        ]
        technologies = [getTechnology(tech, self.get_technologies()['data']) for tech in technologies]

        # Extract description and truncate if necessary
        description = node_data.get('body', '')
        if len(description) > 140:
            description = description[:137] + '...'

        # Extract the run period from danish format
        runperiod = getRunPeriod(node_data.get('runPeriod'))

        # Create data payload
        data = {
            "title": node_data.get('content', {}).get('title'),
            "visibility": "PERSONAL",
            "shortDescription": description,
            "phase": "OPERATION",
            "status": "INPROGRESS",
            "technologies": technologies,
            "runPeriod": runperiod,
            "evaluatedLevelOfRoi": "NOT_SET",
            "levelOfChange": "NOT_SET",
            "levelOfDigitalInformation": "NOT_SET",
            "levelOfProfessionalAssessment": "NOT_SET",
            "levelOfQuality": "NOT_SET",
            "levelOfRoutineWorkReduction": "NOT_SET",
            "levelOfSpeed": "NOT_SET",
            "levelOfStructuredInformation": "NOT_SET",
            "levelOfUniformity": "NOT_SET",
            "codeRepositoryUrl": node_data.get('content', {}).get('repository', {}).get('url'),
        }

        # data['id'] = 460
        # return {'status': 201, 'data': data}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return {'status': 201, 'data': response.json()}
        else:
            logger.error(f"Failed to create epic: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}

    def update_epic(self, os2_autoproces_id, changes):
        """"
        Update an epic in OS2 Autoproces with the given changes.
        :param os2_autoproces_id: The ID of the epic to update.
        :param changes: A list of changes to apply to the epic.
                        Each change should be a dictionary with 'field_name' and 'to' keys.
        """
        url = f"{self.api_client.base_url}/processes/{os2_autoproces_id}"
        headers = self.api_client.get_auth_headers()
        data = {}

        for change in changes:
            field_name = getAutoprocesFieldName(change['field_name'])

            if field_name is not None:
                data[field_name] = change['to']

                if field_name == "technologies":
                    data[field_name] = [getTechnology(data[field_name], self.get_technologies()['data'])]
                elif field_name == "runPeriod":
                    data[field_name] = getRunPeriod(data[field_name])

        # return {'status': 200, 'data': data}
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return {'status': 200, 'response': response.json(), "data": data}
        else:
            logger.error(f"Failed to update epic: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}

    def get_technologies(self):
        """
        Get the list of technologies from OS2 Autoproces.
        """
        if self.technologies:
            return {'status': 200, 'data': self.technologies}

        url = f"{self.api_client.base_url}/technologies"
        headers = self.api_client.get_auth_headers()

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                self.technologies = response.json().get('_embedded', {}).get('technologies', [])
                return {'status': 200, 'data': self.technologies}
            except ValueError:
                logger.error("Failed to parse JSON response")
                return {'status': 500, 'data': None}
        else:
            logger.error(f"Failed to get technologies: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}
