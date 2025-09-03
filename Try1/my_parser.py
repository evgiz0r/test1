# parser.py
import re


def parse_activity_text(text):
    """
    Parses textual activity definitions into a JSON-like structure.
    Supports: action <name> { ... }, referencing actions, operators, atomic nodes.
    """
    # Normalize whitespace and split into statements
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    text = text.strip()
    pos = 0
    length = len(text)
    warnings = []
    actions = {}

    def skip_whitespace():
        nonlocal pos
        while pos < length and text[pos].isspace():
            pos += 1

    def parse_name():
        nonlocal pos
        skip_whitespace()
        match = re.match(r'[a-zA-Z0-9_]+', text[pos:])
        if not match:
            next_pos = pos
            while next_pos < length and text[next_pos] not in [';', '}', '{']:
                next_pos += 1
            warnings.append(f"Warning: Expected name at position {pos}, skipping invalid token.")
            pos = next_pos
            return None
        name = match.group(0)
        pos += len(name)
        return name

    def parse_number():
        nonlocal pos
        skip_whitespace()
        match = re.match(r'\d+', text[pos:])
        if not match:
            warnings.append(f"Warning: Expected number at position {pos}, defaulting to 1.")
            return 1
        num = int(match.group(0))
        pos += len(match.group(0))
        return num

    def parse_block():
        nonlocal pos
        children = []
        skip_whitespace()
        while pos < length and text[pos] != '}':
            skip_whitespace()
            if text.startswith("repeat(", pos):
                pos += len("repeat(")
                n = parse_number()
                skip_whitespace()
                if pos >= length or text[pos] != ')':
                    warnings.append(f"Warning: Expected ')' after repeat number at position {pos}, skipping.")
                    while pos < length and text[pos] != '{':
                        pos += 1
                else:
                    pos += 1
                skip_whitespace()
                if pos >= length or text[pos] != '{':
                    warnings.append(f"Warning: Expected '{{' after repeat(n) at position {pos}, skipping.")
                    while pos < length and text[pos] != '}':
                        pos += 1
                    continue
                pos += 1
                block_children = parse_block()
                children.append({"type": "repeat", "times": n, "children": block_children})
                skip_whitespace()
                if pos < length and text[pos] == '}':
                    pos += 1
            elif text.startswith("sequence", pos):
                pos += len("sequence")
                skip_whitespace()
                if pos >= length or text[pos] != '{':
                    warnings.append(f"Warning: Expected '{{' after sequence at position {pos}, skipping.")
                    while pos < length and text[pos] != '}':
                        pos += 1
                    continue
                pos += 1
                block_children = parse_block()
                children.append({"type": "sequence", "children": block_children})
                skip_whitespace()
                if pos < length and text[pos] == '}':
                    pos += 1
            elif text.startswith("select", pos):
                pos += len("select")
                skip_whitespace()
                if pos >= length or text[pos] != '{':
                    warnings.append(f"Warning: Expected '{{' after select at position {pos}, skipping.")
                    while pos < length and text[pos] != '}':
                        pos += 1
                    continue
                pos += 1
                block_children = parse_block()
                children.append({"type": "select", "children": block_children})
                skip_whitespace()
                if pos < length and text[pos] == '}':
                    pos += 1
            elif text.startswith("parallel", pos):
                pos += len("parallel")
                skip_whitespace()
                if pos >= length or text[pos] != '{':
                    warnings.append(f"Warning: Expected '{{' after parallel at position {pos}, skipping.")
                    while pos < length and text[pos] != '}':
                        pos += 1
                    continue
                pos += 1
                block_children = parse_block()
                children.append({"type": "parallel", "children": block_children})
                skip_whitespace()
                if pos < length and text[pos] == '}':
                    pos += 1
            elif text.startswith("activity", pos):
                pos += len("activity")
                skip_whitespace()
                if pos >= length or text[pos] != '{':
                    warnings.append(f"Warning: Expected '{{' after activity at position {pos}, skipping.")
                    while pos < length and text[pos] != '}':
                        pos += 1
                    continue
                pos += 1
                block_children = parse_block()
                children.append({"type": "activity", "children": block_children})
                skip_whitespace()
                if pos < length and text[pos] == '}':
                    pos += 1
            else:
                # Could be atomic or action reference
                name = parse_name()
                skip_whitespace()
                if pos < length and text[pos] == ';':
                    pos += 1
                if name:
                    children.append({"type": "ref", "name": name})
            skip_whitespace()
        return children

    def parse_actions():
        nonlocal pos
        skip_whitespace()
        while pos < length:
            skip_whitespace()
            if text.startswith("action", pos):
                pos += len("action")
                skip_whitespace()
                action_name = parse_name()
                skip_whitespace()
                if pos < length and text[pos] == '{':
                    pos += 1
                    action_body = parse_block()
                    actions[action_name] = {"type": "action", "name": action_name, "children": action_body}
                    skip_whitespace()
                    if pos < length and text[pos] == '}':
                        pos += 1
                else:
                    warnings.append(f"Warning: Expected '{{' after action name at position {pos}.")
            else:
                # Skip unknown tokens
                pos += 1
        return actions

    actions = parse_actions()
    return {"actions": actions, "warnings": warnings}

def parse_pss_file(file_path):
    try:
        with open(file_path, "r") as f:
            text = f.read()
        return parse_activity_text(text)
    except FileNotFoundError:
        raise FileNotFoundError(f"PSS file not found: {file_path}. Please check the path or provide a fallback activity tree.")
