#!/usr/bin/env python3
"""
MCP Server Example

This script implements a simple MCP server with echo and add tools
for testing the MCP client.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from aiohttp import web
from mcp import (
    ServerSession,
    StreamPair,
    ToolDefinition,
    ToolParameterDefinition,
    ToolResultDefinition,
)


# Define tools
TOOLS = [
    ToolDefinition(
        name="echo",
        description="Echoes back the message",
        parameters=[
            ToolParameterDefinition(
                name="message",
                type="string",
                description="The message to echo",
                required=True,
            )
        ],
        result=ToolResultDefinition(
            type="string",
            description="The echoed message",
        ),
    ),
    ToolDefinition(
        name="add",
        description="Adds two numbers",
        parameters=[
            ToolParameterDefinition(
                name="a",
                type="number",
                description="First number",
                required=True,
            ),
            ToolParameterDefinition(
                name="b",
                type="number",
                description="Second number",
                required=True,
            ),
        ],
        result=ToolResultDefinition(
            type="number",
            description="The sum of a and b",
        ),
    ),
    ToolDefinition(
        name="mcp_create_text_to_image_task",
        description="Creates a text to image generation task and sends progress notifications",
        parameters=[
            ToolParameterDefinition(
                name="prompt",
                type="string",
                description="The prompt for image generation",
                required=True,
            ),
            ToolParameterDefinition(
                name="width",
                type="number",
                description="Width of the image",
                required=True,
            ),
            ToolParameterDefinition(
                name="height",
                type="number",
                description="Height of the image",
                required=True,
            ),
            ToolParameterDefinition(
                name="num_images",
                type="number",
                description="Number of images to generate",
                required=True,
            ),
        ],
        result=ToolResultDefinition(
            type="object",
            description="The result of the image generation task",
        ),
    ),
]


class MCPServer:
    """
    A simple MCP server implementation.
    """

    async def handle_tool_call(
        self, tool_name: str, params: Dict[str, Any], tool_call=None
    ) -> Any:
        """Handle tool calls based on the tool name."""
        if tool_name == "echo":
            return params.get("message", "")
        elif tool_name == "add":
            return params.get("a", 0) + params.get("b", 0)
        elif tool_name == "mcp_create_text_to_image_task":
            # Simulate an image generation task with progress notifications
            prompt = params.get("prompt", "")
            width = params.get("width", 512)
            height = params.get("height", 512)
            num_images = params.get("num_images", 1)
            
            # Send progress notifications if tool_call is provided
            if tool_call and hasattr(tool_call, "send_notification"):
                # Initial status
                await tool_call.send_notification({
                    "type": "status",
                    "status": "starting",
                    "message": f"Starting image generation for: {prompt}"
                })
                
                # Simulate progress
                for i in range(1, 5):
                    await asyncio.sleep(1)  # Simulate processing time
                    progress = i * 25
                    await tool_call.send_notification({
                        "type": "progress",
                        "progress": progress,
                        "message": f"Generating image: {progress}% complete"
                    })
                
                # Final notification before returning result
                await tool_call.send_notification({
                    "type": "status",
                    "status": "completed",
                    "message": "Image generation complete!"
                })
            
            # Return simulated result
            return {
                "images": [
                    {
                        "url": f"https://example.com/images/generated_{i}.png",
                        "width": width,
                        "height": height
                    } for i in range(num_images)
                ],
                "prompt": prompt
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def handle_session(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle an MCP session."""
        stream_pair = StreamPair(reader, writer)
        session = ServerSession(stream_pair)

        # Configure the session with available tools
        session.set_tools(TOOLS)

        # Initialize the session
        await session.initialize()

        # Process tool calls
        async for tool_call in session.tool_calls():
            try:
                result = await self.handle_tool_call(
                    tool_call.name, tool_call.parameters, tool_call
                )
                await tool_call.return_success(result)
            except Exception as e:
                await tool_call.return_error(str(e))


async def handle_mcp_request(request: web.Request) -> web.StreamResponse:
    """Handle MCP requests over HTTP."""
    response = web.StreamResponse()
    await response.prepare(request)
    
    # Create bidirectional streams
    reader = request.content
    writer = response
    
    server = MCPServer()
    await server.handle_session(reader, writer)
    
    return response


async def main():
    """Start the MCP server."""
    app = web.Application()
    app.router.add_post('/mcp/v1/mcp', handle_mcp_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    
    print("MCP Server running at http://localhost:8000/mcp/v1/mcp")
    await site.start()
    
    # Keep the server running
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
