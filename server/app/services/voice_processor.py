from fastapi import UploadFile
import asyncio
from typing import Dict, Any, Optional
import aiofiles
import os
from ..config import settings
from .stt_service import STTService
from ..core.logging import setup_logging
from ..core.interfaces import VoiceProcessorInterface
from .azure_ai import AzureAIService
import uuid
from datetime import datetime

logger = setup_logging()

class VoiceProcessor(VoiceProcessorInterface):
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.stt_service = STTService()
        self.ai_service = AzureAIService()
        self.processing_stats: Dict[str, Dict] = {}

    async def process_audio(self, audio_file: UploadFile) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        temp_path = f"temp_{task_id}_{audio_file.filename}"
        
        try:
            # Initialize processing stats
            self.processing_stats[task_id] = {
                "start_time": datetime.now(),
                "status": "processing",
                "file_size": 0
            }

            # Save uploaded file
            async with aiofiles.open(temp_path, 'wb') as f:
                content = await audio_file.read()
                self.processing_stats[task_id]["file_size"] = len(content)
                await f.write(content)
            
            # Create and track processing task
            task = asyncio.create_task(self._process_audio_file(temp_path, task_id))
            self.active_tasks[task_id] = task
            
            result = await task
            
            # Update stats
            self.processing_stats[task_id].update({
                "end_time": datetime.now(),
                "status": "completed",
                "duration": (datetime.now() - self.processing_stats[task_id]["start_time"]).total_seconds()
            })
            
            return {
                "task_id": task_id,
                "result": result,
                "stats": self.processing_stats[task_id]
            }
            
        except asyncio.CancelledError:
            self.processing_stats[task_id]["status"] = "cancelled"
            logger.info(f"Audio processing cancelled for task {task_id}")
            raise
        except Exception as e:
            self.processing_stats[task_id]["status"] = "failed"
            self.processing_stats[task_id]["error"] = str(e)
            logger.error(f"Audio processing failed: {str(e)}")
            raise
        finally:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _process_audio_file(self, file_path: str, task_id: str) -> Dict[str, Any]:
        async with aiofiles.open(file_path, 'rb') as f:
            audio_data = await f.read()
            
        # Speech to text
        stt_result = await self.stt_service.speech_to_text(audio_data)
        
        # AI analysis
        intent_analysis = await self.ai_service.analyze_text(stt_result["text"])
        
        return {
            "text": stt_result["text"],
            "confidence": stt_result["confidence"],
            "language": stt_result["language"],
            "segments": stt_result["segments"],
            "intent": intent_analysis
        }

    async def interrupt_processing(self, task_id: str) -> bool:
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            try:
                await self.active_tasks[task_id]
            except asyncio.CancelledError:
                pass
            
            # Initialize stats if not exists
            if task_id not in self.processing_stats:
                self.processing_stats[task_id] = {
                    "start_time": datetime.now(),
                    "status": "initialized"
                }
                
            self.processing_stats[task_id]["status"] = "interrupted"
            self.processing_stats[task_id]["end_time"] = datetime.now()
            del self.active_tasks[task_id]
            return True
        return False

    def get_processing_stats(self, task_id: Optional[str] = None) -> Dict:
        if task_id:
            return self.processing_stats.get(task_id, {})
        return self.processing_stats
