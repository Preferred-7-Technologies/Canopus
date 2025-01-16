from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    name: str
    command: str
    expected_result: Dict[str, Any]
    variables: Dict[str, str] = None
    timeout: float = 5.0
    tags: List[str] = None

@dataclass
class TestResult:
    test_case: TestCase
    actual_result: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    execution_time: float = 0.0

class CommandTester:
    def __init__(self, command_processor):
        self.command_processor = command_processor
        self.test_suites: Dict[str, List[TestCase]] = {}
        self._load_test_suites()

    def _load_test_suites(self):
        try:
            test_dir = Path("data/tests")
            test_dir.mkdir(exist_ok=True)
            
            for suite_file in test_dir.glob("*.json"):
                try:
                    with open(suite_file, "r") as f:
                        data = json.load(f)
                        suite_name = data["name"]
                        test_cases = [
                            TestCase(**test_data)
                            for test_data in data["test_cases"]
                        ]
                        self.test_suites[suite_name] = test_cases
                        logger.info(f"Loaded test suite: {suite_name}")
                except Exception as e:
                    logger.error(f"Failed to load test suite {suite_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load test suites: {str(e)}")

    async def run_test_suite(self, suite_name: str) -> List[TestResult]:
        suite = self.test_suites.get(suite_name)
        if not suite:
            raise ValueError(f"Test suite {suite_name} not found")

        results = []
        for test_case in suite:
            result = await self.run_test(test_case)
            results.append(result)

        return results

    async def run_test(self, test_case: TestCase) -> TestResult:
        start_time = asyncio.get_event_loop().time()
        try:
            actual_result = await asyncio.wait_for(
                self.command_processor(test_case.command, test_case.variables),
                timeout=test_case.timeout
            )
            
            success = self._compare_results(
                actual_result,
                test_case.expected_result
            )
            
            return TestResult(
                test_case=test_case,
                actual_result=actual_result,
                success=success,
                execution_time=asyncio.get_event_loop().time() - start_time
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_case=test_case,
                actual_result={},
                success=False,
                error="Test timed out",
                execution_time=test_case.timeout
            )
        except Exception as e:
            return TestResult(
                test_case=test_case,
                actual_result={},
                success=False,
                error=str(e),
                execution_time=asyncio.get_event_loop().time() - start_time
            )

    def _compare_results(self, actual: Dict, expected: Dict) -> bool:
        try:
            for key, value in expected.items():
                if key not in actual:
                    return False
                if isinstance(value, dict):
                    if not self._compare_results(actual[key], value):
                        return False
                elif actual[key] != value:
                    return False
            return True
        except Exception:
            return False

    def save_test_suite(self, suite_name: str, test_cases: List[TestCase]):
        try:
            test_dir = Path("data/tests")
            test_dir.mkdir(exist_ok=True)
            
            suite_data = {
                "name": suite_name,
                "test_cases": [
                    {
                        "name": test.name,
                        "command": test.command,
                        "expected_result": test.expected_result,
                        "variables": test.variables,
                        "timeout": test.timeout,
                        "tags": test.tags
                    }
                    for test in test_cases
                ]
            }
            
            with open(test_dir / f"{suite_name}.json", "w") as f:
                json.dump(suite_data, f, indent=2)
            
            self.test_suites[suite_name] = test_cases
            logger.info(f"Saved test suite: {suite_name}")
            
        except Exception as e:
            logger.error(f"Failed to save test suite: {str(e)}")
            raise
