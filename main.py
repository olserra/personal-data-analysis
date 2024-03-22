from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = "your-access-key"
AWS_SECRET_ACCESS_KEY = "your-secret-key"
AWS_BUCKET_NAME = "your-bucket-name"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    # If you're using a specific AWS region, specify it here, e.g., 'eu-west-1'
)

@app.post("/upload/")
async def upload_pdf_to_s3(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file format.")

    try:
        # Upload to S3
        s3_client.upload_fileobj(
            file.file,
            AWS_BUCKET_NAME,
            file.filename,
            ExtraArgs={'ContentType': 'application/pdf'},
        )
        return {"message": f"Successfully uploaded {file.filename} to S3."}

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="Could not connect to AWS with provided credentials.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
