from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import spacy
from fuzzywuzzy import fuzz
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CommandTemplate:
    name: str
    patterns: List[str]
    response_template: str
    variables: Dict[str, str]
    category: str
    min_confidence: float = 0.75

class VoiceTemplateManager:
    def __init__(self):
        self.templates: Dict[str, CommandTemplate] = {}
        self.nlp = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialize_nlp()
        self._load_templates()

    def _initialize_nlp(self):
        try:
            # Load small English model for better performance
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("NLP engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize NLP engine: {str(e)}")
            raise

    def _load_templates(self):
        try:
            template_dir = Path("data/templates")
            template_dir.mkdir(exist_ok=True)
            
            for template_file in template_dir.glob("*.json"):
                try:
                    with open(template_file, "r") as f:
                        data = json.load(f)
                        template = CommandTemplate(**data)
                        self.templates[template.name] = template
                        logger.info(f"Loaded template: {template.name}")
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load templates: {str(e)}")

    async def match_command(self, command: str) -> Optional[Tuple[CommandTemplate, Dict[str, str], float]]:
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor,
                self._process_command,
                command
            )
        except Exception as e:
            logger.error(f"Command matching failed: {str(e)}")
            return None

    def _process_command(self, command: str) -> Optional[Tuple[CommandTemplate, Dict[str, str], float]]:
        command_doc = self.nlp(command.lower())
        best_match = None
        best_score = 0
        best_vars = {}

        for template in self.templates.values():
            for pattern in template.patterns:
                # Calculate similarity score
                pattern_doc = self.nlp(pattern.lower())
                base_score = command_doc.similarity(pattern_doc)
                
                # Add fuzzy string matching score
                fuzzy_score = fuzz.ratio(command.lower(), pattern.lower()) / 100
                combined_score = (base_score + fuzzy_score) / 2

                if combined_score > best_score:
                    extracted_vars = self._extract_variables(command_doc, pattern)
                    if extracted_vars is not None:
                        best_match = template
                        best_score = combined_score
                        best_vars = extracted_vars

        if best_match and best_score >= best_match.min_confidence:
            return best_match, best_vars, best_score
        return None

    def _extract_variables(self, command_doc, pattern: str) -> Optional[Dict[str, str]]:
        try:
            variables = {}
            for ent in command_doc.ents:
                # Match named entities with template variables
                if ent.label_ in ["TIME", "DATE", "PERSON", "ORG", "GPE"]:
                    variables[ent.label_.lower()] = ent.text
            return variables
        except Exception as e:
            logger.error(f"Variable extraction failed: {str(e)}")
            return None

    def __del__(self):
        self.executor.shutdown(wait=True)