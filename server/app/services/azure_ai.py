import os
import json
from typing import Dict, Any, List, Optional, Union
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage, UserMessage, AssistantMessage,
    ChatCompletionsToolCall, ChatCompletionsToolDefinition,
    CompletionsFinishReason, FunctionDefinition,
    ToolMessage, TextContentItem, ImageContentItem,
    ImageUrl, ImageDetailLevel
)
from azure.core.credentials import AzureKeyCredential
from ..core.logging import setup_logging
from ..config import settings
from datetime import datetime
import asyncio
from enum import Enum
import tempfile

logger = setup_logging()

class ModelType(Enum):
    CODESTRAL = "Codestral-2501"
    JAMBA = "AI21-Jamba-1.5-Large"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"

class AzureAIService:
    def __init__(self):
        self._setup_clients()
        self._register_tools()
        
    def _setup_clients(self):
        """Initialize Azure AI clients for different models"""
        try:
            self.credentials = AzureKeyCredential(settings.AZURE_TOKEN)
            self.endpoint = settings.AZURE_ENDPOINT
            
            self.clients: Dict[str, ChatCompletionsClient] = {}
            for model in ModelType:
                self.clients[model.value] = ChatCompletionsClient(
                    endpoint=self.endpoint,
                    credential=self.credentials
                )
            
            logger.info("Azure AI clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI clients: {str(e)}")
            raise

    def _register_tools(self):
        """Register available tools and functions"""
        self.available_tools = {
            "flight_info": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="get_flight_info",
                    description="Returns information about flights between cities",
                    parameters={
                        "type": "object",
                        "properties": {
                            "origin_city": {
                                "type": "string",
                                "description": "Origin city",
                            },
                            "destination_city": {
                                "type": "string",
                                "description": "Destination city",
                            },
                        },
                        "required": ["origin_city", "destination_city"],
                    },
                )
            ),
            "email": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="manage_email",
                    description="Manage email operations like sending, reading, and searching emails",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["send", "read", "search", "draft"],
                                "description": "Email action to perform"
                            },
                            "recipient": {
                                "type": "string",
                                "description": "Email recipient address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "content": {
                                "type": "string",
                                "description": "Email content"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query for emails"
                            }
                        },
                        "required": ["action"]
                    }
                )
            ),
            "media_control": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="control_media",
                    description="Control media playback on connected services (Spotify, YouTube Music)",
                    parameters={
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "enum": ["spotify", "youtube_music"],
                                "description": "Media service to control"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["play", "pause", "next", "previous", "search", "playlist"],
                                "description": "Media control action"
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query or playlist name"
                            }
                        },
                        "required": ["service", "action"]
                    }
                )
            ),
            "weather": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="get_weather",
                    description="Get weather information for a location",
                    parameters={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City or coordinates"
                            },
                            "forecast_type": {
                                "type": "string",
                                "enum": ["current", "hourly", "daily"],
                                "description": "Type of forecast"
                            }
                        },
                        "required": ["location"]
                    }
                )
            ),
            "task_manager": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="manage_tasks",
                    description="Manage user tasks and reminders",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "update", "delete", "list", "remind"],
                                "description": "Task management action"
                            },
                            "task_id": {
                                "type": "string",
                                "description": "Task identifier"
                            },
                            "title": {
                                "type": "string",
                                "description": "Task title"
                            },
                            "description": {
                                "type": "string",
                                "description": "Task description"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "Task due date (ISO format)"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Task priority"
                            }
                        },
                        "required": ["action"]
                    }
                )
            ),
            "home_automation": ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name="control_home",
                    description="Control smart home devices and automation",
                    parameters={
                        "type": "object",
                        "properties": {
                            "device_type": {
                                "type": "string",
                                "enum": ["light", "thermostat", "security", "camera", "speaker"],
                                "description": "Type of device to control"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "Device identifier"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["on", "off", "adjust", "status", "scene"],
                                "description": "Control action"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Additional parameters for the action"
                            }
                        },
                        "required": ["device_type", "action"]
                    }
                )
            )
        }

    async def process_request(
        self,
        messages: List[Dict[str, Any]],
        model_type: ModelType,
        tools: List[str] = None,
        stream: bool = False,
        image_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Process requests with appropriate model and configuration"""
        try:
            start_time = datetime.now()
            
            # Prepare messages
            formatted_messages = self._format_messages(messages, image_data)
            
            # Get required tools
            selected_tools = [
                self.available_tools[tool]
                for tool in (tools or [])
                if tool in self.available_tools
            ]
            
            # Process with appropriate model
            client = self.clients[model_type.value]
            
            if stream:
                return self._stream_response(client, formatted_messages, model_type)
            
            response = await self._process_with_model(
                client, formatted_messages, selected_tools, model_type
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "result": response,
                "model": model_type.value,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            raise

    def _format_messages(
        self,
        messages: List[Dict[str, Any]],
        image_data: Optional[bytes] = None
    ) -> List[Union[SystemMessage, UserMessage, AssistantMessage]]:
        """Format messages for the AI models"""
        formatted = []
        for msg in messages:
            content = msg["content"]
            role = msg["role"]
            
            if role == "system":
                formatted.append(SystemMessage(content=content))
            elif role == "user":
                if image_data and len(formatted) == 0:
                    # Handle image input
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(image_data)
                        formatted.append(UserMessage(
                            content=[
                                TextContentItem(text=content),
                                ImageContentItem(
                                    image_url=ImageUrl.load(
                                        image_file=temp_file.name,
                                        image_format="jpg",
                                        detail=ImageDetailLevel.HIGH
                                    )
                                ),
                            ],
                        ))
                else:
                    formatted.append(UserMessage(content=content))
            elif role == "assistant":
                formatted.append(AssistantMessage(content=content))
                
        return formatted

    async def _process_with_model(
        self,
        client: ChatCompletionsClient,
        messages: List[Any],
        tools: List[ChatCompletionsToolDefinition],
        model_type: ModelType
    ) -> Dict[str, Any]:
        """Process request with specific model"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.complete(
                    messages=messages,
                    tools=tools if tools else None,
                    model=model_type.value
                )
            )
            
            if (response.choices[0].finish_reason == 
                CompletionsFinishReason.TOOL_CALLS):
                # Handle tool calls
                return await self._handle_tool_calls(
                    client, messages, response, tools, model_type
                )
            
            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Model processing failed: {str(e)}")
            raise

    async def _handle_tool_calls(
        self,
        client: ChatCompletionsClient,
        messages: List[Any],
        response: Any,
        tools: List[ChatCompletionsToolDefinition],
        model_type: ModelType
    ) -> Dict[str, Any]:
        """Handle tool calls from the model"""
        messages.append(
            AssistantMessage(tool_calls=response.choices[0].message.tool_calls)
        )
        
        results = []
        for tool_call in response.choices[0].message.tool_calls:
            if isinstance(tool_call, ChatCompletionsToolCall):
                function_args = json.loads(
                    tool_call.function.arguments.replace("'", '"')
                )
                # Execute tool function
                result = await self._execute_tool(
                    tool_call.function.name,
                    function_args
                )
                messages.append(
                    ToolMessage(tool_call_id=tool_call.id, content=result)
                )
                results.append(result)
        
        # Get final response
        final_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.complete(
                messages=messages,
                tools=tools,
                model=model_type.value
            )
        )
        
        return {
            "content": final_response.choices[0].message.content,
            "tool_results": results,
            "finish_reason": final_response.choices[0].finish_reason
        }

    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> str:
        """Execute tool function"""
        try:
            if tool_name == "get_flight_info":
                return await self._execute_flight_info(args)
            elif tool_name == "manage_email":
                return await self._execute_email_management(args)
            elif tool_name == "control_media":
                return await self._execute_media_control(args)
            elif tool_name == "get_weather":
                return await self._execute_weather_info(args)
            elif tool_name == "manage_tasks":
                return await self._execute_task_management(args)
            elif tool_name == "control_home":
                return await self._execute_home_automation(args)
            
            return json.dumps({"error": "Tool not implemented"})
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return json.dumps({"error": str(e)})

    async def _execute_flight_info(self, args: Dict[str, Any]) -> str:
        # Implement actual flight info logic here
        return json.dumps({
            "airline": "Demo Airline",
            "flight_number": "DA123",
            "flight_date": "2024-05-07",
            "flight_time": "10:00"
        })

    async def _execute_email_management(self, args: Dict[str, Any]) -> str:
        action = args.get("action")
        # Implement email management logic here
        return json.dumps({
            "status": "success",
            "action": action,
            "message": f"Email {action} operation completed"
        })

    async def _execute_media_control(self, args: Dict[str, Any]) -> str:
        service = args.get("service")
        action = args.get("action")
        # Implement media control logic here
        return json.dumps({
            "status": "success",
            "service": service,
            "action": action,
            "message": f"{action.capitalize()} command sent to {service}"
        })

    async def _execute_weather_info(self, args: Dict[str, Any]) -> str:
        location = args.get("location")
        forecast_type = args.get("forecast_type", "current")
        # Implement weather info logic here
        return json.dumps({
            "location": location,
            "forecast_type": forecast_type,
            "temperature": "22°C",
            "condition": "Partly Cloudy"
        })

    async def _execute_task_management(self, args: Dict[str, Any]) -> str:
        action = args.get("action")
        # Implement task management logic here
        return json.dumps({
            "status": "success",
            "action": action,
            "task_id": args.get("task_id", "new_task"),
            "message": f"Task {action} completed"
        })

    async def _execute_home_automation(self, args: Dict[str, Any]) -> str:
        device_type = args.get("device_type")
        action = args.get("action")
        # Implement home automation logic here
        return json.dumps({
            "status": "success",
            "device_type": device_type,
            "action": action,
            "message": f"{device_type.capitalize()} {action} command executed"
        })

    async def _stream_response(
        self,
        client: ChatCompletionsClient,
        messages: List[Any],
        model_type: ModelType
    ):
        """Stream responses from the model"""
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.complete(
                stream=True,
                messages=messages,
                model=model_type.value
            )
        )
        
        async def response_generator():
            for update in response:
                if update.choices:
                    yield update.choices[0].delta.content or ""
                    
        return response_generator()

    async def analyze_text(self, text: str) -> dict:
        try:
            response = await self.chat_client.chat.create_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analyze the user's intent and emotion from their message."},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return {
                "analysis": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {}
            }
        except Exception as e:
            logger.error(f"Failed to analyze text: {str(e)}")
            return {"analysis": "", "error": str(e)}
