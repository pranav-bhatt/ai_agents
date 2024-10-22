from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from aiagents.crew import StartCrewInitialization
from aiagents.config import configuration
app = FastAPI()
import os
import traceback


@app.post("/upload-json/")
async def upload_json(file: UploadFile = File(...)):
    try:
        # Read the contents of the uploaded JSON file
        contents = await file.read()
        # save the contents in a json file
        with open("uploaded_file.json", "wb") as f:
            f.write(contents)
        try:

        # You can parse the JSON here
            configuration.__init__()
            StartCrewInitialization(configuration)
        except Exception as e:
            traceback.print_exc()
            error_trace = traceback.format_exc()
            return JSONResponse(content={"error": error_trace}, status_code=400)
        # Process the data as needed
        return JSONResponse(content={"message": "JSON received and crew started successfully"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    
