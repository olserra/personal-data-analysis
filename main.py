from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import boto3
from fastapi.responses import Response
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from openai import OpenAI
import os

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

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

class Author(BaseModel):
    role: str
    name: Optional[str] = None
    metadata: Dict[str, Any]

class Message(BaseModel):
    id: str
    author: Author
    create_time: Optional[float] = None
    update_time: Optional[float] = None
    content: Dict[str, Any]
    status: str
    end_turn: Optional[bool] = None
    weight: int
    metadata: Dict[str, Any]
    recipient: str

class Mapping(BaseModel):
    id: str
    message: Optional[Message] = None
    parent: Optional[str] = None
    children: List[str]

class Conversation(BaseModel):
    title: str
    create_time: float
    update_time: float
    mapping: Dict[str, Mapping]

class InsightRequest(BaseModel):
    conversations: List[Conversation]

@app.post("/insights")
async def get_insights(request: InsightRequest):
    client = OpenAI()
    
    try:
        # Extract the last 99 conversations, ensure they are serialized properly
        last_conversation = request.conversations[-1]

        last_conversation_str = json.dumps(last_conversation.dict(), ensure_ascii=False)
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Analyze the following conversation for patterns, common mistakes, and learning improvements:"},
                {"role": "user", "content": last_conversation_str}
            ]
        )
        
        return {"completion": completion.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/profiler")
async def download_conversation():
    file_name = "conversations.json"
    try:
        # Fetch the file from S3
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)
        
        # Read the file content
        file_content = response['Body'].read()
        
        return Response(content=file_content, media_type='application/json')
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except ClientError as e:
        # Handle specific client errors differently
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="File not found")
        else:
            raise HTTPException(status_code=500, detail="S3 Client Error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
