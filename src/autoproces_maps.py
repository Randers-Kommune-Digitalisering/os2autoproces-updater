from utils.config import OS2AUTOPROCES_API_URL


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
    if not list:
        return None
    result = next((item for item in list if item.get("name").lower() == technology.lower()), None)
    return f"{OS2AUTOPROCES_API_URL}/technologies/{result['id']}" if result else None
