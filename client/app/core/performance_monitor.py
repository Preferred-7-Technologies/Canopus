import psutil
import time
from dataclasses import dataclass
from typing import Dict, List
import logging
from pathlib import Path
import json
from datetime import datetime
import asyncio
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    command_latency: float
    timestamp: str

class PerformanceMonitor:
    def __init__(self):
        self.metrics_dir = Path("data/metrics")
        self.metrics_dir.mkdir(exist_ok=True)
        self.metrics_history = deque(maxlen=1000)
        self.running = False
        self._start_time = time.time()
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage": 90.0,
            "command_latency": 2.0  # seconds
        }

    async def start_monitoring(self):
        self.running = True
        while self.running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check thresholds and log warnings
                self._check_thresholds(metrics)
                
                # Save metrics periodically
                if len(self.metrics_history) % 100 == 0:
                    self._save_metrics()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {str(e)}")
                await asyncio.sleep(5)

    def stop_monitoring(self):
        self.running = False
        self._save_metrics()

    def _collect_metrics(self) -> PerformanceMetrics:
        return PerformanceMetrics(
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            network_io={
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            },
            command_latency=self._calculate_command_latency(),
            timestamp=datetime.now().isoformat()
        )

    def _check_thresholds(self, metrics: PerformanceMetrics):
        if metrics.cpu_percent > self.thresholds["cpu_percent"]:
            logger.warning(f"High CPU usage: {metrics.cpu_percent}%")
        
        if metrics.memory_percent > self.thresholds["memory_percent"]:
            logger.warning(f"High memory usage: {metrics.memory_percent}%")
        
        if metrics.disk_usage > self.thresholds["disk_usage"]:
            logger.warning(f"High disk usage: {metrics.disk_usage}%")
        
        if metrics.command_latency > self.thresholds["command_latency"]:
            logger.warning(f"High command latency: {metrics.command_latency}s")

    def _calculate_command_latency(self) -> float:
        # Implement command latency calculation logic
        # This is a placeholder implementation
        return 0.1

    def _save_metrics(self):
        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = self.metrics_dir / f"metrics_{current_time}.json"
            
            metrics_data = {
                "start_time": self._start_time,
                "end_time": time.time(),
                "metrics": [
                    {
                        "cpu_percent": m.cpu_percent,
                        "memory_percent": m.memory_percent,
                        "disk_usage": m.disk_usage,
                        "network_io": m.network_io,
                        "command_latency": m.command_latency,
                        "timestamp": m.timestamp
                    }
                    for m in self.metrics_history
                ]
            }
            
            with open(metrics_file, "w") as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {str(e)}")

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else self._collect_metrics()
