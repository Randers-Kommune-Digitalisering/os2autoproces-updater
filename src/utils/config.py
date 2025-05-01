import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

# DB_USER = os.environ["DB_USER"].strip()
# DB_PASS = os.environ["DB_PASS"].strip()
# DB_HOST = os.environ["DB_HOST"].strip()
# DB_PORT = os.environ["DB_PORT"].strip()
# DB_DATABASE = os.environ["DB_DATABASE"].strip()

OS2AUTOPROCES_API_KEY = os.getenv('OS2AUTOPROCES_API_KEY', None).strip() if os.getenv('OS2AUTOPROCES_API_KEY') else None
OS2AUTOPROCES_API_URL = os.getenv('OS2AUTOPROCES_API_URL', None).strip() if os.getenv('OS2AUTOPROCES_API_URL') else None
OS2AUTOPROCES_XAPI_URL = os.getenv('OS2AUTOPROCES_XAPI_URL', None).strip() if os.getenv('OS2AUTOPROCES_XAPI_URL') else None

GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN', None).strip() if os.getenv('GITHUB_ACCESS_TOKEN') else None
GITHUB_API_URL = os.getenv('GITHUB_API_URL', None).strip() if os.getenv('GITHUB_API_URL') else None
GITHUB_PROJECT_ID = os.getenv('GITHUB_PROJECT_ID', None).strip() if os.getenv('GITHUB_PROJECT_ID') else None
GITHUB_ORG = os.getenv('GITHUB_ORG', None).strip() if os.getenv('GITHUB_ORG') else None
GITHUB_OS2AUTOPROCES_FIELD_ID = os.getenv('GITHUB_OS2AUTOPROCES_FIELD_ID', None).strip() if os.getenv('GITHUB_OS2AUTOPROCES_FIELD_ID') else None

AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', None).strip() if os.getenv('AZURE_OPENAI_API_KEY') else None
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', None).strip() if os.getenv('AZURE_OPENAI_ENDPOINT') else None
AZURE_DEPLOYMENT_NAME = os.getenv('AZURE_DEPLOYMENT_NAME', None).strip() if os.getenv('AZURE_DEPLOYMENT_NAME') else None
