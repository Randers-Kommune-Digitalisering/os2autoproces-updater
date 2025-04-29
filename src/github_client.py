import logging
import requests
from typing import Dict, Tuple
from utils.api_requests import APIClient

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

    def get_issue_from_node(self, node_id):
        query = """
        query($node_id: ID!) {
            node(id: $node_id) {
                ... on ProjectV2Item {
                    id
                    fieldValues(first: 100) {
                        nodes {
                            ... on ProjectV2ItemFieldTextValue {
                                text
                                field {
                                    ... on ProjectV2FieldCommon {
                                        id
                                        name
                                    }
                                }
                            }
                            ... on ProjectV2ItemFieldDateValue {
                                date
                                field {
                                    ... on ProjectV2FieldCommon {
                                        id
                                        name
                                    }
                                }
                            }
                            ... on ProjectV2ItemFieldSingleSelectValue {
                                name
                                field {
                                    ... on ProjectV2FieldCommon {
                                        id
                                        name
                                    }
                                }
                            }
                        }
                    }
                    content {
                        ... on DraftIssue {
                            title
                            body
                        }
                        ... on Issue {
                            title
                            body
                            repository {
                                name
                                url
                            }
                            assignees(first: 10) {
                                nodes {
                                    login
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {"node_id": node_id}
        url = f"{self.api_client.url}/graphql"
        headers = self.api_client.get_auth_headers()
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        if response.status_code == 200:
            return {'status': 200, 'data': response.json()}
        elif response.status_code == 404:
            logger.error("Issue not found")
            return {'status': 404, 'data': None}
        else:
            logger.error(f"Failed to fetch issue: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}

    def update_field_value(self, project_id, node_id, field_id, value):
        logger.info(f"Updating field value for node {node_id} in project {project_id} with field {field_id} to {value}")
        query = """
        mutation($node_id: ID!, $value: String!, $field_id: ID!, $project_id: ID!) {
            updateProjectV2ItemFieldValue(input: {
                projectId: $project_id,
                itemId: $node_id,
                value: { text: $value },
                fieldId: $field_id
            }) {
                projectV2Item {
                    id
                }
            }
        }
        """
        variables = {"project_id": project_id, "node_id": node_id, "field_id": field_id, "value": value}
        url = f"{self.api_client.url}/graphql"
        headers = self.api_client.get_auth_headers()
        response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        if response.status_code == 200:
            return {'status': 200, 'data': response.json()}
        else:
            logger.error(f"Failed to update field value: {response.status_code} - {response.text}")
            return {'status': response.status_code, 'data': None}
