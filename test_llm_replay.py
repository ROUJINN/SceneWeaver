#!/usr/bin/env python3
"""
Test script: Extract input from log file and replay with current llm.py
"""

import json
import os
import sys

sys.path.insert(0, "/home/lj/3D/SceneWeaver/Pipeline")

os.chdir("/home/lj/3D/SceneWeaver/Pipeline")

from app.llm import LLM

# Load the log file
log_file = "/home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0/llm_io_logs/llm_20260202_135354_712187.json"

with open(log_file) as f:
    data = json.load(f)

print("=" * 60)
print("REPLAYING LLM REQUEST")
print("=" * 60)
print(f"Method: {data['method']}")
print(f"Original output length: {len(data['output']['content'])}")
print()

# Extract input
method = data["method"]
messages = data["input"]["messages"]
system_msgs = data["input"].get("system_messages")

# Check for base64_image
has_image = any("base64_image" in msg for msg in messages)
print(f"Number of messages: {len(messages)}")
print(f"System messages: {len(system_msgs) if system_msgs else 0}")
print(f"Has base64_image: {has_image}")
print()

# Initialize LLM
print("Initializing LLM...")
llm = LLM()

# Replay the request
print("Sending request to LLM...")
print()

try:
    if method == "ask":
        result = llm.ask(messages, system_msgs=system_msgs)
    elif method == "ask_tool":
        tools = data.get("tools", None)
        result = llm.ask_tool(messages, system_msgs=system_msgs, tools=tools)
    elif method == "ask_with_images":
        # Extract base64_image from messages and build images list
        # Then remove base64_image from messages since ask_with_images will re-add it
        images = []
        for msg in messages:
            if "base64_image" in msg:
                images.append({"base64": msg["base64_image"]})
                msg.pop("base64_image", None)  # Remove from messages so it's not duplicated
        print(f"Found {len(images)} images")
        result = llm.ask_with_images(messages, images=images, system_msgs=system_msgs)
    else:
        print(f"Unknown method: {method}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("NEW RESULT")
    print("=" * 60)
    print(f"Result length: {len(result)}")
    print()
    print("=== First 500 chars ===")
    print(result[:500])
    print()
    print("=== Last 500 chars ===")
    print(result[-500:])
    print()

    # Check if JSON is complete
    json_start = result.find("{")
    if json_start >= 0:
        json_part = result[json_start:]
        open_braces = json_part.count("{")
        close_braces = json_part.count("}")

        print("=== JSON Analysis ===")
        print(f"Open braces: {open_braces}")
        print(f"Close braces: {close_braces}")
        print(f"JSON complete: {open_braces == close_braces}")

        try:
            parsed = json.loads(json_part)
            print(f"JSON parsing: SUCCESS ({len(parsed)} keys)")
        except json.JSONDecodeError as e:
            print(f"JSON parsing: FAILED - {e}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
