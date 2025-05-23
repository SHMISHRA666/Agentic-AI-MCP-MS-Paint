# Import necessary libraries
# basic import 
from mcp.server.fastmcp import FastMCP, Image  # MCP framework for building AI-accessible tools
from mcp.server.fastmcp.prompts import base    # Prompt templates for the MCP framework
from mcp.types import TextContent              # Type for text response content
from mcp import types                          # MCP type definitions
from PIL import Image as PILImage              # Python Imaging Library for image processing
import math                                    # Math operations for calculator functions
import sys                                     # System utilities
from pywinauto.application import Application  # For automating Windows applications (MS Paint)
import win32gui                                # Windows GUI utilities
import win32con                                # Windows API constants
import time                                    # For adding delays
from win32api import GetSystemMetrics          # For getting screen dimensions
# Email imports
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import json
import requests
from urllib.parse import urlencode
import pickle
import webbrowser

# Initialize MCP server - this allows the framework to register our tools
mcp = FastMCP("Calculator")

# Initialize Paint app variable (used by Paint tools)
paint_app = None

# Load environment variables
load_dotenv()

# Gmail API settings
CLIENT_SECRET_FILE = 'client_secret_819038297150-71h5nap5siu85uh3eti1vhf3hpnm71c6.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'  # Will store the access & refresh tokens
# Use a simpler scope that doesn't require verification
# SCOPES = ['https://www.googleapis.com/auth/gmail.send']
SCOPES = ['https://mail.google.com/']  # Full mail access - works better for testing
OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'  # Out-of-band (manual) authorization
USER_EMAIL = os.getenv("USER_EMAIL", "your.email@gmail.com")

def load_client_secrets():
    """Load the client secrets from the JSON file"""
    try:
        if not os.path.exists(CLIENT_SECRET_FILE):
            print(f"ERROR: Client secret file not found: {CLIENT_SECRET_FILE}")
            return None
            
        with open(CLIENT_SECRET_FILE, 'r') as f:
            client_secrets = json.load(f)
            
        if 'installed' not in client_secrets:
            print("ERROR: Invalid client secret file format")
            return None
            
        return client_secrets['installed']
    except Exception as e:
        print(f"ERROR loading client secrets: {str(e)}")
        return None

def refresh_access_token(client_id, client_secret, refresh_token):
    """Get a new access token using the refresh token"""
    token_request = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(OAUTH_TOKEN_URL, data=token_request)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('access_token')
    else:
        print(f"ERROR: Failed to refresh access token")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_valid_tokens():
    """Get valid tokens, refreshing if necessary"""
    client_secrets = load_client_secrets()
    if not client_secrets:
        return None
    
    client_id = client_secrets['client_id']
    client_secret = client_secrets['client_secret']
    
    # Check if we have existing tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        # If we have a refresh token, use it to get a new access token
        if 'refresh_token' in token_data:
            print("Refreshing access token...")
            new_access_token = refresh_access_token(
                client_id,
                client_secret,
                token_data['refresh_token']
            )
            
            if new_access_token:
                token_data['access_token'] = new_access_token
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(token_data, f)
                return token_data
    
    # If we don't have tokens, inform the user to run manual_gmail_auth.py
    print("\n" + "=" * 70)
    print("ERROR: No valid OAuth tokens available")
    print("=" * 70)
    print("Please run 'manual_gmail_auth.py' first to set up OAuth tokens")
    print("Example: python manual_gmail_auth.py")
    print("=" * 70 + "\n")
    return None

def send_email_with_oauth(recipient, subject, message):
    """Send email using Gmail API with OAuth authentication"""
    token_data = get_valid_tokens()
    if not token_data:
        return False, "Could not get valid OAuth tokens. Please run manual_gmail_auth.py first."
    
    access_token = token_data['access_token']
    
    try:
        # Create email message
        email_message = MIMEMultipart()
        email_message['to'] = recipient
        email_message['subject'] = subject
        
        # Add text part
        msg = MIMEText(message)
        email_message.attach(msg)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
        
        # Build the API request
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json'
        }
        data = {'raw': raw_message}
        
        # Send the request
        print(f"Sending email to {recipient}...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Email sent successfully to {recipient}")
            return True, f"Email sent successfully to {recipient}"
        else:
            error_message = f"Failed to send email. Status code: {response.status_code}"
            print(error_message)
            print(f"Response: {response.text}")
            return False, error_message
    except Exception as e:
        error_message = f"Error sending email: {str(e)}"
        print(error_message)
        return False, error_message

