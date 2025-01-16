from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from ....services.azure_ai import AzureAIService, ModelType
from ....core.security import verify_api_key
from typing import Dict, Any, List
from fastapi.responses import StreamingResponse
import json

router = APIRouter()
azure_service = AzureAIService()

@router.post("/analyze")
async def analyze_text(
    text: str,
    api_key: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    try:
        result = await azure_service.analyze_text(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...),
    api_key: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    try:
        audio_data = await audio.read()
        result = await azure_service.speech_to_text(audio_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete")
async def complete_request(
    messages: List[Dict[str, Any]],
    model: ModelType,
    tools: List[str] = Query(None),
    stream: bool = False,
    api_key: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    try:
        result = await azure_service.process_request(
            messages=messages,
            model_type=model,
            tools=tools,
            stream=stream
        )
        
        if stream:
            return StreamingResponse(
                result,
                media_type="text/event-stream"
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-image")
async def analyze_image(
    prompt: str,
    image: UploadFile = File(...),
    api_key: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    try:
        image_data = await image.read()
        messages = [
            {"role": "system", "content": "You are an image analysis assistant."},
            {"role": "user", "content": prompt}
        ]
        
        result = await azure_service.process_request(
            messages=messages,
            model_type=ModelType.GPT4O,
            image_data=image_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))