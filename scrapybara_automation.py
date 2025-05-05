import os
import asyncio
import json
import logging
from pathlib import Path
from async_scrapybara_ubuntu_computer import AsyncScrapybaraUbuntu
from agents import (
    Agent,
    AsyncComputer,
    Button,
    ComputerTool,
    Environment,
    ModelSettings,
    Runner,
    trace,
)
from openai.types.shared import Reasoning

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure agent logging
agent_logger = logging.getLogger("openai.agents")
agent_logger.setLevel(logging.DEBUG)
agent_logger.addHandler(logging.StreamHandler())

class EZLynxFormAutomation:
    """
    Automates EZLynx applicant form filling using Scrapybara and OpenAI Agent SDK.
    """
    
    def __init__(self, credentials_file=None, email_content_file=None, instance_id=None):
        """
        Initialize the automation.
        
        Args:
            credentials_file (str): Path to the JSON file with login credentials
            email_content_file (str): Path to the JSON file with extracted email content
            instance_id (str, optional): Scrapybara instance ID to resume, if any
        """
        self.credentials_file = credentials_file or "credentials.json"
        self.email_content_file = email_content_file or "extracted_email.json"
        self.log_file = "automation_log.json"
        self.instance_id_file = "instance_id.txt"
        self.instance_id = None
        self.status = "initialized"
        self.log_entries = []
        self.computer = None
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Human interaction related attributes
        self.require_human_input = False
        self.human_input_prompt = ""
        self.human_input_field = ""
        self.human_inputs_collected = {}
        
        # Load credentials and email content
        self._load_data()
    
    def _load_data(self):
        """Load credentials and email content from files."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    self.credentials = json.load(f)
            else:
                self.credentials = {}
                
            if os.path.exists(self.email_content_file):
                with open(self.email_content_file, 'r') as f:
                    self.email_content = json.load(f)
            else:
                self.email_content = {}
                
            # Try to load instance ID if it exists
            # if not self.instance_id and os.path.exists(self.instance_id_file):
            #     with open(self.instance_id_file, 'r') as f:
            #         self.instance_id = f.read().strip()

        except Exception as e:
            self.log(f"Error loading data: {str(e)}", level="error")
            self.credentials = {}
            self.email_content = {}
    
    def log(self, message, level="info"):
        """Add a log entry."""
        entry = {
            "timestamp": asyncio.get_event_loop().time(),
            "level": level,
            "message": message
        }
        self.log_entries.append(entry)
        
        # Log to console as well
        if level == "error":
            logger.error(message)
        elif level == "warn":
            logger.warning(message)
        else:
            logger.info(message)
            
        self._save_log()
        return entry
    
    def _save_log(self):
        """Save log entries to file."""
        log_data = {
            "status": self.status,
            "log_entries": self.log_entries,
            "require_human_input": self.require_human_input,
            "human_input_prompt": self.human_input_prompt,
            "human_input_field": self.human_input_field
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    async def initialize_scrapybara(self):
        """Initialize the Scrapybara instance."""
        self.log("Initializing Scrapybara instance...")
        self.status = "initializing"
        
        try:
            # Initialize Scrapybara
            self.computer = AsyncScrapybaraUbuntu(
                verbose=True, 
                instance_id=self.instance_id,
                timeout_hours=1  # Reduce timeout for testing
            )
            
            await self.computer.initialize()
            self.log(f"Using Scrapybara Instance ID: {self.computer.instance.id}")
            
            # Save the instance ID for future use
            with open(self.instance_id_file, "w") as f:
                f.write(self.computer.instance.id)
            
            # Take a screenshot to confirm initialization
            # screenshot = await self.computer.screenshot()
            # screenshot_path = self.screenshot_dir / "initialization.png"
            
            # Save screenshot path (in a real implementation, you'd save the actual image)
            # self.log(f"Screenshot saved to {screenshot_path}")
            
            self.status = "initialized"
            self.log("Scrapybara instance initialized successfully")
            return True
        
        except Exception as e:
            self.status = "error"
            self.log(f"Error initializing Scrapybara: {str(e)}", level="error")
            return False
    
    async def login_with_agent(self):
        """Use OpenAI Agent to log in to the website."""
        if not self.computer:
            self.log("Scrapybara instance not initialized", level="error")
            return False
        
        try:
            # Extract credentials
            url = self.credentials.get("destination_url")
            username = self.credentials.get("username")
            password = self.credentials.get("password")
            
            if not url or not username or not password:
                self.log("Missing login credentials", level="error")
                return False
                
            # Create prompt for login
            prompt = f"""
            Navigate to the following web page:
            URL: {url}

            Log in using the following credentials:
                Username: {username}
                Password: {password}
            
            Wait for the page to load after login.
            """
            
            self.log("Starting login process with OpenAI Agent...")
            self.status = "logging_in"
            
            # Take screenshot before starting
            # screenshot = await self.computer.screenshot()
            
            # Run the agent
            with trace("Login Process"):
                agent = Agent(
                    name="EZLynx Login Agent",
                    instructions="You are a helpful agent that logs in to a website accurately. Be precise in your interactions.",
                    tools=[ComputerTool(self.computer)],
                    model="computer-use-preview",
                    model_settings=ModelSettings(truncation="auto", reasoning=Reasoning(generate_summary="concise")),
                )
                
                self.log("Agent initialized, starting login process...")
                result = await Runner.run(agent, prompt, max_turns=100)
                
                self.log(f"Agent completed login: {result.final_output}")
            
            # Take screenshot after login
            # screenshot = await self.computer.screenshot()
            screenshot_path = self.screenshot_dir / "after_login.png"
            
            self.status = "logged_in"
            self.log("Login successful")
            return True
            
        except Exception as e:
            self.status = "error"
            self.log(f"Error during login with agent: {str(e)}", level="error")
            return False
    
    async def fill_applicant_form(self):
        """Use OpenAI Agent to fill out the applicant form with human intervention when needed."""
        if not self.computer:
            self.log("Scrapybara instance not initialized", level="error")
            return False
            
        if self.status != "logged_in":
            self.log("Must be logged in before filling form", level="error")
            return False
            
        try:
            # Extract email content for the form
            email_body = self.email_content.get("body", "")
            
            if not email_body:
                self.log("No email content available for form filling", level="error")
                return False
                
            # Create a prompt for the form filling
            initial_prompt = f"""
            You are now logged into EZLynx. Your task is to fill out a new applicant form using information from this email:

            {email_body}

            Follow these steps:
            1. Look for a "New Application" or "Add Applicant" button and click it
            2. Fill out the form fields with information from the email
            3. Look for business name, address, industry, and all other relevant information in the email
            4. Leave non-required fields empty if the information is not available in the email
            5. If a REQUIRED field does not have corresponding information in the email, STOP and ask for human input
               by ending your response with exactly "HUMAN_INPUT_REQUIRED: [field name] - [brief explanation]"
            6. Only submit the form when all required fields are filled
            7. If you need human input, take a screenshot first so the human can see the form
            8. Required fields are usually marked with an asterisk (*) but if you need human input for any required field that is not marked with an asterisk, STOP and ask for human input as described
            
            Think step by step and be methodical in filling out the form.
            """
            
            self.log("Starting form filling process with OpenAI Agent...")
            self.status = "filling_form"
            
            # Take screenshot before starting
            # screenshot = await self.computer.screenshot()
            
            # Create the agent
            with trace("Form Filling Process"):
                agent = Agent(
                    name="EZLynx Form Filling Agent",
                    instructions="You are a helpful agent that accurately fills out forms with provided information. Ask for human help when required fields don't have corresponding info. Leave non-required fields empty if info is not available.",
                    tools=[ComputerTool(self.computer)],
                    model="computer-use-preview",
                    model_settings=ModelSettings(truncation="auto", reasoning=Reasoning(generate_summary="concise")),
                )
                
                self.log("Agent initialized, starting form filling process...")
                
                # Run the agent with initial prompt
                result = await Runner.run(agent, initial_prompt, max_turns=500)
                
                new_inputs = result.to_input_list()
                if new_inputs[-1].get("pending_safety_checks"):
                    self.log("Safety checks failed, retrying...", level="warn")
                    vals = new_inputs[-1].get("pending_safety_checks")
                    del vals["pending_safety_checks"]
                    new_inputs[-1]["acknowledged_safety_checks"] = vals
                    result = await Runner.run(agent, new_inputs, max_turns=500)

                # Check if human input is required
                if "HUMAN_INPUT_REQUIRED:" in result.final_output:
                    # Parse the required field and explanation
                    input_request = result.final_output.split("HUMAN_INPUT_REQUIRED:")[1].strip()
                    field_name = input_request.split("-")[0].strip()
                    explanation = "-".join(input_request.split("-")[1:]).strip()
                    
                    # Take a screenshot for the human
                    # screenshot = await self.computer.screenshot()
                    screenshot_path = self.screenshot_dir / "form_input_needed.png"
                    self.log(f"Screenshot saved to {screenshot_path}")
                    
                    # Log the need for human input
                    self.log(f"Human input required for field: {field_name}", level="warn")
                    self.log(f"Explanation: {explanation}", level="warn")
                    
                    # Set the human intervention flags
                    self.require_human_input = True
                    self.human_input_prompt = f"Please provide value for: {field_name}\n{explanation}"
                    self.human_input_field = field_name
                    self.status = "waiting_for_input"
                    
                    return {
                        "success": False, 
                        "requires_input": True, 
                        "field": field_name, 
                        "prompt": self.human_input_prompt
                    }
                
                # If we got here, the agent completed its task without requiring input
                self.status = "form_filled"
                self.log("Form filled successfully")
                self.log(f"Agent output: {result.final_output}")
                return True
                
        except Exception as e:
            self.status = "error"
            self.log(f"Error during form filling with agent: {str(e)}", level="error")
            return False
    
    async def provide_human_input(self, input_value):
        """Provide human input to the form filling process and continue."""
        if not self.computer:
            self.log("Scrapybara instance not initialized", level="error")
            return False
            
        if self.status != "waiting_for_input":
            self.log("Not waiting for human input", level="error")
            return False
            
        try:
            # Store the human input
            self.human_inputs_collected[self.human_input_field] = input_value
            self.log(f"Received human input for {self.human_input_field}: {input_value}")
            
            # Clear the human intervention flags
            self.require_human_input = False
            
            # Update status
            self.status = "filling_form"
            
            # Create a prompt to continue form filling with the new information
            email_body = self.email_content.get("body", "")
            
            # Create a continuation prompt that includes all human inputs
            human_inputs_text = "\n".join([f"{field}: {value}" for field, value in self.human_inputs_collected.items()])
            
            continuation_prompt = f"""
            Continue filling out the EZLynx form. You were previously working with this email content:
            
            {email_body}
            
            You have received additional information from a human for fields that weren't in the email:
            
            {human_inputs_text}
            
            Please continue filling out the form with this new information. Remember:
            1. Leave non-required fields empty if the information is not available
            2. If you encounter another REQUIRED field without corresponding information, STOP and ask for human input
               by ending your response with exactly "HUMAN_INPUT_REQUIRED: [field name] - [brief explanation]"
            3. Only submit the form when all required fields are filled
            4. Take a screenshot first if you need more human input so the human can see the form
            5. Required fields are usually marked with an asterisk (*) but if you need human input for any required field that is not marked with an asterisk, STOP and ask for human input as described
            Continue where you left off with the form.
            """
            
            # Run the agent with the continuation prompt
            with trace("Form Filling Process - Continuation"):
                agent = Agent(
                    name="EZLynx Form Filling Agent",
                    instructions="You are a helpful agent that accurately fills out forms with provided information. Ask for human help when required fields don't have corresponding info. Leave non-required fields empty if info is not available.",
                    tools=[ComputerTool(self.computer)],
                    model="computer-use-preview",
                    model_settings=ModelSettings(truncation="auto", reasoning=Reasoning(generate_summary="concise")),
                )
                
                self.log("Agent continuing form filling with human input...")
                result = await Runner.run(agent, continuation_prompt, max_turns=500)
                
                new_inputs = result.to_input_list()
                if new_inputs[-1].get("pending_safety_checks"):
                    self.log("Safety checks failed, retrying...", level="warn")
                    vals = new_inputs[-1].get("pending_safety_checks")
                    del vals["pending_safety_checks"]
                    new_inputs[-1]["acknowledged_safety_checks"] = vals
                    result = await Runner.run(agent, new_inputs, max_turns=500)

                # Check if human input is required again
                if "HUMAN_INPUT_REQUIRED:" in result.final_output:
                    # Parse the required field and explanation
                    input_request = result.final_output.split("HUMAN_INPUT_REQUIRED:")[1].strip()
                    field_name = input_request.split("-")[0].strip()
                    explanation = "-".join(input_request.split("-")[1:]).strip()
                    
                    # Take a screenshot for the human
                    # screenshot = await self.computer.screenshot()
                    screenshot_path = self.screenshot_dir / "form_input_needed_again.png"
                    self.log(f"Screenshot saved to {screenshot_path}")
                    
                    # Log the need for human input
                    self.log(f"Human input required for field: {field_name}", level="warn")
                    self.log(f"Explanation: {explanation}", level="warn")
                    
                    # Set the human intervention flags
                    self.require_human_input = True
                    self.human_input_prompt = f"Please provide value for: {field_name}\n{explanation}"
                    self.human_input_field = field_name
                    self.status = "waiting_for_input"
                    
                    return {
                        "success": False, 
                        "requires_input": True, 
                        "field": field_name, 
                        "prompt": self.human_input_prompt
                    }
                
                # If we got here, the agent completed the form
                self.status = "form_filled"
                self.log("Form filled successfully with human input")
                self.log(f"Agent output: {result.final_output}")
                return {"success": True, "message": "Form filled successfully"}
                
        except Exception as e:
            self.status = "error"
            self.log(f"Error during form filling with human input: {str(e)}", level="error")
            return {"success": False, "message": str(e)}
    
    async def run_automation(self):
        """Run the full automation process."""
        try:
            # Initialize Scrapybara
            init_success = await self.initialize_scrapybara()
            if not init_success:
                raise Exception("Failed to initialize Scrapybara")
            
            # Login to the website using the agent
            login_success = await self.login_with_agent()
            if not login_success:
                raise Exception("Failed to login to the website")
            
            # Fill out the applicant form
            form_result = await self.fill_applicant_form()
            
            # Check if human input is needed
            if isinstance(form_result, dict) and form_result.get('requires_input'):
                self.log("Automation paused waiting for human input")
                return {"success": True, "status": "waiting_for_input", "human_input": form_result}
            
            # If not waiting for input and form filling was successful
            if form_result is True:
                self.status = "completed"
                self.log("Automation process completed successfully")
                return {"success": True, "message": "Automation completed successfully"}
            
            # If we got here with form_result as False, something went wrong
            return {"success": False, "message": "Form filling failed"}
            
        except Exception as e:
            self.status = "error"
            self.log(f"Error in automation process: {str(e)}", level="error")
            return {"success": False, "message": str(e)}
    
    async def cleanup(self):
        """Clean up and stop the Scrapybara instance."""
        if self.computer:
            try:
                self.log("Stopping Scrapybara instance...")
                await self.computer.stop()
                self.log("Scrapybara instance stopped")
            except Exception as e:
                self.log(f"Error stopping Scrapybara: {str(e)}", level="error")
    
    def get_status(self):
        """Get the current status information."""
        status_info = {
            "status": self.status,
            "log_entries": self.log_entries[-10:] if len(self.log_entries) > 10 else self.log_entries
        }
        
        # Add human interaction info if applicable
        if self.require_human_input:
            status_info.update({
                "require_human_input": True,
                "human_input_prompt": self.human_input_prompt,
                "human_input_field": self.human_input_field
            })
        
        return status_info
    
    async def get_streaming_url(self):
        """Get the Scrapybara streaming URL if available."""
        if not self.computer or not self.computer.instance:
            return None
            
        try:
            return await self.computer.get_streaming_url()
        except:
            return None