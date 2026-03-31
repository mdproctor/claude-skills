#!/usr/bin/env python3
"""
Convert Graphviz (dot) diagrams in markdown files to Mermaid format.
"""

import re
import sys
from pathlib import Path

def convert_graphviz_to_mermaid(dot_code):
    """
    Convert a Graphviz digraph to Mermaid flowchart.

    Args:
        dot_code: String containing the Graphviz code

    Returns:
        String containing the Mermaid code
    """
    lines = dot_code.strip().split('\n')

    # Extract graph name from first line
    first_line = lines[0]
    graph_match = re.match(r'digraph\s+(\w+)\s*{', first_line)

    # Start Mermaid flowchart (TD = top-down)
    mermaid_lines = ['flowchart TD']

    # Track node IDs and their shapes
    node_shapes = {}
    node_labels = {}

    # Process each line
    for line in lines[1:]:
        line = line.strip()

        if line == '}':
            continue

        # Node definition: "NodeName" [shape=diamond] or with style attributes;
        node_def_match = re.match(r'"([^"]+)"\s*\[([^\]]+)\];?', line)
        if node_def_match:
            label = node_def_match.group(1)
            attributes = node_def_match.group(2)

            # Extract shape from attributes
            shape_match = re.search(r'shape=(\w+)', attributes)
            shape = shape_match.group(1) if shape_match else 'box'

            # Create unique ID from label
            node_id = re.sub(r'[^a-zA-Z0-9]', '_', label)
            node_shapes[label] = shape
            node_labels[label] = node_id

            # Map Graphviz shapes to Mermaid syntax
            if shape == 'diamond':
                mermaid_lines.append(f'    {node_id}{{{label}}}')
            elif shape == 'doublecircle':
                mermaid_lines.append(f'    {node_id}(({label}))')
            elif shape == 'box':
                mermaid_lines.append(f'    {node_id}[{label}]')
            else:
                mermaid_lines.append(f'    {node_id}[{label}]')
            continue

        # Edge definition: "A" -> "B" [label="yes"];
        edge_match = re.match(r'"([^"]+)"\s*->\s*"([^"]+)"(?:\s*\[label="([^"]*)"\])?;?', line)
        if edge_match:
            from_node = edge_match.group(1)
            to_node = edge_match.group(2)
            label = edge_match.group(3) if edge_match.group(3) else ""

            # Get node IDs
            from_id = node_labels.get(from_node, re.sub(r'[^a-zA-Z0-9]', '_', from_node))
            to_id = node_labels.get(to_node, re.sub(r'[^a-zA-Z0-9]', '_', to_node))

            # Create edge
            if label:
                mermaid_lines.append(f'    {from_id} -->|{label}| {to_id}')
            else:
                mermaid_lines.append(f'    {from_id} --> {to_id}')

    return '\n'.join(mermaid_lines)


def convert_file(file_path):
    """
    Convert all Graphviz diagrams in a markdown file to Mermaid.

    Args:
        file_path: Path to the markdown file

    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Find all ```dot blocks
    pattern = r'```dot\n(.*?)\n```'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if not matches:
        return False

    # Replace from end to start to preserve indices
    new_content = content
    for match in reversed(matches):
        dot_code = match.group(1)
        mermaid_code = convert_graphviz_to_mermaid(dot_code)

        # Replace the entire code block
        new_block = f'```mermaid\n{mermaid_code}\n```'
        new_content = new_content[:match.start()] + new_block + new_content[match.end():]

    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)

    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Convert specific file
        file_path = Path(sys.argv[1])
        if convert_file(file_path):
            print(f"✅ Converted {file_path}")
        else:
            print(f"⚠️  No Graphviz diagrams found in {file_path}")
    else:
        print("Usage: python convert_graphviz_to_mermaid.py <file.md>")
        sys.exit(1)
