import json
import os
import subprocess
from typing import Any, Dict, List
from ollama import chat, ChatResponse

# Tool implementations
def list_dir(path: str = ".") -> str:
    """List all files in the specified directory."""
    try:
        files = os.listdir(path)
        return json.dumps({"success": True, "files": files})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def read_file(path: str) -> str:
    """Read the contents of a file."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        return json.dumps({"success": True, "content": content})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace old_text with new_text in a file."""
    try:
        with open(path, 'r') as f:
            content = f.read()

        if old_text not in content:
            return json.dumps({"success": False, "error": "Text not found in file"})

        new_content = content.replace(old_text, new_text, 1)

        with open(path, 'w') as f:
            f.write(new_content)

        return json.dumps({"success": True, "message": "File updated successfully"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

# Tool registry
TOOLS = {
    "list_dir": {
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
    },
    "read_file": {
        "function": read_file,
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        }
    },
    "edit_file": {
        "function": edit_file,
        "description": "Replace text in a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Text to replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "Text to replace it with"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }
    }
}

# System prompt
SYSTEM_PROMPT = """You are a code agent that helps with file operations. You have access to the following tools:

<tool>
tool: list_dir
description: List all files in a directory
parameters:
  - path: string (optional) - Directory path to list (default: current directory)
</tool>

<tool>
tool: read_file
description: Read the contents of a file
parameters:
  - path: string (required) - Path to the file to read
</tool>

<tool>
tool: edit_file
description: Replace text in a file
parameters:
  - path: string (required) - Path to the file to edit
  - old_text: string (required) - Text to replace
  - new_text: string (required) - Text to replace it with
</tool>

When you need to use a tool, respond in this JSON format:
{"tool": "tool_name", "arguments": {"arg1": "value1", "arg2": "value2"}}

When you don't need a tool, just respond with your answer.
"""

def run_model(messages: List[Dict]) -> ChatResponse:
    """Run the Ollama model with the given messages."""
    response: ChatResponse = chat(
        model="llama3.1:8b",
        messages=messages,
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

def run_agent():
    """Main agent loop."""
    print("Code Agent started. Type '/quit' to exit.")

    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    while True:
        user_input = input("\nWhat would you like to do? ")

        if user_input.lower() == '/quit':
            print("Goodbye!")
            break

        conversation.append({"role": "user", "content": user_input})

        # Get model response
        response = run_model(conversation)
        response_content = response.message.content.strip()

        # Check if it's a tool call
        tool_call = parse_tool_call(response_content)

        if tool_call:
            tool_name, arguments = tool_call
            print(f"\n[Calling tool: {tool_name}]")

            # Execute the tool
            result = execute_tool(tool_name, arguments)
            print(f"[Tool result: {result}]")

            # Add tool call and result to conversation
            conversation.append({
                "role": "assistant",
                "content": response_content
            })
            conversation.append({
                "role": "user",
                "content": f"Tool result: {result}"
            })

            # Get final response from model after tool execution
            response = run_model(conversation)
            final_content = response.message.content.strip()
            print(f"\n{final_content}")

            conversation.append({
                "role": "assistant",
                "content": final_content
            })
        else:
            # No tool call, just return the response
            print(f"\n{response_content}")
            conversation.append({
                "role": "assistant",
                "content": response_content
            })

if __name__ == "__main__":
    run_agent()
