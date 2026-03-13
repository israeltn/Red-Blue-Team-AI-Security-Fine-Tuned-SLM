import json

file_path = r'd:\AI projects\AI blue red team SLM\dataset\security_dataset.jsonl'
with open(file_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Line {i+1}: {e}")
            # Identify the character at the error position
            start = max(0, e.pos - 20)
            end = min(len(line), e.pos + 20)
            print(f"Context: {line[start:end]}")
            print(f"Error at pos {e.pos}: {repr(line[e.pos])}")
