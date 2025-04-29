import logging

from flask import Blueprint, Response, request, jsonify
from utils.config import OS2AUTOPROCES_API_KEY, OS2AUTOPROCES_API_URL, OS2AUTOPROCES_XAPI_URL, GITHUB_ACCESS_TOKEN, GITHUB_API_URL, GITHUB_PROJECT_ID, GITHUB_OS2AUTOPROCES_FIELD_ID
from github_client import GithubClient
from autoproces_client import AutoprocesClient
from autoproces_maps import getTechnology

logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api-endpoints', __name__, url_prefix='/api')

os2_client = AutoprocesClient(base_url=OS2AUTOPROCES_API_URL, xapi_url=OS2AUTOPROCES_XAPI_URL, api_key=OS2AUTOPROCES_API_KEY)
github_client = GithubClient(base_url=GITHUB_API_URL, access_token=GITHUB_ACCESS_TOKEN)


@api_endpoints.route('/webhook', methods=['POST'])
def github_webhook():
    # Get payload from GitHub webhook
    try:
        payload = request.get_json(force=True)
    except Exception as e:
        logger.error(f'Error parsing webhook JSON: {e}')
        return Response('Payload not in JSON format', status=400)

    # Updated project epic
    os2_autoproces_id = None
    changes = []

    if payload.get('projects_v2_item'):
        if payload['action'] == 'edited':
            node_id = payload['projects_v2_item']['node_id']

            # Get issue data from GitHub
            epic = github_client.get_issue_from_node(node_id)
            if epic['status'] != 200:
                logger.error(f"Failed to fetch epic data for node_id {node_id}: {epic['error']}")
                return Response('Failed to fetch epic data', status=500)

            # Check if the epic is marked as deployed
            if epic.get('data', {}).get('data', {}).get('node', {}).get('fieldValues', {}).get('nodes'):
                for field in epic['data']['data']['node']['fieldValues']['nodes']:

                    # Check if epic has an OS2 Autoproces ID
                    if field.get('field', {}).get('name') == 'OS2 Autoproces ID':
                        os2_autoproces_id = field.get('text')
                        if os2_autoproces_id:  # OS2 Autoproces ID is already set
                            logger.info(f"Epic {node_id} already exists in OS2 Autoproces with ID {os2_autoproces_id}")

            # Check new changes to field values
            if payload['changes'].get('field_value'):
                field_values = payload['changes']['field_value']
                if not isinstance(field_values, list):
                    field_values = [field_values]

                for field in field_values:
                    # Check if newly deployed, unless OS2 Autoproces ID is already set
                    if os2_autoproces_id is None and field.get('field_name') == 'Fase':
                        if field.get('to').get('name'):
                            if '6. Driftstest' in field['to']['name'] or '7. Drift' in field['to']['name']:

                                # Create epic in OS2 Autoproces and update field value in GitHub
                                response = os2_client.create_epic(epic['data']['data']['node'])
                                if response['status'] == 201:
                                    os2_autoproces_id = response['data'].get('id')
                                else:
                                    logger.error(f"Failed to create epic in OS2 Autoproces: {response['error']}")
                                    return Response('Failed to create epic in OS2 Autoproces', status=500)

                                # Update field value in GitHub after creating epic
                                github_client.update_field_value(GITHUB_PROJECT_ID, node_id, GITHUB_OS2AUTOPROCES_FIELD_ID, os2_autoproces_id)
                                logger.info(f"Epic {node_id} created OS2 Autoproces and ID updated in GitHub")

                    else:
                        # Store other changes made to epic
                        changes.append({
                            'field_name': field.get('field_name'),
                            'field_id': field.get('field_node_id'),
                            'from': field.get('from').get('name', field.get('from').get('text')) if field.get('from') else None,
                            'to': field.get('to').get('name', field.get('to').get('text')) if field.get('to') else None
                        })

                if os2_autoproces_id and len(changes) > 0:
                    # for change in changes:
                    response = os2_client.update_epic(os2_autoproces_id, changes)
                    logger.info(f"Updating epic with OS2 uid {os2_autoproces_id} in OS2 Autoproces with changes: {changes}")

    return jsonify({"response": response, "os2uid": os2_autoproces_id}), 200


@api_endpoints.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


@api_endpoints.route('/technologies', methods=['GET'])
def get_technologies():
    technologies = os2_client.get_technologies()
    if technologies['status'] == 200:
        return jsonify(technologies), 200
    else:
        return jsonify({'error': 'Failed to fetch technologies'}), 500


@api_endpoints.route('/technologies/<string:technology>', methods=['GET'])
def get_technology(technology):
    technologies = os2_client.get_technologies()

    if technologies['status'] == 200:
        result = getTechnology(technology, technologies['data'])
        return jsonify(result), 200
    else:
        return jsonify({'error': 'Failed to fetch technologies'}), 500


@api_endpoints.route('/autoproces/headers', methods=['GET'])
def autoproces():
    headers = os2_client.get_access_token()
    return jsonify({'status': 'ok', 'headers': headers}), 200


@api_endpoints.route('/github/epic/<string:node_id>', methods=['GET'])
def get_project_issue(node_id):
    result = github_client.get_issue_from_node(node_id)
    if result['status'] == 200:
        return jsonify(result['data']), 200
    elif result['status'] == 404:
        return jsonify({'error': 'Epic not found'}), 404
    else:
        return jsonify({'error': 'Failed to fetch epic'}), 500


# @api_endpoints.route('/github/issue/<string:issue_id>', methods=['GET'])
# def github_issue(issue_id):
#     result = github_client.get_issue_from_node(issue_id)
#     if result['status'] == 200:
#         return jsonify(result['data']), 200
#     elif result['status'] == 404:
#         return jsonify({'error': 'Issue not found'}), 404
#     else:
#         return jsonify({'error': 'Failed to fetch issue'}), 500
