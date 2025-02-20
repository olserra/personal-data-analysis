# Personal Data Analysis

## Introduction

Bridging the Human-AI With Your Own Data. Seamlessly integrate metadata to forge a bridge between human intelligence and your AI, enhancing its ability to learn from decentralized, blockchain-protected digital profiles ready for web-wide application.

## API Endpoints

### Upload Endpoint

- **URL:** `/upload`
- **Method:** `POST`
- **Description:** Uploads a file to the AWS S3 bucket.
- **Body:** `multipart/form-data` with a key of `pdfData` and the value being the file.
- **Headers:**
  - `Content-Type: multipart/form-data`
  - `x-user-id: User's unique identifier`
- **Success Response:** Code: 200, Content: `{ message: "File uploaded successfully", filename: "uploadedFileName.pdf" }`
- **Error Response:** Code: 500, Content: `{ error: "Error message" }`

### Test Endpoint

- **URL:** `/`
- **Method:** `GET`
- **Description:** A simple endpoint to test if the API is working.
- **Success Response:** Code: 200, Content: `{ message: "Success! Your FastAPI application is working correctly." }`
