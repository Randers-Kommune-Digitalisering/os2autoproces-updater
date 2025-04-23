import logging
import json

from datetime import timedelta
from flask import Blueprint, Response, request, jsonify

from utils.config import POD_NAME
from utils.config import OS2AUTOPROCES_API_KEY, OS2AUTOPROCES_API_URL, GITHUB_ACCESS_TOKEN, GITHUB_API_URL
from github_client import GithubClient
from autoproces_client import AutoprocesClient

logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api-endpoints', __name__, url_prefix='/api')

os2_client = AutoprocesClient(base_url=OS2AUTOPROCES_API_URL, api_key=OS2AUTOPROCES_API_KEY)
github_client = GithubClient(base_url=GITHUB_API_URL, access_token=GITHUB_ACCESS_TOKEN)


# NB: uncomment code in main.py to enable these endpoints
# Any endpoints added here will be available at /api/<endpoint> - e.g. http://127.0.0.1:8080/api/example
# Change the the example below to suit your needs + add more as needed


@api_endpoints.route('/webhook', methods=['POST'])
def github_webhook():
    try:
        payload = request.get_json(force=True)
        logger.info('Webhook received: ' + json.dumps(payload))
        return jsonify(True), 200
    except Exception as e:
        logger.error(f'Error parsing webhook JSON: {e}')
        return Response('Payload not in JSON format', status=400)


@api_endpoints.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


@api_endpoints.route('/autoproces/token', methods=['GET'])
def autoproces():
    token = os2_client.get_access_token()
    return jsonify({'status': 'ok', 'token': token}), 200


@api_endpoints.route('/github/user', methods=['GET'])
def github_user():
    user = github_client.get_user()
    if user:
        return jsonify(user), 200
    else:
        return jsonify({'error': 'Failed to fetch user'}), 500
