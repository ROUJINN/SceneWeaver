#!/usr/bin/env python3
"""
Test script to check LLM output truncation.
"""
import json

log_file = '/home/lj/3D/SceneWeaver/fxxkingresults/Design_me_a_bedroom_0/llm_io_logs/llm_20260202_135354_712187.json'

with open(log_file) as f:
    data = json.load(f)

content = data['output']['content']

print(f"=== File: {log_file}")
print(f"=== Method: {data['method']}")
print(f"=== Content length: {len(content)}")
print()
print("=== First 1000 chars of output ===")
print(content[:1000])
print()
print("=== Last 500 chars of output ===")
print(content[-500:])
print()

# Check if JSON is complete
json_start = content.find('```json')
if json_start == -1:
    json_start = content.find('{\n  "')

if json_start >= 0:
    json_part = content[json_start:]
    # Remove the ```json and ``` markers
    json_part = json_part.replace('```json', '').replace('```', '').strip()

    # Count braces to see if JSON is complete
    open_braces = json_part.count('{')
    close_braces = json_part.count('}')
    open_brackets = json_part.count('[')
    close_brackets = json_part.count(']')

    print(f"=== JSON Analysis ===")
    print(f"Open braces {{: {open_braces}")
    print(f"Close braces }}: {close_braces}")
    print(f"Open brackets [: {open_brackets}")
    print(f"Close brackets ]: {close_brackets}")
    print(f"JSON complete: {open_braces == close_braces and open_brackets == close_brackets}")
    print()

    # Try to parse the JSON
    try:
        parsed = json.loads(json_part)
        print("=== JSON parsing: SUCCESS ===")
        print(f"Number of keys in parsed JSON: {len(parsed)}")
    except json.JSONDecodeError as e:
        print(f"=== JSON parsing: FAILED ===")
        print(f"Error: {e}")
        print(f"Error position: line {e.lineno}, column {e.colno}")
else:
    print("No JSON found in output")
