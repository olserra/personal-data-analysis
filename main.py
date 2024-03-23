from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's domain for production
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

@app.get("/")
async def test_endpoint():
    return {"message": "Success! Your BoostioAI FastAPI application is working correctly."}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type != 'application/json':
        raise HTTPException(status_code=415, detail="Unsupported file type. Only JSON files are accepted.")
    try:
        file_content = await file.read()
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file.filename, Body=file_content)
        return {"message": "File uploaded successfully", "filename": file.filename}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
