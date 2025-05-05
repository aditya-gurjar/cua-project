import React, { useState, useEffect } from 'react';
import './App.css';

interface EmailContent {
  subject: string;
  body: string;
}

interface LogEntry {
  timestamp: number;
  level: string;
  message: string;
}

interface AutomationStatus {
  status: string;
  log_entries: LogEntry[];
  streaming_url?: string;
  require_human_input?: boolean;
  human_input_prompt?: string;
  human_input_field?: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [destinationUrl, setDestinationUrl] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [emailContent, setEmailContent] = useState<EmailContent | null>(null);
  const [currentStep, setCurrentStep] = useState<'upload' | 'review' | 'automate'>('upload');
  const [automationStatus, setAutomationStatus] = useState<AutomationStatus | null>(null);
  const [statusPolling, setStatusPolling] = useState<NodeJS.Timeout | null>(null);
  const [humanInputValue, setHumanInputValue] = useState('');
  const [isSubmittingInput, setIsSubmittingInput] = useState(false);

  useEffect(() => {
    // Clean up the polling interval when component unmounts
    return () => {
      if (statusPolling) {
        clearInterval(statusPolling);
      }
    };
  }, [statusPolling]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setEmailContent(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !destinationUrl || !username || !password) {
      setMessage('Please fill in all fields.');
      return;
    }

    setIsLoading(true);
    setMessage('');
    setEmailContent(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('destination_url', destinationUrl);
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.extraction_error) {
        setMessage(`File uploaded but error extracting content: ${data.extraction_error}`);
      } else {
        setMessage('File uploaded, credentials saved, and email content extracted successfully!');
        setEmailContent(data.email_content);
        setCurrentStep('review');
      }
    } catch (error) {
      setMessage('Error uploading file or saving credentials.');
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startAutomation = async () => {
    setCurrentStep('automate');
    setMessage('Starting automation process with OpenAI agent...');
    setAutomationStatus(null);
    
    try {
      // Start the automation process
      const response = await fetch('http://localhost:8000/start-automation', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.error) {
        setMessage(`Error starting automation: ${data.error}`);
      } else {
        setMessage('Automation started. Monitoring progress...');
        
        // Start polling for status updates
        const interval = setInterval(fetchAutomationStatus, 2000);
        setStatusPolling(interval);
      }
    } catch (error) {
      setMessage('Error starting automation.');
      console.error('Error:', error);
    }
  };
  
  const fetchAutomationStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/automation-status');
      
      if (response.status === 404) {
        // No automation running
        if (statusPolling) {
          clearInterval(statusPolling);
          setStatusPolling(null);
        }
        return;
      }
      
      const data = await response.json();
      setAutomationStatus(data);
      
      // If automation is completed or errored, stop polling
      if (data.status === 'completed' || data.status === 'error' || data.status === 'form_filled') {
        if (statusPolling) {
          clearInterval(statusPolling);
          setStatusPolling(null);
        }
        
        if (data.status === 'completed' || data.status === 'form_filled') {
          setMessage('Successfully filled the applicant form!');
        } else if (data.status === 'error') {
          setMessage('Error occurred during automation. Check logs for details.');
        }
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };
  
  const submitHumanInput = async () => {
    if (!humanInputValue.trim()) {
      setMessage('Please enter a value before submitting');
      return;
    }
    
    setIsSubmittingInput(true);
    
    try {
      const response = await fetch('http://localhost:8000/provide-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          input_value: humanInputValue
        })
      });
      
      const data = await response.json();
      
