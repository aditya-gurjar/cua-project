import email
import os
from pathlib import Path
import json

def extract_email_content(file_path):
    """
    Extract the body content from an .eml file.
    
    Args:
        file_path (str): Path to the .eml file
        
    Returns:
        dict: Contains 'subject' and 'body' of the email
    """
    # Read the .eml file
    with open(file_path, 'rb') as f:
        msg = email.message_from_binary_file(f)
    
    # Extract subject
    subject = msg.get('Subject', '')
    
    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()
    
    return {
        'subject': subject,
        'body': body
    }

def save_extracted_content(content, output_file="extracted_email.json"):
    """
    Save the extracted email content to a JSON file.
    
    Args:
        content (dict): The email content to save
        output_file (str): Path to save the JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2)
    
    print(f"Email content saved to {output_file}")

def main():
    # Create uploads directory if it doesn't exist
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # Path to the uploaded .eml file
    # In practice, this would come from the FastAPI endpoint
    eml_file = "uploads/sample.eml"

if __name__ == "__main__":
    main()