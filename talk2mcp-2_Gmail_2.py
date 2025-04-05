# Import necessary libraries
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
# Import Google's generative AI library
# Note: Using google.generativeai directly instead of deprecated google.genai
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
import json
import webbrowser

# Load environment variables from .env file (including GEMINI_API_KEY and email settings)
load_dotenv()

# Configure the Gemini API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")
# Configure the generative AI client with the API key
client = genai.configure(api_key=api_key)

# Global variables to track conversation state
max_iterations = 10  # Maximum number of tool-calling iterations before stopping
last_response = None  # Stores the response from the most recent iteration
iteration = 0  # Counter for the current iteration
iteration_response = []  # List to store results from all iterations for context building
# Get email settings from environment variables with fallback
USER_EMAIL = os.getenv("USER_EMAIL", "your.email@gmail.com")  # Default email can be overridden by .env file
# OAuth client details for Gmail authentication
CLIENT_SECRET_FILE = 'client_secret_819038297150-71h5nap5siu85uh3eti1vhf3hpnm71c6.apps.googleusercontent.com.json'
TOKEN_PICKLE_FILE = 'token.pickle'

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content from Gemini with a timeout to prevent hanging
    
    Args:
        client: The configured Gemini client
        prompt: The text prompt to send to the model
        timeout: Maximum seconds to wait for a response (default: 10)
        
    Returns:
        The model's response, or raises an exception on timeout/error
    """
    print("Starting LLM generation...")
    try:
        # Initialize the Gemini model with appropriate model version
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Run the synchronous generate_content call in a separate thread
        # with a timeout to prevent the script from hanging indefinitely
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state
    Used at the beginning and end of main execution to ensure clean state
    """
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

def check_client_secret_file():
    """Verify that the OAuth client secret file exists and is valid
    
    Returns:
        bool: True if the file exists and contains valid OAuth credentials, False otherwise
    """
    try:
        if not os.path.exists(CLIENT_SECRET_FILE):
            print(f"ERROR: OAuth client secret file not found: {CLIENT_SECRET_FILE}")
            return False
            
        # Try to load and validate the JSON structure
        with open(CLIENT_SECRET_FILE, 'r') as f:
            client_data = json.load(f)
            
        # Check for required keys in the OAuth client secret format
        if 'installed' not in client_data:
            print("ERROR: Invalid client secret file. Missing 'installed' section.")
            return False
            
        required_keys = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
        for key in required_keys:
            if key not in client_data['installed']:
                print(f"ERROR: Invalid client secret file. Missing '{key}' in 'installed' section.")
                return False
                
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in client secret file: {CLIENT_SECRET_FILE}")
        return False
    except Exception as e:
        print(f"ERROR checking client secret file: {str(e)}")
        return False

