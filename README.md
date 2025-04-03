# Agentic AI Mathematical Computation and Paint Tool

This project demonstrates the capabilities of agentic AI tools using the MCP (Model-Context Protocol) framework to perform mathematical operations and automate Microsoft Paint.

## Overview

The project consists of two main components:

1. **example2-3.py**: An MCP server that provides various mathematical tools and Microsoft Paint automation capabilities.
2. **talk2mcp-2.py**: A client that connects to the MCP server and uses Gemini AI to solve problems through an iterative process.

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

## Requirements

- Python 3.12+ (Python 3.13 may have compatibility issues with some libraries)
- Google Gemini API key

### Dependencies

```
pip install mcp google-generativeai python-dotenv pillow pywinauto
```

## Setup

1. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. Ensure Microsoft Paint is installed on your system (Windows only).

## Usage

1. Start the application by running:
   ```
   python talk2mcp-2.py
   ```

2. The script will:
   - Connect to the MCP server
   - Use Gemini AI to solve the math problem (finding ASCII values of "INDIA" and calculating the sum of exponentials)
   - Open Microsoft Paint
   - Draw a rectangle
   - Display the final result as text in Paint

## How It Works

### MCP Server (example2-3.py)

The server defines tools that can be called by the client:

1. **Math Tools**: Collection of mathematical operations
2. **String Processing Tools**: Functions to manipulate strings and convert to ASCII values
3. **Paint Tools**: Functions to automate Microsoft Paint operations

### Client (talk2mcp-2.py)

The client uses the Gemini AI model to solve problems in an iterative approach:

1. **Initialization**: Connects to the MCP server and retrieves available tools
2. **System Prompt Creation**: Generates a prompt with tool descriptions for the AI
3. **Iterative Problem Solving**:
   - AI evaluates the current state and decides which tool to use
   - Client executes the tool and collects results
   - Results are added to the context for the next iteration
4. **Result Visualization**: When the AI reaches a final answer, it's displayed in Microsoft Paint

## Project Structure

```
├── .env                  # Environment variables
├── example2-3.py         # MCP server with math and Paint tools
├── talk2mcp-2.py         # Client connecting to MCP server using Gemini AI
└── README.md             # Project documentation
```

## Troubleshooting

- If you encounter import errors, ensure all dependencies are installed correctly
- Python version compatibility: Python 3.12 is recommended (Python 3.13 may have issues with some libraries)
- Make sure Paint is installed and accessible on your system
- Verify your Gemini API key is correctly set in the .env file

## Extension Ideas

- Add more mathematical functions
- Implement more complex Paint operations
- Create custom visualizations for different problem types
- Support different LLM providers beyond Google Gemini
