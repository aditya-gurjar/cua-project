from fastapi import FastAPI, File, UploadFile, Form, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Import the email extraction function
from simple_eml_parser import extract_email_content, save_extracted_content
# Import the Scrapybara automation class
from scrapybara_automation import EZLynxFormAutomation

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directories if they don't exist
UPLOAD_DIR = Path("uploads")
CREDENTIALS_FILE = Path("credentials.json")
EMAIL_CONTENT_FILE = Path("extracted_email.json")
UPLOAD_DIR.mkdir(exist_ok=True)

# Global instance of the automation
automation_instance = None
automation_task = None

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    destination_url: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    # Save the .eml file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Save credentials
    credentials = {
        "destination_url": destination_url,
        "username": username,
        "password": password,
        "eml_file": str(file_path)
    }
    
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f)
    
    # Extract email content
    try:
        email_content = extract_email_content(str(file_path))
        save_extracted_content(email_content, str(EMAIL_CONTENT_FILE))
        
        return {
            "filename": file.filename, 
            "saved_to": str(file_path), 
            "credentials_saved": True,
            "email_content": email_content
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "filename": file.filename,
                "saved_to": str(file_path),
                "credentials_saved": True,
                "extraction_error": str(e)}
        )

@app.get("/email-content")
async def get_email_content():
    """Endpoint to retrieve the extracted email content."""
    if not EMAIL_CONTENT_FILE.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "No extracted email content available"}
        )
    
    with open(EMAIL_CONTENT_FILE, "r") as f:
        data = json.load(f)
    
    return data

# Function to run the automation in the background
async def run_automation():
    """Run the automation process in the background."""
    global automation_instance
    
    try:
        # Initialize automation instance
        automation_instance = EZLynxFormAutomation(
            credentials_file=str(CREDENTIALS_FILE),
            email_content_file=str(EMAIL_CONTENT_FILE)
        )
        
        # Run the full automation process
        await automation_instance.run_automation()
    except Exception as e:
        print(f"Error in automation: {str(e)}")
        if automation_instance:
            await automation_instance.cleanup()

@app.post("/start-automation")
async def start_automation(background_tasks: BackgroundTasks):
    """Start the form filling automation process."""
    global automation_instance, automation_task
    
    # Check if automation is already running
    if automation_instance and automation_instance.status not in ["error", "completed", "waiting_for_input"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Automation is already running"}
        )
    
    # Start a new automation instance in the background
    background_tasks.add_task(run_automation)
    
    return {"message": "Automation process started in the background"}

@app.post("/provide-input")
async def provide_human_input(input_data: Dict[str, Any] = Body(...)):
    """Provide human input to the automation process."""
    global automation_instance
    
    if not automation_instance:
        return JSONResponse(
            status_code=404,
            content={"error": "No automation has been started"}
        )
    
    if automation_instance.status != "waiting_for_input":
        return JSONResponse(
            status_code=400,
            content={"error": "Automation is not waiting for input"}
        )
    
    try:
        input_value = input_data.get("input_value")
        if not input_value:
            return JSONResponse(
                status_code=400,
                content={"error": "No input value provided"}
            )
        
        # Provide the input to the automation
        result = await automation_instance.provide_human_input(input_value)
        
        # Check if more input is needed
        if isinstance(result, dict) and result.get("requires_input"):
            return {
                "status": "waiting_for_input",
                "field": result.get("field"),
                "prompt": result.get("prompt")
            }
        
        # If form filling completed successfully
        return {"status": "continuing", "message": "Input provided, continuing automation"}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error providing input: {str(e)}"}
        )

@app.get("/automation-status")
async def get_automation_status():
    """Get the current status of the automation."""
    global automation_instance
    
    if not automation_instance:
        return JSONResponse(
            status_code=404,
            content={"error": "No automation has been started"}
        )
    
    # Get the streaming URL if available
    streaming_url = None
    if automation_instance.computer and automation_instance.computer.instance:
        try:
            streaming_url = await automation_instance.get_streaming_url()
        except:
            streaming_url = None
    
    status_info = automation_instance.get_status()
    
    # Add streaming URL if available
    if streaming_url:
        status_info["streaming_url"] = streaming_url
    
    return status_info

@app.post("/stop-automation")
async def stop_automation():
    """Stop the current automation process."""
    global automation_instance
    
    if not automation_instance:
        return JSONResponse(
            status_code=404,
            content={"error": "No automation has been started"}
        )
    
    try:
        await automation_instance.cleanup()
        return {"message": "Automation stopped successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error stopping automation: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)