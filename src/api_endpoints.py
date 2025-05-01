import logging

from flask import Blueprint, Response, request, jsonify
from utils.config import OS2AUTOPROCES_API_KEY, OS2AUTOPROCES_API_URL, OS2AUTOPROCES_XAPI_URL, GITHUB_ACCESS_TOKEN, GITHUB_API_URL, GITHUB_PROJECT_ID, GITHUB_OS2AUTOPROCES_FIELD_ID
from github_client import GithubClient
from autoproces_client import AutoprocesClient
from autoproces_maps import getTechnology
# from openai_client import create_shortDescription

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

    # Check if update is issue (i.e. updated description)
    if payload.get('issue'):
        if payload['action'] == 'edited':
            logger.info(f"Received issue update: {payload['action']}")
            issue_id = payload['issue']['node_id']

            # Get project item data from GitHub
            epic = github_client.get_issue_from_id(issue_id)
            if epic['status'] != 200:
                logger.error(f"Failed to fetch epic data for issue ID {issue_id}: {epic.get('error', 'Unknown error')}")
                return Response('Failed to fetch epic data', status=500)

            # Check if the epic is marked as deployed - true if epic has an OS2 Autoproces ID
            project_items = epic.get('data', {}).get('data', {}).get('node', {}).get('projectItems', {}).get('nodes', [])
            for project_item in project_items:
                for field in project_item.get('fieldValues', {}).get('nodes', []):

                    if field.get('field', {}).get('name') == 'OS2 Autoproces ID':
                        os2_autoproces_id = field.get('text')
                        if os2_autoproces_id:  # OS2 Autoproces ID is already set
                            logger.info(f"Epic with issue ID {issue_id} already exists in OS2 Autoproces with ID {os2_autoproces_id}")

            # Store changes made to epic
            if os2_autoproces_id:
                for key in payload['changes'].keys():
                    if payload['changes'][key].get('from', None):
                        changes.append({
                            'field_name': key,
                            'from': payload['changes'][key].get('from'),
                            'to': payload['issue'].get(key, None)
                        })

    # Check if update is project item (i.e. updated field value)
    elif payload.get('projects_v2_item'):
        if payload['action'] == 'edited':
            node_id = payload['projects_v2_item']['node_id']

            # Get issue data from GitHub
            epic = github_client.get_issue_from_node(node_id)
            if epic['status'] != 200:
                logger.error(f"Failed to fetch epic data for project node ID {node_id}: {epic.get('error', 'Unknown error')}")
                return Response('Failed to fetch epic data', status=500)

            # Check if the epic is marked as deployed - true if epic has an OS2 Autoproces ID
            if epic.get('data', {}).get('data', {}).get('node', {}).get('fieldValues', {}).get('nodes'):
                for field in epic['data']['data']['node']['fieldValues']['nodes']:

                    if field.get('field', {}).get('name') == 'OS2 Autoproces ID':
                        os2_autoproces_id = field.get('text')
                        if os2_autoproces_id:  # OS2 Autoproces ID is already set
                            logger.info(f"Epic with project node ID {node_id} already exists in OS2 Autoproces with ID {os2_autoproces_id}")

            # Check new changes to field values
            if payload['changes'].get('field_value'):
                field_values = payload['changes']['field_value']
                if not isinstance(field_values, list):
                    field_values = [field_values]

                is_deployed = os2_autoproces_id is not None
                for field in field_values:
                    # Check if newly deployed, unless OS2 Autoproces ID is already set
                    if os2_autoproces_id is None and field.get('field_name') == 'Fase':
                        if field.get('to').get('name'):
                            if '6. Driftstest' in field['to']['name'] or '7. Drift' in field['to']['name']:

                                # Create epic in OS2 Autoproces and update field value in GitHub
                                response = os2_client.create_epic(epic['data']['data']['node'])
                                if response['status'] == 201:
                                    os2_autoproces_id = response['data'].get('id')
                                    logger.info(f"Epic {node_id} created OS2 Autoproces")
                                else:
                                    logger.error(f"Failed to create epic in OS2 Autoproces: {response.get('errors')}")
                                    return Response('Failed to create epic in OS2 Autoproces', status=500)

                                # Update field value in GitHub after creating epic
                                response = github_client.update_field_value(GITHUB_PROJECT_ID, node_id, GITHUB_OS2AUTOPROCES_FIELD_ID, os2_autoproces_id)
                                if response['status'] == 200:
                                    logger.info(f"Epic {node_id} updated with OS2 Autoproces ID {os2_autoproces_id} in GitHub")
                                else:
                                    logger.error(f"Failed to update field value in GitHub: {response.get('errors')}")
                                    return Response('Failed to update field value in GitHub', status=500)

                    elif is_deployed is True:
                        # Store other changes made to epic
                        changes.append({
                            'field_name': field.get('field_name'),
                            'field_id': field.get('field_node_id'),
                            'from': field.get('from').get('name', field.get('from').get('text')) if isinstance(field.get('from'), dict) else field.get('from') if isinstance(field.get('from'), str) else None,
                            'to': field.get('to').get('name', field.get('to').get('text')) if isinstance(field.get('to'), dict) else field.get('to') if isinstance(field.get('to'), str) else None
                        })

    # Update in OS2 Autoproces with changes
    if len(changes) > 0:
        response = os2_client.update_epic(os2_autoproces_id, changes)
        if response['status'] == 200:
            if response.get('data') and len(response.get('data')) > 0:
                logger.info(f"Epic {os2_autoproces_id} updated in OS2 Autoproces with changes: {response.get('data')}")
        else:
            logger.error(f"Failed to update epic in OS2 Autoproces: {response.get('errors')}")
            return Response('Failed to update epic in OS2 Autoproces', status=500)

    return jsonify({"os2uid": os2_autoproces_id or None, "changes": changes}), 200


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


# @api_endpoints.route('/shortDescription', methods=['POST'])
# def short_description():
#     data = request.get_json()
#     if not data or 'message' not in data:
#         return jsonify({'error': 'Invalid input'}), 400

#     message = data['message']
#     short_description = create_shortDescription(message)
#     if short_description:
#         return jsonify({'shortDescription': short_description}), 200
#     else:
#         return jsonify({'error': 'Failed to generate short description'}), 500

# @api_endpoints.route('/autoproces/headers', methods=['GET'])
# def autoproces():
#     headers = os2_client.get_access_token()
#     return jsonify({'status': 'ok', 'headers': headers}), 200


# @api_endpoints.route('/github/epic/<string:node_id>', methods=['GET'])
# def get_project_issue(node_id):
#     result = github_client.get_issue_from_node(node_id)
#     if result['status'] == 200:
#         return jsonify(result['data']), 200
#     elif result['status'] == 404:
#         return jsonify({'error': 'Epic not found'}), 404
#     else:
#         return jsonify({'error': 'Failed to fetch epic'}), 500


# @api_endpoints.route('/github/issue/<string:issue_id>', methods=['GET'])
# def github_issue(issue_id):
#     result = github_client.get_issue_from_id(issue_id)
#     if result['status'] == 200:
#         return jsonify(result['data']), 200
#     elif result['status'] == 404:
#         return jsonify({'error': 'Issue not found'}), 404
#     else:
#         return jsonify({'error': 'Failed to fetch issue'}), 500
