import json
import logging
import gspread
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Debugging environment variables
print("GOOGLE_CREDENTIALS:", os.getenv("GOOGLE_CREDENTIALS"))
print("GOOGLE_SHEET_ID:", os.getenv("GOOGLE_SHEET_ID"))



logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check if env variables exist
if "GOOGLE_CREDENTIALS" not in os.environ or "GOOGLE_SHEET_ID" not in os.environ:
    logging.error("❌ Environment variables not found!")
    raise RuntimeError("Environment variables missing. Set GOOGLE_CREDENTIALS and GOOGLE_SHEET_ID")

creds_path = "google_credentials.json"
if not os.path.exists(creds_path):
    with open(creds_path, "w") as f:
        f.write(os.environ["GOOGLE_CREDENTIALS"])
        
# Google Sheets Authentication
def get_google_creds():
    try:
        return Credentials.from_service_account_file(
            creds_path, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
    except Exception as e:
        logging.error(f"❌ Error loading Google credentials: {e}")
        raise HTTPException(status_code=500, detail="Invalid Google credentials")

def get_sheets_client():
    creds = get_google_creds()
    return gspread.authorize(creds)

SHEET_ID = os.environ["GOOGLE_SHEET_ID"]

TAG_TO_SHEET = {
    "HSC26": "Sheet1",
    "HSC25": "Sheet2",
    "SSC26": "Sheet3",
    "SSC27": "Sheet4"
}

class PaymentInput(BaseModel):
    teacher_name: str
    student_name: str
    amount: float
    tag: str  

@app.post("/submit-payment/")
async def submit_payment(data: PaymentInput):
    try:
        logging.info(f"✅ Received data: {data}")

        if data.tag not in TAG_TO_SHEET:
            logging.warning(f"❌ Invalid tag: {data.tag}")
            raise HTTPException(status_code=400, detail="Invalid tag. Use HSC26, HSC25, SSC26, or SSC27.")

        # Add debugging info
        logging.info(f"🔍 Using sheet ID: {SHEET_ID}")
        
        client = get_sheets_client()
        logging.info("✅ Google Sheets client created")
        
        workbook = client.open_by_key(SHEET_ID)
        logging.info(f"✅ Workbook opened: {workbook.title}")
        
        sheet_name = TAG_TO_SHEET[data.tag]
        logging.info(f"🔍 Looking for sheet: {sheet_name}")

        try:
            worksheet = workbook.worksheet(sheet_name)
            logging.info(f"✅ Found worksheet: {worksheet.title}")
        except gspread.exceptions.WorksheetNotFound:
            logging.info(f"🆕 Creating new sheet: {sheet_name}")
            worksheet = workbook.add_worksheet(title=sheet_name, rows="100", cols="4")
            worksheet.append_row(["Teacher Name", "Student Name", "Amount", "Tag"])
            logging.info("✅ Added header row to new worksheet")

        # Print row data for debugging
        row_data = [data.teacher_name, data.student_name, data.amount, data.tag]
        logging.info(f"🔍 Appending row: {row_data}")
        
        result = worksheet.append_row(row_data)
        logging.info(f"✅ Append result: {result}")
        logging.info(f"✅ Payment added to {sheet_name}")

        return {"message": f"Payment saved successfully in {sheet_name}", "tag": data.tag}

    except Exception as e:
        logging.error(f"❌ Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
