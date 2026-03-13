import json
import os

file_path = r'd:\AI projects\AI blue red team SLM\dataset\security_dataset.jsonl'
output_path = r'd:\AI projects\AI blue red team SLM\dataset\security_dataset_fixed.jsonl'

def fix_line(line):
    while True:
        try:
            json.loads(line)
            return line
        except json.JSONDecodeError as e:
            if "escape" in str(e).lower():
                # The error position e.pos is the position of the invalid backslash.
                # We fix it by escaping it (adding another backslash).
                line = line[:e.pos] + '\\\\' + line[e.pos+1:]
            else:
                print(f"Non-escape error at line {i+1}: {e}")
                return line

with open(file_path, 'r', encoding='utf-8') as f, \
     open(output_path, 'w', encoding='utf-8') as out:
    for i, line in enumerate(f):
        fixed = fix_line(line)
        out.write(fixed)

print("Done fixing. Validating fixed file...")

validation_success = True
with open(output_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Fixed file still has error at line {i+1}: {e}")
            validation_success = False

if validation_success:
    print("Validation successful. Overwriting original file...")
    import shutil
    shutil.copy(output_path, file_path)
    print("Original file updated.")
else:
    print("Validation failed. Not overwriting original file.")
