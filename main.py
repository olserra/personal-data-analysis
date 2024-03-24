from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import boto3
from fastapi.responses import Response
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import os
import json
from langchain.agents import (
    create_json_agent,
    AgentExecutor
)
from langchain_community.agent_toolkits import JsonToolkit
from langchain.chains import LLMChain
from langchain.llms.openai import OpenAI
from langchain.requests import TextRequestsWrapper
from langchain.tools.json.tool import JsonSpec

load_dotenv()

app = FastAPI()

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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

file_name = "conversations.json"

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)


@app.post("/insights")
async def get_insights():
    try:
        file_name = "conversations.json"
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)

        # Correctly reading the file content from S3 response
        file_content = response['Body'].read()
        data = json.loads(file_content)

        data = json.loads(file_content)
        # Wrap the list in a dictionary if it's not already a dict
        if isinstance(data, list):
            data = {"conversations": data}

        json_spec = JsonSpec(dict_=data, max_value_length=16000)
        json_toolkit = JsonToolkit(spec=json_spec)

        json_agent_executor = create_json_agent(
            llm=OpenAI(api_key=OPENAI_API_KEY, temperature=0),
            model_name="gpt-3.5-turbo", 
            toolkit=json_toolkit,
            verbose=True
        )

        insights = json_agent_executor.run("Analyze the following conversation for patterns, common mistakes, and learning improvements")
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

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
