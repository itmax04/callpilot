import json, os, tempfile
from pathlib import Path
import azure.functions as func
from callpilot.models import Transcript
from callpilot.providers import DemoProvider
app=func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
@app.route(route='analyze', methods=['POST'])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    try:
        t=Transcript.model_validate(req.get_json())
        result=DemoProvider(Path(__file__).resolve().parents[1]/'data').analyze(t,'v2')
        # Blob persistence is opt-in; no cloud resource is created by this repository.
        if os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
            from azure.storage.blob import BlobServiceClient
            c=BlobServiceClient.from_connection_string(os.environ['AZURE_STORAGE_CONNECTION_STRING'])
            container=os.getenv('AZURE_BLOB_CONTAINER','callpilot-results'); c.get_container_client(container).upload_blob(f'{t.call_id}.json',result.model_dump_json(),overwrite=True)
        return func.HttpResponse(result.model_dump_json(),mimetype='application/json')
    except Exception as e: return func.HttpResponse(json.dumps({'error':str(e)}),status_code=400,mimetype='application/json')