async def main():
    reset_state()  # Reset state at the start of main execution
    print("Starting main execution...")
    print("\n" + "=" * 70)
    print("IMPORTANT: This application requires Gmail OAuth 2.0 authentication")
    print("Before running this application, you need to generate OAuth tokens")
    print("Please run 'manual_gmail_auth.py' first if you haven't already")
    print("Command: python manual_gmail_auth.py")
    print("\nThe manual_gmail_auth.py script will:")
    print("1. Provide an authorization URL to copy/paste into your browser")
    print("2. Guide you through the authentication process")
    print("3. Save the authorization tokens for use by this application")
    print("\nMake sure your .env file contains:")
    print("- USER_EMAIL: Your Gmail address that will be used for sending emails")
    print("=" * 70 + "\n")
    
    # Check if the OAuth token file exists before proceeding
    token_file = 'token.json'
    if not os.path.exists(token_file):
        print("ERROR: OAuth token file not found!")
        print(f"Please run 'python manual_gmail_auth.py' to create the token file.")
        return
    
    # Verify the OAuth client secret file exists and is valid
    if not check_client_secret_file():
        print("Cannot continue without a valid OAuth client secret file.")
        return
    
    # Inform user about the authorization process
    print("When prompted, please follow these steps to authorize Gmail access:")
    print("1. Copy the provided authorization URL and paste it into your browser")
    print("2. Choose the Gmail account you want to use (matching USER_EMAIL)")
    print("3. You may see a warning that the app is unverified - click 'Advanced' and 'Go to...'")
    print("4. Click 'Continue' to grant the application permission to send emails")
    print("5. Copy the authorization code shown and paste it back into this terminal")
    print("6. Press Enter to continue the authorization process")
    
    try:
        # Create a connection to the MCP server using example2-3_Gmail_2.py
        # which implements various math functions and email sending functions with OAuth
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3_Gmail_2.py"]
        )

        # Create a client that communicates with the MCP server via stdio
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            # Create a session with the MCP server to enable tool calling
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                try:
                    await session.initialize()
                    print("Session initialized successfully")
                except Exception as e:
                    print(f"Error initializing session: {e}")
                    print("This error might occur if there's a problem with the MCP server.")
                    raise
                    
                # Retrieve the list of available tools from the MCP server
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt that describes the available tools to the LLM
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # Parse tool objects and create descriptions for each tool
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Extract tool properties from the tool object
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema into a more readable format
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            # Create a formatted description of the tool
                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    # Join all tool descriptions into a single string for the system prompt
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                # Build the system prompt that instructs the LLM on how to use tools
                system_prompt = f"""You are an agent that can solve both text-based and mathematical problems in iterations. You have access to various tools for text processing, mathematics, and email sending.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [your answer]

CRITICAL INSTRUCTIONS:
- You must provide ONLY ONE function call per iteration - do not provide multiple function calls at once
- The system will execute your function call and return the result before asking for your next action
- First, carefully analyze what the query is asking for to determine which functions are needed
- Only use functions that are directly relevant to solving the current query
- Do not call functions unnecessarily - only call a function if its output is needed
- For example, only use strings_to_chars_to_int if you specifically need to convert characters to ASCII values
- Similarly, only use fibonacci_numbers or other math functions when the query requires them
- When a function returns multiple values, you need to process all of them
- For array parameters (like int_list_to_exponential_sum), pass all values in a single call separated by commas
- Do not repeat function calls with the same parameters - if a call gives an error, try a different format
- Only give FINAL_ANSWER when you have completed all necessary calculations or text processing
- Your final answer can be either text or numbers, depending on what the query asks for
- After calculating the final answer, you must send it via email using the send_email function:
  1. Call 'send_email' with these parameters:
     - recipient: Use '{USER_EMAIL}' (the user's own email)
     - subject: 'Final Answer from Agent'
     - message: Your final answer formatted as 'This is the FINAL_ANSWER by the agent: [your answer]'
  2. Only after sending the email, provide your FINAL_ANSWER

Examples of different types of problems (REMEMBER: ONE FUNCTION CALL PER ITERATION):
- For math: FUNCTION_CALL: add|5|3
- For string processing: FUNCTION_CALL: strings_to_chars_to_int|INDIA
- For string length: FUNCTION_CALL: length_string|Delhi
- For sequence generation: FUNCTION_CALL: fibonacci_numbers|6
- For array operations (CORRECT): FUNCTION_CALL: int_list_to_exponential_sum|73,78,68,73,65
- For array operations (INCORRECT): FUNCTION_CALL: int_list_to_exponential_sum|73|78|68|73|65
- For email: FUNCTION_CALL: send_email|{USER_EMAIL}|Final Answer from Agent|This is the FINAL_ANSWER by the agent: [0, 1, 1, 2, 3, 5]
- Final response can be text: FINAL_ANSWER: [Delhi]
- Or numbers: FINAL_ANSWER: [0, 1, 1, 2, 3, 5]

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # The main query to solve - specifically designed for the agent to demonstrate tool use
                query = """First find the length of string of the answer to the question\
                'What is the capital of India?' and \
                then Find the fibonacci numbers of the length of the answer\
                to the previous question \
                ('What is the capital of India?'). \
                send the result as an email to myself."""
                print("Starting iteration loop...")
                
                # Use global iteration variables for tracking state
                global iteration, last_response
                
                # Main iteration loop - runs until max_iterations or we get a final answer
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # Build the current query, including history from previous iterations
                    if last_response is None:
                        current_query = query  # First iteration uses the original query
                    else:
                        # For subsequent iterations, append previous iterations' results
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get the model's response with timeout protection
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        # Call Gemini to get the next action
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Ensure we only use the FUNCTION_CALL line if multiple lines are returned
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    # Process tool calls (when the model wants to use a function)
                    if response_text.startswith("FUNCTION_CALL:"):
                        # Parse the function call information from the LLM response
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        # Debug information about the function call
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool in the available tools list
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's expected input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            # Convert each parameter to the correct type based on the schema
                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input (comma-separated values)
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            # Call the tool with the prepared arguments
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Add delays after sending email to ensure it completes successfully
                            if func_name == "send_email":
                                await asyncio.sleep(2)  # Wait for email sending to complete
                            
                            # Extract and format the result content for the next iteration
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items in the result
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type for the next iteration
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            # Store the result for use in future iterations as context
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            # Handle errors during tool execution
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    # Process final answer when the model has completed the calculation
                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        print(f"Final answer: {response_text}")
                        break

                    # Increment iteration counter
                    iteration += 1

    except Exception as e:
        # Handle any unexpected errors during execution
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset global state at the end of main execution

# Script entry point
if __name__ == "__main__":
    asyncio.run(main())
    
    
