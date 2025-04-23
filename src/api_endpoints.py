import logging
import json

from datetime import timedelta
from flask import Blueprint, Response, request, jsonify

from utils.config import POD_NAME
from utils.config import OS2AUTOPROCES_API_KEY, OS2AUTOPROCES_API_URL
from autoproces_client import AutoprocesClient

logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api-endpoints', __name__, url_prefix='/api')
client = AutoprocesClient(base_url=OS2AUTOPROCES_API_URL, api_key=OS2AUTOPROCES_API_KEY)


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


@api_endpoints.route('/autoproces', methods=['GET'])
def autoproces():
    token = client.get_access_token()
    return jsonify({'status': 'ok', 'token': token}), 200