      if (data.error) {
        setMessage(`Error submitting input: ${data.error}`);
      } else {
        setMessage('Input submitted successfully');
        setHumanInputValue('');
        
        // Check if more input is needed
        if (data.status === 'waiting_for_input') {
          // Update with new input prompt
          setAutomationStatus(prev => {
            if (!prev) return null;
            return {
              ...prev,
              require_human_input: true,
              human_input_prompt: data.prompt,
              human_input_field: data.field
            };
          });
        } else {
          // Continue automation
          setAutomationStatus(prev => {
            if (!prev) return null;
            return {
              ...prev,
              require_human_input: false,
              human_input_prompt: '',
              human_input_field: ''
            };
          });
        }
      }
    } catch (error) {
      setMessage('Error submitting input to server');
      console.error('Error:', error);
    } finally {
      setIsSubmittingInput(false);
    }
  };
  
  const stopAutomation = async () => {
    try {
      const response = await fetch('http://localhost:8000/stop-automation', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.error) {
        setMessage(`Error stopping automation: ${data.error}`);
      } else {
        setMessage('Automation stopped successfully.');
        
        // Stop polling
        if (statusPolling) {
          clearInterval(statusPolling);
          setStatusPolling(null);
        }
      }
    } catch (error) {
      setMessage('Error stopping automation.');
      console.error('Error:', error);
    }
  };

  const renderUploadForm = () => (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="file">Upload EML File:</label>
        <input
          type="file"
          id="file"
          accept=".eml"
          onChange={handleFileChange}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="destination">EZLynx URL:</label>
        <input
          type="url"
          id="destination"
          value={destinationUrl}
          onChange={(e) => setDestinationUrl(e.target.value)}
          placeholder="https://ezlynx.com/login"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="username">Username:</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>

      <button type="submit" disabled={isLoading} className="primary-button">
        {isLoading ? 'Processing...' : 'Upload & Extract Data'}
      </button>
    </form>
  );

  const renderEmailContent = () => {
    if (!emailContent) return null;
    
    return (
      <div className="email-content">
        <div className="email-header">
          <h2>Extracted Email Content</h2>
          <p className="email-subject"><strong>Subject:</strong> {emailContent.subject}</p>
        </div>
        
        <div className="email-body">
          <h3>Email Body:</h3>
          <pre>{emailContent.body}</pre>
        </div>
        
        <div className="action-buttons">
          <button onClick={startAutomation} className="primary-button">
            Start AI-Powered Form Automation
          </button>
          <button onClick={() => setCurrentStep('upload')} className="secondary-button">
            Back to Upload
          </button>
        </div>
      </div>
    );
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'initializing':
      case 'logging_in':
      case 'filling_form':
        return 'status-in-progress';
      case 'initialized':
      case 'logged_in':
      case 'form_filled':
      case 'completed':
        return 'status-success';
      case 'waiting_for_input':
        return 'status-waiting';
      case 'error':
        return 'status-error';
      default:
        return '';
    }
  };

  const getLogEntryClass = (level: string) => {
    switch (level) {
      case 'error':
        return 'log-error';
      case 'warn':
        return 'log-warning';
      default:
        return 'log-info';
    }
  };

  const renderHumanInputForm = () => {
    if (!automationStatus?.require_human_input) return null;
    
    return (
      <div className="human-input-form">
        <h3>Human Input Required</h3>
        <p className="input-prompt">{automationStatus.human_input_prompt}</p>
        
        <div className="form-group">
          <label htmlFor="human-input">Enter value:</label>
          <input
            type="text"
            id="human-input"
            value={humanInputValue}
            onChange={(e) => setHumanInputValue(e.target.value)}
            placeholder="Enter the required information"
          />
        </div>
        
        <button 
          onClick={submitHumanInput} 
          disabled={isSubmittingInput || !humanInputValue.trim()} 
          className="primary-button"
        >
          {isSubmittingInput ? 'Submitting...' : 'Submit & Continue Automation'}
        </button>
      </div>
    );
  };

  const renderAutomationProcess = () => (
    <div className="automation-container">
      <h2>AI-Powered Automation</h2>
      
      {automationStatus && (
        <div className="automation-status">
          <p>
            Current Status: 
            <span className={`status-badge ${getStatusClass(automationStatus.status)}`}>
              {automationStatus.status}
            </span>
          </p>
        </div>
      )}
      
      <div className="progress-indicator">
        <div className={`progress-step ${automationStatus?.status === 'initializing' ? 'current' : ''} ${automationStatus?.status === 'initialized' || automationStatus?.status === 'logging_in' || automationStatus?.status === 'logged_in' || automationStatus?.status === 'filling_form' || automationStatus?.status === 'form_filled' || automationStatus?.status === 'completed' ? 'completed' : ''}`}>
          <div className="step-icon">1</div>
          <div className="step-label">Initializing</div>
        </div>
        <div className="progress-divider"></div>
        <div className={`progress-step ${automationStatus?.status === 'logging_in' ? 'current' : ''} ${automationStatus?.status === 'logged_in' || automationStatus?.status === 'filling_form' || automationStatus?.status === 'form_filled' || automationStatus?.status === 'completed' ? 'completed' : ''}`}>
          <div className="step-icon">2</div>
          <div className="step-label">Logging In</div>
        </div>
        <div className="progress-divider"></div>
        <div className={`progress-step ${automationStatus?.status === 'filling_form' || automationStatus?.status === 'waiting_for_input' ? 'current' : ''} ${automationStatus?.status === 'form_filled' || automationStatus?.status === 'completed' ? 'completed' : ''}`}>
          <div className="step-icon">3</div>
          <div className="step-label">Filling Form</div>
        </div>
        <div className="progress-divider"></div>
        <div className={`progress-step ${automationStatus?.status === 'completed' ? 'completed' : ''}`}>
          <div className="step-icon">4</div>
          <div className="step-label">Completed</div>
        </div>
      </div>
      
      {automationStatus?.streaming_url && (
        <div className="streaming-container">
          <h3>Live Automation View</h3>
          <div className="streaming-placeholder">
            <p>Streaming URL is available. In a production environment, this would display a live view of the automation.</p>
            {/* In a real implementation, this might be an iframe or video stream */}
          </div>
        </div>
      )}
      
      {/* Human input form */}
      {renderHumanInputForm()}
      
      <div className="automation-log">
        <h3>Automation Logs</h3>
        {automationStatus?.log_entries && automationStatus.log_entries.length > 0 ? (
          automationStatus.log_entries.map((entry, index) => (
            <p key={index} className={getLogEntryClass(entry.level)}>
              {entry.message}
            </p>
          ))
        ) : (
          <p>Waiting for automation logs...</p>
        )}
      </div>
      
      <div className="action-buttons">
        <button onClick={stopAutomation} className="danger-button">
          Stop Automation
        </button>
        <button onClick={() => setCurrentStep('review')} className="secondary-button">
          Back to Review
        </button>
      </div>
    </div>
  );

  return (
    <div className="container">
      <h1>EZLynx AI Automation POC</h1>
      <p className="description">
        Upload an email with applicant details and automate the form-filling process in EZLynx with AI.
      </p>
      
      {currentStep === 'upload' && renderUploadForm()}
      {currentStep === 'review' && renderEmailContent()}
      {currentStep === 'automate' && renderAutomationProcess()}

      {message && (
        <div className={`message ${message.includes('successfully') ? 'success' : ''}`}>
          {message}
        </div>
      )}
    </div>
  );
}

export default App;