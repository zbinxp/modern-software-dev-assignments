# import
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Callable
from ollama import chat, ChatResponse

# define tools
def list_dir( path = None):
    # list current dir
    return os.listdir(path)

TOOLS={
    "list_dir":{
        "function": list_dir,
        "description": "List all files in a directory",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: current directory)"
                }
            },
            "required": []
        }
    }
}

def run_model(conversation:List[Dict])-> ChatResponse:
    response:ChatResponse = chat(
        model="llama3.1:8b",
        messages=conversation,
        options={"temperature": 0.3},
    )
    return response

def execute_tool(tool_name: str, arguments: Dict) -> str:
    """Execute a tool and return the result."""
    if tool_name not in TOOLS:
        return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})

    tool = TOOLS[tool_name]
    func = tool["function"]

    # Get required parameters
    params = tool["parameters"]["properties"]
    required = tool["parameters"].get("required", [])

    # Build kwargs from arguments
    kwargs = {}
    for param_name in params:
        if param_name in arguments:
            kwargs[param_name] = arguments[param_name]
        elif param_name in required:
            return json.dumps({"success": False, "error": f"Missing required parameter: {param_name}"})

    return func(**kwargs)

def parse_tool_call(response_content: str) -> tuple[str, Dict] | None:
    """Parse tool call from model response."""
    try:
        # Try to find JSON in the response
        data = json.loads(response_content.strip())
        if "tool" in data and "arguments" in data:
            return data["tool"], data["arguments"]
    except json.JSONDecodeError:
        pass
    return None

# start agent
def run_agent():
    print("agent started.")
    conversation = [
        {"role": "system", "content": """You'are a helpful assistant. 
            Here're a list of tools you can use.
            
            <tool>
            tool: list_dir
            description: list all of files in the directory
            arguments: None
            </tool>
            
            When you need to use a tool, respond in this JSON format:
        {"tool": "tool_name", "arguments": {"arg1": "value1", "arg2": "value2"}}

        When you don't need a tool, just respond with your answer.
        """},
    ]
    while True:
        user_prompt = input("\nwhat's up?")
        if user_prompt == 'quit':
            print('byte!')
            break
        
        conversation.append({
            "role": "user", "content": user_prompt
        })
        # execute the prompt
        res = run_model(conversation)
        # print(f'res: {res}')
        # if response is a tool use, append to conversation, send to model
        content = res.message.content.strip()
        tool_call = parse_tool_call(content)
        if tool_call:
            tool_name, tool_arguments = tool_call
            # execute the tool calls and save results to conversation
            tool_result = execute_tool(tool_name, tool_arguments)
            print(f"[Tool result: {tool_result}]")
            
            conversation.append({"role":"assistant", "content": content})
            conversation.append({"role":"user", "content":f"Tool result: {tool_result}"})
            # Get final response from model after tool execution
            response = run_model(conversation)
            final_content = response.message.content.strip()
            print(f"\n{final_content}")
            
        else:
            # else, just return the content
            print(f"\n{content}")

if __name__ == "__main__":
    run_agent()