from dataclasses import dataclass
from typing import List, Dict, Optional
import json
from pathlib import Path
import logging
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class MacroStep:
    command: str
    delay: float = 0.0  # Delay in seconds before executing this step
    condition: Optional[str] = None  # Condition to check before executing
    timeout: float = 30.0  # Maximum time to wait for condition

@dataclass
class CommandMacro:
    name: str
    description: str
    steps: List[MacroStep]
    variables: Dict[str, str]
    enabled: bool = True

class MacroManager:
    def __init__(self, command_processor):
        self.command_processor = command_processor
        self.macros: Dict[str, CommandMacro] = {}
        self._load_macros()

    def _load_macros(self):
        try:
            macro_dir = Path("data/macros")
            macro_dir.mkdir(exist_ok=True)
            
            for macro_file in macro_dir.glob("*.json"):
                try:
                    with open(macro_file, "r") as f:
                        data = json.load(f)
                        steps = [MacroStep(**step) for step in data["steps"]]
                        macro = CommandMacro(
                            name=data["name"],
                            description=data["description"],
                            steps=steps,
                            variables=data.get("variables", {}),
                            enabled=data.get("enabled", True)
                        )
                        self.macros[macro.name] = macro
                        logger.info(f"Loaded macro: {macro.name}")
                except Exception as e:
                    logger.error(f"Failed to load macro {macro_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load macros: {str(e)}")

    async def execute_macro(self, macro_name: str, variables: Dict[str, str] = None) -> List[Dict]:
        try:
            macro = self.macros.get(macro_name)
            if not macro or not macro.enabled:
                raise ValueError(f"Macro {macro_name} not found or disabled")

            results = []
            for step in macro.steps:
                # Replace variables in command
                command = self._replace_variables(step.command, variables)
                
                # Wait for specified delay
                if step.delay > 0:
                    await asyncio.sleep(step.delay)
                
                # Check condition if specified
                if step.condition:
                    condition_met = await self._check_condition(
                        self._replace_variables(step.condition, variables),
                        step.timeout
                    )
                    if not condition_met:
                        raise TimeoutError(f"Condition not met: {step.condition}")

                # Execute command
                result = await self.command_processor(command)
                results.append({
                    "step": command,
                    "result": result
                })

            return results

        except Exception as e:
            logger.error(f"Failed to execute macro {macro_name}: {str(e)}")
            raise

    def _replace_variables(self, text: str, variables: Dict[str, str] = None) -> str:
        if not variables:
            return text
        
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    async def _check_condition(self, condition: str, timeout: float) -> bool:
        try:
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                result = await self.command_processor(condition)
                if result and result.get("success", False):
                    return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            logger.error(f"Condition check failed: {str(e)}")
            return False

    def save_macro(self, macro: CommandMacro):
        try:
            macro_dir = Path("data/macros")
            macro_dir.mkdir(exist_ok=True)
            
            macro_data = {
                "name": macro.name,
                "description": macro.description,
                "steps": [
                    {
                        "command": step.command,
                        "delay": step.delay,
                        "condition": step.condition,
                        "timeout": step.timeout
                    }
                    for step in macro.steps
                ],
                "variables": macro.variables,
                "enabled": macro.enabled
            }
            
            with open(macro_dir / f"{macro.name}.json", "w") as f:
                json.dump(macro_data, f, indent=2)
            
            self.macros[macro.name] = macro
            logger.info(f"Saved macro: {macro.name}")
            
        except Exception as e:
            logger.error(f"Failed to save macro: {str(e)}")
            raise
