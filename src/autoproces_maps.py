import logging
from utils.config import OS2AUTOPROCES_API_URL

logger = logging.getLogger(__name__)


def getRunPeriod(run_period):
    mapping = {
        "Løbende kørsel": "ONDEMAND",
        "Engangskørsel": "ONCE",
        "Dagligt": "DAILY",
        "Ugentligt": "WEEKLY",
        "Månedligt": "MONTHLY",
        "Hvert kvartal": "QUATERLY",
        "Årligt": "YEARLY"
    }
    return mapping.get(run_period) or "ONDEMAND"


def getTechnology(technology, list):
    logger.info('Mapping technology: %s', technology)
    if not list:
        logger.error('Technology list is empty or None')
        return None
    result = next((item for item in list if item.get("name").lower() == technology.lower()), None)
    return f"{OS2AUTOPROCES_API_URL}/technologies/{result['id']}" if result else None


def getAutoprocesFieldName(github_field_name):
    mapping = {
        "Teknologi": "technologies",
        "Skedulering": "runPeriod",
        "body": "description",
        "title": "title"
    }
    return mapping.get(github_field_name) or None
