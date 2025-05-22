#!/usr/bin/env python3
"""
MCP Client Example

This script demonstrates how to use the MCP client to connect to a streamable HTTP server
and call tools.
"""
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from datetime import timedelta
from typing import Any
import mcp.types as types
from mcp.shared.context import RequestContext
from mcp.shared.message import SessionMessage
from mcp.shared.session import RequestResponder

# Define a custom notification handler function
async def custom_message_handler(
    message: RequestResponder[types.ServerRequest, types.ClientResult] 
    | types.ServerNotification 
    | Exception,
) -> None:
    """
    Custom handler that processes all incoming messages (both requests and notifications)
    """
    if isinstance(message, types.ServerNotification):
        print(f"Received notification: {message.root.__class__.__name__}")
        
        # Handle different notification types
        match message.root:
            case types.LoggingMessageNotification(params=params):
                print(f"Log message: {params.message}")
                print(f"Log level: {params.level}")
                # You could log this to a file, display it in UI, etc.
                
            case types.ResourceChangedNotification(params=params):
                print(f"Resource changed: {params.uri}")
                # You could refresh the resource in your UI, etc.
                
            case types.SamplingRequestedNotification(params=params):
                print(f"Sampling requested for: {params.request}")
                # You could show a UI prompt to approve/deny sampling
                
            case _:
                print(f"Unhandled notification type: {message.root}")
    
    elif isinstance(message, RequestResponder):
        print(f"Received request: {message.request.root.__class__.__name__}")
        # Handle requests if needed
    
    elif isinstance(message, Exception):
        print(f"Received exception: {type(message).__name__}: {str(message)}")
        # Handle exceptions appropriately
        
# Example of handling a specific notification type with a custom logging callback
async def custom_logging_callback(params: types.LoggingMessageNotificationParams) -> None:
    """Custom handler specifically for logging notifications"""
    level_map = {
        types.LoggingLevel.DEBUG: "DEBUG",
        types.LoggingLevel.INFO: "INFO",
        types.LoggingLevel.WARN: "WARNING",
        types.LoggingLevel.ERROR: "ERROR",
    }
    
    level_str = level_map.get(params.level, str(params.level))
    print(f"[{level_str}] {params.message}")
    
    # You could also forward this to a logging system
    # logging.log(convert_level(params.level), params.message)

async def main():
    print("Connecting to MCP server...")
    try:
        # Connect to a streamable HTTP server with a timeout
        async with streamablehttp_client("http://localhost:8000/mcp/v1/mcp") as (
            read_stream,
            write_stream,
            _,
        ):
            print("Connected to server, initializing session...")
            
            # Create a session using the client streams
            # We can pass a custom message handler if needed
            async with ClientSession(
                read_stream, 
                write_stream,
                read_timeout_seconds=timedelta(seconds=60),
                logging_callback=custom_logging_callback,
                message_handler=custom_message_handler,
            ) as session:
                # Initialize the connection
                await session.initialize()
                print("Session initialized successfully!")
                
                # List available tools (uncomment to use)
                # tools = await session.list_tools()
                # print("Available tools:", tools)

                print("\nCalling text-to-image generation tool...")
                
                # Call the mcp_create_text_to_image_task with progress callback
                task = await session.call_tool(
                    "mcp_create_text_to_image_task",
                    {
                        "prompt": "A beautiful sunset over the mountains",
                        "width": 512,
                        "height": 512,
                        "negitive_prompt": "tree",
                    },
                )
                print("Task: ",task )
                # Wait for the task to complete and get the result
                print("Waiting for task result...")
                result = await task.result()
                print("\nTask completed!")
                print("Result:", result)
                
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
