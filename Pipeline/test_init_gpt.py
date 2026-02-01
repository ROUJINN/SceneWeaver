#!/usr/bin/env python3
"""
Test script for init_gpt tool
Tests both LLM-only mode and full integration with Infinigen

Usage:
    # LLM-only test (quick - tests API calls only)
    cd Pipeline
    lg sceneweaver
    python test_init_gpt.py --mode llm_only

    # Full integration test (complete workflow)
    python test_init_gpt.py --mode full

    # Cleanup test files after test
    python test_init_gpt.py --mode llm_only --cleanup
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add Pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

import app.prompt.gpt.init_gpt as prompts
from app.llm import LLM
from app.tool.init_gpt import InitGPTExecute
from app.utils import extract_json


# Color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def log_info(msg: str) -> None:
    """Log info message in blue"""
    print(f"{Colors.OKCYAN}{msg}{Colors.ENDC}")


def log_success(msg: str) -> None:
    """Log success message in green"""
    print(f"{Colors.OKGREEN}{msg}{Colors.ENDC}")


def log_error(msg: str) -> None:
    """Log error message in red"""
    print(f"{Colors.FAIL}{msg}{Colors.ENDC}")


def log_warning(msg: str) -> None:
    """Log warning message in yellow"""
    print(f"{Colors.WARNING}{msg}{Colors.ENDC}")


def log_step(step_num: int, total_steps: int, description: str) -> None:
    """Log a test step"""
    print(f"\n{Colors.BOLD}[{step_num}/{total_steps}]{Colors.ENDC} {description}")


def setup_environment(test_dir: Path, mode: str = "llm_only") -> None:
    """Set up required environment variables"""
    log_info(f"Setting up environment in {test_dir}")
    log_info(f"Test mode: {mode}")

    os.environ["UserDemand"] = (
        "Design me a comfortable bedroom with a bed, nightstand, and wardrobe."
    )
    os.environ["iter"] = "0"
    os.environ["save_dir"] = str(test_dir)
    os.environ["roomtype"] = "bedroom"
    os.environ["sceneweaver_dir"] = str(Path(__file__).parent.parent)
    os.environ["socket"] = "False"  # Skip Blender socket for testing

    log_info("Environment variables set:")
    log_info(f"  UserDemand: {os.getenv('UserDemand')}")
    log_info(f"  iter: {os.getenv('iter')}")
    log_info(f"  save_dir: {os.getenv('save_dir')}")
    log_info(f"  roomtype: {os.getenv('roomtype')}")
    log_info(f"  sceneweaver_dir: {os.getenv('sceneweaver_dir')}")
    log_info(f"  socket: {os.getenv('socket')}")


def create_pipeline_dirs(test_dir: Path) -> None:
    """Create required directory structure"""
    log_info("Creating directory structure...")
    (test_dir / "pipeline").mkdir(parents=True, exist_ok=True)
    (test_dir / "args").mkdir(parents=True, exist_ok=True)
    (test_dir / "record_files").mkdir(parents=True, exist_ok=True)
    (test_dir / "record_scene").mkdir(parents=True, exist_ok=True)
    log_success("Directory structure created")


def validate_llm_response(response: str, step_name: str) -> Optional[Dict[str, Any]]:
    """Validate that LLM response contains valid JSON"""
    try:
        result = extract_json(response)
        if not result:
            log_error(f"{step_name}: No valid JSON found in response")
            return None
        log_success(f"{step_name}: Valid JSON found")
        return result
    except Exception as e:
        log_error(f"{step_name}: Failed to parse JSON - {e}")
        log_error(f"Response: {response[:500]}...")
        return None


def test_llm_initialization() -> Tuple[bool, Optional[LLM]]:
    """Test that LLM can be initialized with proper config"""
    log_step(0, 5, "Testing LLM initialization...")

    try:
        gpt = LLM()
        log_success("LLM initialized successfully")
        log_info(f"  Model: {gpt.model}")
        log_info(f"  Base URL: {gpt.base_url}")
        log_info(f"  Max tokens: {gpt.max_tokens}")
        log_info(f"  Temperature: {gpt.temperature}")
        return True, gpt
    except Exception as e:
        log_error(f"Failed to initialize LLM: {e}")
        traceback.print_exc()
        return False, None


def test_llm_step_1(tool: InitGPTExecute) -> Tuple[bool, Optional[Dict]]:
    """Test step 1: Get big objects and relations"""
    log_step(1, 5, "Testing Step 1 - Get big objects and relations...")

    start_time = time.time()

    try:
        user_demand = os.getenv("UserDemand")
        ideas = "A comfortable bedroom with essential furniture"
        roomtype = os.getenv("roomtype")

        log_info("Preparing prompt...")
        user_prompt = prompts.step_1_big_object_prompt_user.format(
            demand=user_demand, ideas=ideas, roomtype=roomtype
        )

        log_info("Calling LLM API (may take 30-60 seconds)...")
        gpt = LLM()
        gpt_text_response = gpt.ask(
            [{"role": "user", "content": user_prompt}],
            system_msgs=[
                {"role": "system", "content": prompts.step_1_big_object_prompt_system}
            ],
            temperature=1.0,
        )

        elapsed = time.time() - start_time
        log_info(f"LLM call completed in {elapsed:.1f}s")

        # Validate response
        result = validate_llm_response(gpt_text_response, "Step 1")
        if not result:
            return False, None

        # Check required fields
        required_fields = [
            "Room size",
            "Category list of big object",
            "Object against the wall",
        ]
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            log_error(f"Missing required fields: {missing_fields}")
            return False, None

        log_success(f"Step 1 passed with fields: {list(result.keys())}")
        log_info(f"  Room size: {result.get('Room size')}")
        log_info(
            f"  Categories: {list(result.get('Category list of big object', {}).keys())}"
        )

        return True, result

    except Exception as e:
        log_error(f"Step 1 failed: {e}")
        traceback.print_exc()
        return False, None


def test_llm_step_5(
    tool: InitGPTExecute, step1_result: Dict
) -> Tuple[bool, Optional[Dict]]:
    """Test step 5: Generate positions for big objects"""
    log_step(2, 5, "Testing Step 5 - Generate positions for big objects...")

    start_time = time.time()

    try:
        # Prepare data from step 1 result
        big_category_dict = step1_result["Category list of big object"]
        category_against_wall = step1_result["Object against the wall"]
        relation_big_object = step1_result.get("Relation between big objects", [])
        roomsize = step1_result["Room size"]

        # Convert to string format
        from app.utils import dict2str, lst2str

        big_category_dict_str = dict2str(big_category_dict)
        category_against_wall_str = lst2str(category_against_wall)
        relation_big_object_str = lst2str(relation_big_object)
        roomsize_str = lst2str(roomsize)

        log_info("Preparing prompt...")
        user_prompt = prompts.step_5_position_prompt_user.format(
            big_category_dict=big_category_dict_str,
            category_against_wall=category_against_wall_str,
            relation_big_object=relation_big_object_str,
            demand=os.getenv("UserDemand"),
            roomsize=roomsize_str,
        )

        log_info("Calling LLM API (may take 30-60 seconds)...")
        gpt = LLM()

        # Step 5 has retry logic in the original code
        success = False
        iter_count = 0
        max_retries = 5
        gpt_text_response = None

        while not success and iter_count < max_retries:
            iter_count += 1
            log_info(f"Attempt {iter_count}/{max_retries}...")
            gpt_text_response = gpt.ask(
                [{"role": "user", "content": user_prompt}],
                system_msgs=[
                    {"role": "system", "content": prompts.step_5_position_prompt_system}
                ],
                temperature=1.0,
            )

            try:
                result = extract_json(
                    gpt_text_response.replace("'", '"').replace("None", "null")
                )
                if "Placement" in result:
                    success = True
                    break
            except:
                log_warning(f"Attempt {iter_count} failed to parse JSON, retrying...")

        elapsed = time.time() - start_time
        log_info(f"LLM calls completed in {elapsed:.1f}s (after {iter_count} attempts)")

        if not success or not gpt_text_response:
            log_error("Step 5 failed after maximum retries")
            return False, None

        # Validate response
        result = extract_json(
            gpt_text_response.replace("'", '"').replace("None", "null")
        )
        if not result or "Placement" not in result:
            log_error("Step 5: Missing 'Placement' field in response")
            return False, None

        log_success(
            f"Step 5 passed with Placement keys: {list(result.get('Placement', {}).keys())}"
        )

        return True, result

    except Exception as e:
        log_error(f"Step 5 failed: {e}")
        traceback.print_exc()
        return False, None


def test_llm_step_3(tool: InitGPTExecute) -> Tuple[bool, Optional[Dict]]:
    """Test step 3: Map categories to Infinigen classes"""
    log_step(3, 5, "Testing Step 3 - Map to Infinigen classes...")

    start_time = time.time()

    try:
        # Use common categories for a bedroom
        category_list = ["bed", "nightstand", "wardrobe", "lamp", "book"]

        log_info("Preparing prompt...")
        user_prompt = prompts.step_3_class_name_prompt_user.format(
            category_list=str(category_list), demand=os.getenv("UserDemand")
        )

        log_info("Calling LLM API (may take 30-60 seconds)...")
        gpt = LLM()
        gpt_text_response = gpt.ask(
            [{"role": "user", "content": user_prompt}],
            system_msgs=[
                {"role": "system", "content": prompts.step_3_class_name_prompt_system}
            ],
            temperature=1.0,
        )

        elapsed = time.time() - start_time
        log_info(f"LLM call completed in {elapsed:.1f}s")

        # Validate response
        result = extract_json(
            gpt_text_response.replace("'", '"').replace("None", "null")
        )
        if not result or "Mapping results" not in result:
            log_error("Step 3: Missing 'Mapping results' field in response")
            return False, None

        mapping = result["Mapping results"]
        log_success(f"Step 3 passed with {len(mapping)} mappings")
        for cat, cls in mapping.items():
            if cls:
                log_info(f"  {cat} -> {cls}")
            else:
                log_warning(f"  {cat} -> (no match)")

        return True, result

    except Exception as e:
        log_error(f"Step 3 failed: {e}")
        traceback.print_exc()
        return False, None


def test_json_file_creation(test_dir: Path) -> bool:
    """Test that JSON files are created correctly"""
    log_step(4, 5, "Testing JSON file creation...")

    json_file = test_dir / "pipeline" / "init_gpt_results_0.json"

    if not json_file.exists():
        log_error(f"JSON file not found: {json_file}")
        return False

    try:
        with open(json_file, "r") as f:
            data = json.load(f)

        log_success(f"JSON file created successfully: {json_file}")
        log_info(f"  File size: {json_file.stat().st_size} bytes")
        log_info(f"  Keys: {list(data.keys())}")

        # Validate required fields
        required_fields = [
            "user_demand",
            "roomsize",
            "big_category_dict",
            "category_against_wall",
            "relation_big_object",
            "name_mapping",
            "Placement_big",
        ]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            log_warning(f"Missing optional fields: {missing_fields}")

        return True

    except Exception as e:
        log_error(f"Failed to read/parse JSON file: {e}")
        traceback.print_exc()
        return False


def test_full_integration(test_dir: Path) -> bool:
    """Test complete init_gpt workflow"""
    log_step(5, 5, "Testing full init_gpt.execute() workflow...")

    try:
        tool = InitGPTExecute()

        log_info("Calling tool.execute()...")
        log_info("Note: This may take several minutes as it calls Infinigen...")
        log_warning("If Infinigen is not properly configured, this step may fail")

        result = tool.execute(
            ideas="A comfortable bedroom with bed, nightstand, and wardrobe",
            roomtype="bedroom",
        )

        if "Successfully" in result:
            log_success(f"Full integration test passed: {result}")

            # Check for roominfo.json
            roominfo_file = test_dir / "roominfo.json"
            if roominfo_file.exists():
                with open(roominfo_file, "r") as f:
                    info = json.load(f)
                log_info(f"roominfo.json created: {list(info.keys())}")

            return True
        else:
            log_error(f"Full integration test failed: {result}")
            return False

    except Exception as e:
        log_error(f"Full integration test failed with exception: {e}")
        traceback.print_exc()
        return False


def test_llm_only(test_dir: Path) -> bool:
    """Test LLM calls only, skip Infinigen integration"""
    print("\n" + "=" * 60)
    print(f"{Colors.HEADER}{Colors.BOLD}LLM-Only Test (Quick){Colors.ENDC}")
    print("=" * 60 + "\n")

    total_start_time = time.time()

    # Setup
    setup_environment(test_dir, "llm_only")
    create_pipeline_dirs(test_dir)

    # Initialize tool
    tool = InitGPTExecute()

    # Test LLM initialization
    success, gpt = test_llm_initialization()
    if not success:
        return False

    # Test step 1: Get big objects and relations
    success, step1_result = test_llm_step_1(tool)
    if not success:
        log_error("LLM-Only Test: FAILED at Step 1")
        return False

    # Test step 5: Generate positions
    success, step5_result = test_llm_step_5(tool, step1_result)
    if not success:
        log_error("LLM-Only Test: FAILED at Step 5")
        return False

    # Test step 3: Map to Infinigen classes
    success, step3_result = test_llm_step_3(tool)
    if not success:
        log_error("LLM-Only Test: FAILED at Step 3")
        return False

    # Simulate JSON creation (like the real tool does)
    log_step(5, 5, "Simulating JSON file creation...")
    try:
        results = {
            "user_demand": os.getenv("UserDemand"),
            "roomsize": step1_result["Room size"],
            "big_category_dict": step1_result["Category list of big object"],
            "category_against_wall": step1_result["Object against the wall"],
            "relation_big_object": step1_result.get("Relation between big objects", []),
            "small_category_list": [],
            "relation_small_object": [],
            "name_mapping": step3_result.get("Mapping results", {}),
            "gpt_text_response": "test_response",
            "Placement_big": step5_result.get("Placement", {}),
            "Placement_small": [],
        }

        json_file = test_dir / "pipeline" / "init_gpt_results_0.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=4)

        log_success("JSON file created successfully")
    except Exception as e:
        log_error(f"Failed to create JSON file: {e}")
        return False

    # Validate JSON file
    if not test_json_file_creation(test_dir):
        log_error("LLM-Only Test: FAILED at JSON validation")
        return False

    total_elapsed = time.time() - total_start_time

    print("\n" + "=" * 60)
    print(f"{Colors.OKGREEN}{Colors.BOLD}LLM-Only Test: PASSED{Colors.ENDC}")
    print("=" * 60)
    print(f"{Colors.OKGREEN}Total time: {total_elapsed:.1f}s{Colors.ENDC}")
    print(f"{Colors.OKGREEN}All LLM API calls completed successfully!{Colors.ENDC}")
    print("=" * 60 + "\n")

    return True


def test_full_integration_mode(test_dir: Path) -> bool:
    """Test complete init_gpt workflow"""
    print("\n" + "=" * 60)
    print(f"{Colors.HEADER}{Colors.BOLD}Full Integration Test{Colors.ENDC}")
    print("=" * 60 + "\n")

    total_start_time = time.time()

    # Setup
    setup_environment(test_dir, "full")
    create_pipeline_dirs(test_dir)

    # Run full integration test
    if not test_full_integration(test_dir):
        print("\n" + "=" * 60)
        print(f"{Colors.FAIL}{Colors.BOLD}Full Integration Test: FAILED{Colors.ENDC}")
        print("=" * 60 + "\n")
        return False

    total_elapsed = time.time() - total_start_time

    print("\n" + "=" * 60)
    print(f"{Colors.OKGREEN}{Colors.BOLD}Full Integration Test: PASSED{Colors.ENDC}")
    print("=" * 60)
    print(f"{Colors.OKGREEN}Total time: {total_elapsed:.1f}s{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Complete workflow executed successfully!{Colors.ENDC}")
    print("=" * 60 + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test init_gpt tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # LLM-only test (quick - tests API calls only)
  python test_init_gpt.py --mode llm_only

  # Full integration test (complete workflow)
  python test_init_gpt.py --mode full

  # Cleanup test files after test
  python test_init_gpt.py --mode llm_only --cleanup
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["llm_only", "full"],
        default="llm_only",
        help="Test mode: llm_only (quick) or full (complete)",
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up test directory after test"
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        default=None,
        help="Use specific directory for test (default: auto-generated temp dir)",
    )

    args = parser.parse_args()

    # Create test directory
    if args.test_dir:
        test_dir = Path(args.test_dir)
        test_dir.mkdir(parents=True, exist_ok=True)
    else:
        test_dir = Path(tempfile.mkdtemp(prefix="test_init_gpt_"))

    print(f"\n{Colors.BOLD}Test directory: {test_dir}{Colors.ENDC}")

    # Print banner
    print("\n" + "=" * 60)
    print(f"{Colors.HEADER}{Colors.BOLD}InitGPT Tool Test Script{Colors.ENDC}")
    print("=" * 60)

    try:
        if args.mode == "llm_only":
            success = test_llm_only(test_dir)
        else:
            success = test_full_integration_mode(test_dir)

        # Cleanup if requested
        if args.cleanup:
            log_info(f"Cleaning up test directory: {test_dir}")
            try:
                shutil.rmtree(test_dir)
                log_success("Test directory cleaned up")
            except Exception as e:
                log_error(f"Failed to cleanup: {e}")
        else:
            print(f"\n{Colors.BOLD}Test files preserved in: {test_dir}{Colors.ENDC}")

        return 0 if success else 1

    except KeyboardInterrupt:
        log_warning("\nTest interrupted by user")
        if not args.cleanup:
            print(f"Test files preserved in: {test_dir}")
        return 130
    except Exception as e:
        log_error(f"\nUnexpected error: {e}")
        traceback.print_exc()
        if not args.cleanup:
            print(f"Test files preserved in: {test_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
