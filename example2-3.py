# Import necessary libraries
# ----- MCP Framework Imports -----
from mcp.server.fastmcp import FastMCP, Image  # MCP framework for building AI-accessible tools
from mcp.server.fastmcp.prompts import base    # Prompt templates for the MCP framework
from mcp.types import TextContent              # Type for text response content
from mcp import types                          # MCP type definitions

# ----- Image Processing Imports -----
from PIL import Image as PILImage              # Python Imaging Library for image processing

# ----- Utility Imports -----
import math                                    # Math operations for calculator functions
import sys                                     # System utilities
import time                                    # For adding delays

# ----- Windows Automation Imports -----
from pywinauto.application import Application  # For automating Windows applications (MS Paint)
import win32gui                                # Windows GUI utilities for window manipulation
import win32con                                # Windows API constants for window states
from win32api import GetSystemMetrics          # For getting screen dimensions

# Initialize MCP server with the name "Calculator"
# This creates the server instance that will register and expose our tools to LLMs
mcp = FastMCP("Calculator")

# =============================================================================
# MATHEMATICAL FUNCTION TOOLS
# Each tool is decorated with @mcp.tool() to register it with the MCP framework
# =============================================================================

# Addition tool - adds two integers and returns the result
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

# List addition tool - sums all numbers in a list
@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# String length tool - returns the number of characters in a string
@mcp.tool()
def length_string(string: str) -> int:
    """Return the length of a string"""
    print("CALLED: length_string(string: str) -> int:")
    return len(string)

# Subtraction tool - subtracts the second number from the first
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# Multiplication tool - multiplies two integers
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

# Division tool - divides the first number by the second (returns float)
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# Power tool - raises the first number to the power of the second
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# Square root tool - calculates the square root of a number
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# Cube root tool - calculates the cube root of a number
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# Factorial tool - calculates the factorial of an integer (n!)
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# Natural logarithm tool - calculates ln(a)
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# Modulo tool - calculates the remainder when dividing two numbers
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# Sine tool - calculates the sine of an angle (in radians)
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# Cosine tool - calculates the cosine of an angle (in radians)
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# Tangent tool - calculates the tangent of an angle (in radians)
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# Special mining tool - specialized function that subtracts the second number twice from the first
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

# =============================================================================
# IMAGE AND STRING PROCESSING TOOLS
# Tools for manipulating images and processing strings
# =============================================================================

# Thumbnail generation tool - creates a 100x100 thumbnail from an image file
@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

# String to ASCII conversion tool - converts each character to its ASCII value
@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

# Exponential sum tool - calculates sum of e^x for each number in a list
@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

# Fibonacci sequence generator - returns the first n numbers in the Fibonacci sequence
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

# =============================================================================
# PAINT APPLICATION TOOLS 
# These tools use pywinauto to automate Microsoft Paint application
# =============================================================================

# Global variable to store the Paint application instance
# This is used by all Paint-related tools to access the same application window
paint_app = None

# Draw rectangle tool - Creates a rectangle in MS Paint between two coordinate points
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
        
        # Click on the Rectangle tool in the Paint ribbon (coordinates may need adjustment for different resolutions)
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

# Add text tool - Adds text at a specified location in MS Paint
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
        
        # Then click on the text tool in the Paint ribbon (coordinates may need adjustment for different resolutions)
        paint_window.click_input(coords=(512, 128))
        time.sleep(2)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # The following commented code is an alternative approach using keyboard shortcuts
        # Left here for reference but not used in the current implementation
        # paint_window.type_keys('t')
        # time.sleep(0.1)
        # paint_window.type_keys('x')
        # time.sleep(2)
        
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

        # Process the text content - store the original text
        full_text = text
        
        # The following commented code was an alternative approach for text processing
        # Left here for reference but not used in the current implementation
        # if "[" in full_text and "]" in full_text:
        #     # Keep the original format but ensure the numerical part is included
        #     start_idx = full_text.find("[")
        #     end_idx = full_text.find("]") + 1
        #     numerical_part = full_text[start_idx:end_idx]
        #     full_text = full_text.split(":")[0] + ": " + numerical_part
        
        # Handle spaces correctly for pywinauto's type_keys method
        # This replaces spaces with the {SPACE} keyword that pywinauto recognizes
        processed_text = full_text.replace(" ", "{SPACE}")
        paint_window.type_keys(processed_text)

        # The following commented code is an alternative approach for typing text
        # Left here for reference but not used in the current implementation
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

# Open Paint tool - Launches Microsoft Paint application and maximizes the window
@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on primary monitor"""
    global paint_app
    try:
        # Start the Paint application
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Maximize the window for better visibility
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

# =============================================================================
# DYNAMIC RESOURCES
# Resources are similar to tools but are accessed differently by the client
# They use the resource:// URI scheme
# =============================================================================

# Add a dynamic greeting resource - demonstrates how to implement a simple resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# =============================================================================
# PROMPT TEMPLATES
# Define prompt templates that can be used by clients
# These help structure the interaction between the AI and users
# =============================================================================

# Code review prompt template - provides a consistent format for code review requests
@mcp.prompt()
def review_code(code: str) -> str:
    """Prompt template for code review"""
    print("CALLED: review_code(code: str) -> str:")
    return f"Please review this code:\n\n{code}"

# Error debugging prompt template - provides a structured conversation for error debugging
@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Prompt template for debugging errors"""
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server mode
    else:
        mcp.run(transport="stdio")  # Run with stdio transport for production use
