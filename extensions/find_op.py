#!/usr/bin/env python3
"""Script to find opcode information in rv_f and generate binary pattern."""

import sys
import os

# Load arg_lut.csv into a dictionary
def load_arg_lut():
    """Load arg_lut.csv and return a dictionary mapping arg names to (high, low) bits."""
    arg_lut = {}
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'arg_lut.csv')
    with open(csv_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Parse: "name", high, low
            parts = line.split(',')
            if len(parts) == 3:
                name = parts[0].strip().strip('"')
                high = int(parts[1].strip())
                low = int(parts[2].strip())
                arg_lut[name] = (high, low)
    return arg_lut

def find_op_in_files(op_name):
    """Find the line in ratified folder that starts with op_name."""
    ratified_dir = os.path.join(os.path.dirname(__file__), 'ratified')
    
    # Get all files in ratified directory
    if not os.path.isdir(ratified_dir):
        return None
    
    files = os.listdir(ratified_dir)
    
    for filename in files:
        file_path = os.path.join(ratified_dir, filename)
        if not os.path.isfile(file_path):
            continue
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Handle pseudo_op lines: $pseudo_op rv_i::fence fence.tso ...
                if line.startswith('$pseudo_op'):
                    # Remove $pseudo_op prefix
                    line = line.replace('$pseudo_op ', '', 1)
                    # Now line is like: rv_i::fence fence.tso 31..28=8 ...
                    # Remove the namespace part (first word with ::)
                    parts = line.split()
                    if len(parts) >= 2 and '::' in parts[0]:
                        line = ' '.join(parts[1:])
                    # Now line is like: fence.tso 31..28=8 ...
                
                # Skip comments
                if line.startswith('#'):
                    continue
                
                # Get the first word (opcode name)
                parts = line.split()
                if not parts:
                    continue
                first_word = parts[0]
                if first_word == op_name:
                    # Return everything after the opcode name
                    if len(parts) > 1:
                        return ' '.join(parts[1:])
                    return ''
    
    return None

def parse_field(field_str):
    """Parse a field like '14..12=2' or '6..2=0x01' and return (high, low, value_bits)."""
    if '..' in field_str and '=' in field_str:
        # Format: high..low=value
        range_part, value_part = field_str.split('=')
        high, low = map(int, range_part.split('..'))
        
        # Convert value to binary
        if value_part.startswith('0x'):
            value = int(value_part, 16)
        else:
            value = int(value_part)
        
        # Calculate number of bits needed
        num_bits = high - low + 1
        # Format with leading zeros to match the bit width
        value_bits = format(value, '0{}b'.format(num_bits))
        return (high, low, value_bits)
    
    # Handle single bit format like "12=0"
    if '=' in field_str:
        parts = field_str.split('=')
        bit_pos = int(parts[0])
        value = int(parts[1])
        value_bits = format(value, '01b')  # Single bit
        return (bit_pos, bit_pos, value_bits)
    
    return None

def generate_binary_pattern(remaining_content, arg_lut):
    """Generate a binary pattern with * for parameters and binary for fixed values, grouped by fields."""
    # Initialize a 32-character array with '0' (or we can use a different placeholder for unset bits)
    pattern = ['0'] * 32
    
    # Parse each field in the content
    fields = remaining_content.split()
    field_info = []  # Store (low, high, bits) for each field in order
    
    for field in fields:
        # Check if it's a fixed value field like "14..12=2" or "12=0"
        if '=' in field:
            result = parse_field(field)
            if result is not None:
                high, low, value_bits = result
                for i, bit in enumerate(value_bits):
                    pattern[31 - (low + i)] = bit  # bit 31 is index 0
                field_info.append((low, high, value_bits))
                continue
        # Otherwise it's a parameter name, look it up in arg_lut
        if field in arg_lut:
                high, low = arg_lut[field]
                num_bits = high - low + 1
                value_bits = '*' * num_bits
                # Replace with * for each bit position
                for i in range(num_bits):
                    pattern[31 - (low + i)] = '*'
                field_info.append((low, high, value_bits))
    
    # Sort by high bit position (descending order) to match the actual bit layout (high to low)
    field_info.sort(key=lambda x: x[1], reverse=True)
    
    # Build output with spaces between fields
    result_parts = [bits for _, _, bits in field_info]
    return ' '.join(result_parts)

def main():
    import sys
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: find_op.py <opcode_name>\n")
        sys.exit(1)
    
    op_name = sys.argv[1]
    
    # Load arg_lut
    arg_lut = load_arg_lut()
    
    # Find the opcode in ratified folder
    remaining_content = find_op_in_files(op_name)
    
    if remaining_content is None:
        sys.stderr.write("Error: opcode '{}' not found in ratified folder\n".format(op_name))
        sys.exit(1)
    
    # Generate binary pattern
    pattern = generate_binary_pattern(remaining_content, arg_lut)
    
    # Output the result
    print('"{}"'.format(pattern))

if __name__ == '__main__':
    main()
