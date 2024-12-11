from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from aiagents.crew import StartCrewInitialization
from aiagents.config import configuration
app = FastAPI()
from uuid import uuid4
import traceback
import json
from os import path, makedirs


@app.post("/upload-json/")
async def upload_json(file: UploadFile = File(...)):
    try:
        # Read the contents of the uploaded JSON file
        contents = await file.read()
        if not path.exists(configuration.swagger_files_directory):
            makedirs(configuration.swagger_files_directory)
        # Save the uploaded Swagger file in the designated directory
        file_path = path.join(
            configuration.swagger_files_directory, file.filename
        )
        # need to handle duplicate summary stuff
        file_content = json.loads(contents.decode())
        with open(file_path, "w") as file:
            json.dump(file_content, file, indent=4)
        try:

        # You can parse the JSON here
            configuration.update_config_upload()
            StartCrewInitialization(configuration)
        except Exception as e:
            traceback.print_exc()
            error_trace = traceback.format_exc()
            return JSONResponse(content={"error": error_trace}, status_code=400)
        # Process the data as needed
        return JSONResponse(content={"message": "JSON received and crew summary completed successfuly"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    
