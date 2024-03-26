from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import boto3
from fastapi.responses import Response
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import os
import zipfile
import io

load_dotenv()

app = FastAPI()

global OPENAI_API_KEY
global ZIP_FILE_NAME

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Retrieve environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

global OPENAI_API_KEY
global ZIP_FILE_NAME

@app.get("/")
async def test_endpoint():
    return {"message": "Success! Your BoostioAI FastAPI application is working correctly."}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), openai_api_key: str = None):

    if not file.content_type.startswith('application/zip'):
        raise HTTPException(status_code=415, detail="Unsupported file type. Only ZIP files are accepted.")
    try:
        zip_content = await file.read()
        ZIP_FILE_NAME = os.path.basename(file.filename)  # Store the file name in the global variable

        # Store the received OpenAI API key in the global variable
        OPENAI_API_KEY = openai_api_key

        # Write the zip file content to S3
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=ZIP_FILE_NAME, Body=zip_content)

        return {"message": "File uploaded successfully", "filename": ZIP_FILE_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wa")  # Use @app.post to allow POST requests to the /wa endpoint
async def get_insights_from_zip():
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=ZIP_FILE_NAME)
        print(response)
        zip_content = response['Body'].read()

        # Read the zip file content and extract text from it
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            # Assuming there's only one text file in the zip
            text_file = [file for file in zip_ref.namelist() if file.endswith(".txt")]
            if text_file:
                with zip_ref.open(text_file[0]) as f:
                    text = f.read().decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="No text file found in the zip")

        # Send the text as a message to the OpenAI API
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": "Analyze the following conversation."},
                {"role": "user", "content": text}
            ]
        )

        return completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