# DEFINE TOOLS

# Email tool using OAuth
@mcp.tool()
async def send_email(recipient: str, subject: str, message: str) -> dict:
    """Send an email using Gmail API with OAuth authentication"""
    print(f"CALLED: send_email(recipient: {recipient}, subject: {subject}, message: {message})")
    
    success, result_message = send_email_with_oauth(recipient, subject, message)
    
    if success:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=result_message
                )
            ]
        }
    else:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=result_message
                )
            ]
        }

# Addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

@mcp.tool()
def length_string(string: str) -> int:
    """Return the length of a string"""
    print("CALLED: length_string(string: str) -> int:")
    return len(string)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool - special tool that performs (a - b - b)
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

# IMAGE AND STRING PROCESSING TOOLS

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

# PAINT APPLICATION TOOLS 
# These tools use pywinauto to automate Microsoft Paint application

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        # Check if Paint is already open
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window reference
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width to adjust coordinates
        primary_width = GetSystemMetrics(0)
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(1)  # Increased delay for focus
        
        # Click on the Rectangle tool using the correct coordinates for primary screen
        paint_window.click_input(coords=(796, 126))
        time.sleep(2)  # Wait for tool selection to register
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Draw rectangle - coordinates should already be relative to the Paint window
        # Offset by 100,100 to position correctly within the canvas
        canvas.click_input(coords=(x1+100, y1+100))
        canvas.press_mouse_input(coords=(x1+100, y1+100))
        canvas.move_mouse_input(coords=(x2+100, y2+100))
        canvas.release_mouse_input(coords=(x2+100, y2+100))
        
        # Return success message
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        # Return error message if drawing fails
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        # Check if Paint is already open
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window reference
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # First click on Rectangle tool (to reset any other active tools)
        paint_window.click_input(coords=(796, 126))
        time.sleep(2)
        
        # Then click on the text tool
        paint_window.click_input(coords=(512, 128))
        time.sleep(2)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Select text tool using keyboard shortcuts
        # paint_window.type_keys('t')
        # time.sleep(0.1)
        # paint_window.type_keys('x')
        # time.sleep(2)
        
        # Click where to start typing
         # Create a text area by clicking and dragging
        canvas.click_input(coords=(772, 576))
        time.sleep(0.2)
        canvas.press_mouse_input(coords=(772, 576))
        time.sleep(0.2)
        # Make text area wider based on text length
        canvas.move_mouse_input(coords=(772+len(text)*20, 576))
        time.sleep(0.2)
        canvas.release_mouse_input(coords=(772+len(text)*20, 576))
        time.sleep(2)

        # Process the text content - extract numerical part if needed
        full_text = text
        # # Remove brackets and unnecessary parts if needed
        # if "[" in full_text and "]" in full_text:
        #     # Keep the original format but ensure the numerical part is included
        #     start_idx = full_text.find("[")
        #     end_idx = full_text.find("]") + 1
        #     numerical_part = full_text[start_idx:end_idx]
        #     full_text = full_text.split(":")[0] + ": " + numerical_part
        
        # Type the text passed from client - handle spaces properly
        # pywinauto's type_keys method requires special handling for spaces
        # Using '{SPACE}' to ensure spaces are correctly typed
        processed_text = full_text.replace(" ", "{SPACE}")
        paint_window.type_keys(processed_text)

        # # Type the text passed from client
        # paint_window.type_keys(full_text)
        time.sleep(2)
        
        # Click elsewhere to exit text mode
        canvas.click_input(coords=(1050, 800))
        
        # Return success message
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        # Return error message if adding text fails
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    global paint_app
    try:
        # Start the Paint application
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)
        
        # Return success message
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on primary monitor and maximized"
                )
            ]
        }
    except Exception as e:
        # Return error message if opening Paint fails
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

# DYNAMIC RESOURCES
# Resources are similar to tools but are accessed differently by the client

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# PROMPT TEMPLATES
# Define prompt templates that can be used by clients

@mcp.prompt()
def review_code(code: str) -> str:
    """Prompt template for code review"""
    print("CALLED: review_code(code: str) -> str:")
    return f"Please review this code:\n\n{code}"


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Prompt template for debugging errors"""
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

# MAIN ENTRY POINT
if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
