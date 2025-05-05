# EZLynx AI-Powered Form Automation POC

This project demonstrates how AI can automate form-filling tasks in the EZLynx insurance platform with human-in-the-loop capability. The application uses OpenAI's Agent SDK with Scrapybara to power a browser automation solution that extracts data from emails and fills out applicant forms without the brittleness of traditional RPA solutions.

## Features

- Email (.eml) file upload and data extraction
- Secure credential management for EZLynx login
- AI-powered browser automation using OpenAI Agent SDK
- Human-in-the-loop for required fields missing in the source data
- Real-time monitoring of automation progress with live logs
- React-based UI for clear visualization of the process

## Architecture

The application consists of:

1. **Backend**: FastAPI server that handles:
   - File uploads and data extraction
   - Coordination with the AI automation engine
   - Human-in-the-loop interaction management
   
2. **Frontend**: React/TypeScript application that provides:
   - User-friendly interface for email uploading
   - Real-time status monitoring
   - Human input forms for missing data
   
3. **Automation Engine**: 
   - Scrapybara for browser automation
   - OpenAI's Agent SDK for intelligent form filling
   - Human intervention workflow for required fields

## Prerequisites

- Python 3.9+
- Node.js 16+ and npm
- Scrapybara API key (set as environment variable `SCRAPYBARA_API_KEY`)
- OpenAI API key (set as environment variable `OPENAI_API_KEY`)

## Installation

### Backend Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file with your API keys:
   ```
   SCRAPYBARA_API_KEY=your_scrapybara_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

### Frontend Setup

1. Navigate to the frontend directory (create it if it doesn't exist):
   ```
   mkdir -p frontend
   cd frontend
   ```
2. Install dependencies:
   ```
   npm install
   ```
3. Start the development server:
   ```
   npm start
   ```

## Running the Application

1. Start the backend server:
   ```
   uvicorn app:app --reload
   ```
2. In a separate terminal, start the frontend:
   ```
   cd frontend
   npm start
   ```
3. Open your browser and navigate to `http://localhost:3000`

## Usage

1. **Upload Data**: Upload an .eml file containing applicant data and enter EZLynx credentials
2. **Review Data**: Review the extracted email content
3. **Start Automation**: Launch the AI-powered automation process
4. **Monitor Progress**: Watch the real-time logs as the AI navigates the website
5. **Human Input**: When required, provide missing information that the AI cannot find
6. **Completion**: The automation completes the form submission

## Human-in-the-Loop Workflow

The human-in-the-loop capability provides several advantages:

1. **Fills Data Gaps**: Allows automation to proceed even when source data is incomplete
2. **Quality Control**: Humans provide accurate information for critical fields
3. **Non-Disruptive**: The automation pauses and resumes seamlessly
4. **Transparent**: Clear prompts explain exactly what information is needed

When the AI encounters a required field that's not present in the email data:
1. It takes a screenshot of the current form state
2. Automation pauses and the user is prompted for the missing data
3. The input form clearly displays which field needs information
4. After submission, the automation continues with the new information

## Project Structure

```
├── app.py                         # FastAPI application
├── simple_eml_parser.py           # Email extraction functionality
├── async_scrapybara_ubuntu_computer.py # Scrapybara integration
├── scrapybara_automation.py       # AI automation implementation
├── requirements.txt               # Python dependencies
├── frontend/                      # React frontend application
│   ├── src/
│   │   ├── App.tsx               # Main application component
│   │   └── App.css               # Styling
│   └── package.json              # Frontend dependencies
├── uploads/                       # Directory for uploaded files
├── screenshots/                   # Directory for automation screenshots
└── .env                           # Environment variables
```

## Demonstration Guide

For the client demo:

1. Prepare sample .eml files with varying completeness:
   - Complete data (shows full automation)
   - Missing some required fields (shows human-in-the-loop)
   
2. Highlight key features:
   - Show how AI intelligently finds and fills form fields
   - Demonstrate pausing for human input when needed
   - Emphasize resilience to UI changes (compared to traditional RPA)
   - Show how the AI handles unexpected form elements or variations

3. Discuss advantages over traditional RPA:
   - No brittle selectors or fixed workflows
   - Adaptive to UI changes and different form layouts
   - Human intervention only when necessary
   - More maintainable and scalable

## Next Steps

After this POC, the proposed next steps are:

1. **Enhanced Intelligence**: Train the AI with more examples of EZLynx forms
2. **Workflow Integration**: Connect with client's existing systems and workflow
3. **Analytics Dashboard**: Create metrics tracking for time saved and accuracy
4. **Expanded Scope**: Support additional form types and insurance workflows
5. **Security Enhancements**: Add role-based access and audit logging
6. **Multi-Tenant Support**: Scale to support multiple agencies in their system

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: TypeScript, React
- **Automation**: Scrapybara, OpenAI Agent SDK
- **Browser Control**: AsyncScrapybaraUbuntu
- **File Processing**: Python email parsing

## License

This project is intended as an internal POC demonstration only.