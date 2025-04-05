# Agentic AI Mathematical Computation, Paint Tool, and Gmail Integration

This project demonstrates the capabilities of agentic AI tools using the MCP (Model-Context Protocol) framework to perform mathematical operations, automate Microsoft Paint, and send emails via Gmail.

## Overview

The project consists of multiple components for different functionalities:

1. **Mathematical and Paint Automation**:
   - `example2-3.py`: An MCP server that provides various mathematical tools and Microsoft Paint automation capabilities.
   - `talk2mcp-2.py`: A client that connects to the MCP server and uses Gemini AI to solve problems and visualize results in Paint.

2. **Gmail Integration**:
   - `example2-3_Gmail.py`: MCP server with mathematical tools and Gmail SMTP integration.
   - `talk2mcp-2_Gmail.py`: Client for Gmail SMTP-based email sending.
   - `example2-3_Gmail_2.py`: MCP server with OAuth-based Gmail integration.
   - `talk2mcp-2_Gmail_2.py`: Client for OAuth-based Gmail sending.
   - `manual_gmail_auth.py`: Helper script to handle Gmail OAuth 2.0 authentication.

## Features

### Mathematical Tools
- Basic operations: Addition, subtraction, multiplication, division
- Advanced math: Power, square root, cube root, factorial, logarithm, trigonometric functions
- List operations: Sum of lists, Fibonacci sequence generation
- String processing: ASCII value conversion, exponential sum calculations

### Paint Automation
- Opening Microsoft Paint
- Drawing rectangles with specified coordinates
- Adding text to Paint canvas

### Gmail Integration
- Email sending via SMTP with App Password authentication
- Email sending via OAuth 2.0 authentication
- Manual OAuth flow for obtaining and refreshing tokens

## Requirements

- Python 3.12+ (Python 3.13 may have compatibility issues with some libraries)
- Google Gemini API key
- Gmail account for email functionality

### Dependencies

The project requires the following Python packages:
```
# See requirements.txt for full dependencies with version requirements
mcp
uv
Pillow
pywinauto
PyWin32
python-dotenv
google-generativeai
requests
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your API key and email settings:
   ```
   # Gemini API key
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Email settings
   USER_EMAIL=your_email@gmail.com
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password_here
   ```

3. For OAuth Gmail integration:
   - Create a Google Cloud project with the Gmail API enabled
   - Download the OAuth client secret file and save it as `client_secret_xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com.json`
   - Run `python manual_gmail_auth.py` to authorize the application

4. Ensure Microsoft Paint is installed on your system (Windows only).

## Usage

### Paint Automation Version

1. Start the application by running:
   ```
   python talk2mcp-2.py
   ```

2. The script will:
   - Connect to the MCP server
   - Use Gemini AI to solve a math problem
   - Open Microsoft Paint
   - Draw a rectangle
   - Display the final result as text in Paint

### Gmail SMTP Version

1. Run the following command:
   ```
   python talk2mcp-2_Gmail.py
   ```

2. The script will:
   - Connect to the MCP server
   - Use Gemini AI to solve the math problem
   - Send the result via email using SMTP and App Password authentication

### Gmail OAuth Version

1. First ensure you've completed the OAuth setup:
   ```
   python manual_gmail_auth.py
   ```

2. Then run the OAuth-based client:
   ```
   python talk2mcp-2_Gmail_2.py
   ```

3. The script will:
   - Connect to the MCP server
   - Use Gemini AI to solve the math problem
   - Send the result via email using OAuth 2.0 authentication

## How It Works

### MCP Servers

- **example2-3.py**: Provides mathematical operations and Paint automation
- **example2-3_Gmail.py**: Provides mathematical operations and SMTP email sending
- **example2-3_Gmail_2.py**: Provides mathematical operations and OAuth-based email sending

### Client Applications

- **talk2mcp-2.py**: Uses Gemini to solve problems and visualize in Paint
- **talk2mcp-2_Gmail.py**: Uses Gemini to solve problems and send results via SMTP
- **talk2mcp-2_Gmail_2.py**: Uses Gemini to solve problems and send results via OAuth

### OAuth Authentication

The `manual_gmail_auth.py` script handles:
1. Creating an OAuth authorization URL
2. Guiding the user through the authorization process
3. Exchanging authorization codes for access tokens
4. Refreshing access tokens when needed

## Common Workflow

All client applications follow a similar iterative approach:
1. **Initialization**: Connect to the appropriate MCP server and retrieve available tools
2. **System Prompt Creation**: Generate a prompt with tool descriptions for the AI
3. **Iterative Problem Solving**:
   - AI evaluates the current state and decides which tool to use
   - Client executes the tool and collects results
   - Results are added to the context for the next iteration
4. **Result Presentation**: 
   - Paint version: Visualize in Microsoft Paint
   - Gmail versions: Send the result via email

## Project Structure

```
├── .env                                    # Environment variables
├── requirements.txt                        # Project dependencies
├── example2-3.py                           # MCP server (Paint version)
├── example2-3_Gmail.py                     # MCP server (SMTP Gmail version)
├── example2-3_Gmail_2.py                   # MCP server (OAuth Gmail version)
├── talk2mcp-2.py                           # Client for Paint automation
├── talk2mcp-2_Gmail.py                     # Client for SMTP Gmail
├── talk2mcp-2_Gmail_2.py                   # Client for OAuth Gmail
├── manual_gmail_auth.py                    # Helper script for Gmail OAuth
├── client_secret_*.json                    # OAuth client secret file (not included)
└── README.md                               # Project documentation
```

## Troubleshooting

### General Issues
- Ensure all dependencies are installed correctly
- Python version compatibility: Python 3.12 is recommended (Python 3.13 may have issues)
- Verify your Gemini API key is correctly set in the .env file

### Paint Automation Issues
- Make sure Paint is installed and accessible on your system
- The screen coordinates used in Paint automation may need adjustment based on your screen resolution

### Gmail Issues
- SMTP version: Ensure you've created an App Password in your Google Account security settings
- OAuth version: 
  - Verify you've completed the OAuth flow with `manual_gmail_auth.py`
  - Ensure you've added your email as a test user in the Google Cloud Console
  - Check that the token.json file exists in the project directory

## Extension Ideas

- Add more mathematical functions
- Implement more complex Paint operations
- Extend email capabilities (attachments, HTML formatting, etc.)
- Create custom visualizations for different problem types
- Support different LLM providers beyond Google Gemini
