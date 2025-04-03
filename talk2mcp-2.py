import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
# from google import genai
# Import the correct package
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file (including GEMINI_API_KEY)
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)  # Old method

# Configure the API key for Gemini API
client = genai.configure(api_key=api_key)

# Global variables to track conversation state
max_iterations = 3  # Maximum number of tool-calling iterations
last_response = None  # Stores the response from the previous iteration
iteration = 0  # Current iteration count
iteration_response = []  # List to store results from all iterations

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
        # Initialize the Gemini model
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
    Used at the beginning and end of main execution
    """
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset state at the start of main execution
    print("Starting main execution...")
    try:
        # Create a connection to the MCP server using example2-3.py
        # which implements various math functions and Paint tool commands
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3.py"]
        )

        # Create a client that communicates with the MCP server
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            # Create a session with the MCP server
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                try:
                    await session.initialize()
                    print("Session initialized successfully")
                except Exception as e:
                    print(f"Error initializing session: {e}")
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
                    
                    # Join all tool descriptions into a single string
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                # Build the system prompt that instructs the LLM on how to use tools
                system_prompt = f"""You are a math agent solving problems in iterations. You have access to various mathematical tools.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [number]

Important:
- When a function returns multiple values, you need to process all of them
- Only give FINAL_ANSWER when you have completed all necessary calculations
- Do not repeat function calls with the same parameters

Examples:
- FUNCTION_CALL: add|5|3
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FINAL_ANSWER: [42]

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # The main query to solve
                query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. """
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
                        # Parse the function call information
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        # Debug information about the function call
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool in the available tools
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
                                    # Handle array input
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
                            
                            # Extract and format the result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
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
                            
                            # Store the result for use in future iterations
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
                        
                        # Open Microsoft Paint to visualize the result
                        result = await session.call_tool("open_paint")
                        print(result.content[0].text)

                        # Wait for Paint to be fully maximized
                        await asyncio.sleep(2)

                        # Draw a rectangle on the Paint canvas
                        result = await session.call_tool(
                            "draw_rectangle",
                            arguments={
                                "x1": 600,
                                "y1": 400,
                                "x2": 1000,
                                "y2": 600
                            }
                        )
                        print(result.content[0].text)

                        await asyncio.sleep(2)

                        # Add the final result text to the Paint canvas
                        print("Adding text...")
                        print(f"Sending text: {response_text}")

                        result = await session.call_tool(
                            "add_text_in_paint",
                            arguments={
                                "text": response_text
                            }
                        )
                        print(result.content[0].text)
                        print("All steps completed.")
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
    
    
