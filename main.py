from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets Authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(CREDS)

# Google Sheet ID
SHEET_ID = "1UuVLs6AR76KqAfbGX-rkmrr8tiPil3OY_rVtr6xTLN4"  # Change to your actual Google Sheet ID
workbook = client.open_by_key(SHEET_ID)

# Predefined mapping of tags to sheet names
TAG_TO_SHEET = {
    "HSC26": "Sheet1",
    "HSC25": "Sheet2",
    "SSC26": "Sheet3",
    "SSC27": "Sheet4"
}

# Define the request model
class PaymentInput(BaseModel):
    teacher_name: str
    student_name: str
    amount: float
    tag: str  # Example: HSC26, HSC25, SSC26, SSC27

@app.post("/submit-payment/")
async def submit_payment(data: PaymentInput):
    try:
        # Get the corresponding sheet name
        if data.tag not in TAG_TO_SHEET:
            raise HTTPException(status_code=400, detail="Invalid tag. Use HSC26, HSC25, SSC26, or SSC27.")
        
        sheet_name = TAG_TO_SHEET[data.tag]

        # Check if worksheet exists, otherwise create it
        try:
            worksheet = workbook.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = workbook.add_worksheet(title=sheet_name, rows="100", cols="4")
            worksheet.append_row(["Teacher Name", "Student Name", "Amount", "Tag"])  # Add headers

        # Append data to the selected worksheet
        worksheet.append_row([data.teacher_name, data.student_name, data.amount, data.tag])

        return {"message": f"Payment saved successfully in {sheet_name}", "tag": data.tag}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# source venv/bin/activate    
# pip3 install fastapi uvicorn pandas
# pip3 freeze > requirements.txt -> This will save all installed dependencies into the file.

# pip3 uninstall fastapi starlette -y
#pip3 install --upgrade fastapi starlette

# pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib gspread

# uvicorn main:app --reload

#  uvicorn main:app --reload