import re
import sys

# Define your instruction set with necessary details
INSTRUCTION_SET = {
    "addi":   {"task_id": "11", "modtag": "1000", "type": "arithmetic"},
    "add":    {"task_id": "11", "modtag": "0000", "type": "arithmetic"},
    "subi":   {"task_id": "11", "modtag": "1001", "type": "arithmetic"},
    "sub":    {"task_id": "11", "modtag": "0001", "type": "arithmetic"},
    "muli":   {"task_id": "11", "modtag": "1010", "type": "arithmetic"},
    "mul":    {"task_id": "11", "modtag": "0010", "type": "arithmetic"},
    "divi":   {"task_id": "11", "modtag": "1011", "type": "arithmetic"},
    "div":    {"task_id": "11", "modtag": "0011", "type": "arithmetic"},
    # Task ID '01' - Memory Instructions
    "st":     {"task_id": "01", "modtag": "00",   "type": "memo"},
    "ld":     {"task_id": "01", "modtag": "01",   "type": "memo"},
    "lui":    {"task_id": "01", "modtag": "10",   "type": "memo"},
    "ldm":    {"task_id": "01", "modtag": "11",   "type": "memo"},
    # Task ID '10' - Flow Instructions
    "beq":    {"task_id": "10", "modtag": "000",  "type": "flow"},
    "bne":    {"task_id": "10", "modtag": "001",  "type": "flow"},
    "blt":    {"task_id": "10", "modtag": "010",  "type": "flow"},
    "bge":    {"task_id": "10", "modtag": "011",  "type": "flow"},
    "bgt":    {"task_id": "10", "modtag": "100",  "type": "flow"},
    "ble":    {"task_id": "10", "modtag": "101",  "type": "flow"},
    "pcset":  {"task_id": "10", "modtag": "110",  "type": "flow"},
    "jump":   {"task_id": "10", "modtag": "111",  "type": "flow"},
    # Added 'break' instruction
    "break":  {"task_id": "00", "modtag": "1111", "type": "glitch"}
}

def parse_instruction(instruction):
    parts = instruction.strip().split()
    if not parts:
        return None, None, None, None, None
    operation = parts[0].lower()
    if operation not in INSTRUCTION_SET:
        return None, None, None, None, None
    instr_type = INSTRUCTION_SET[operation]["type"]
    rd = rs1 = rs2 = imm = '0'  # Initialize all variables to default values

    if instr_type == "memo":
        if len(parts) < 4:
            return None, None, None, None, None
        rd = parts[1].rstrip(',')[1:]    # RD
        rs1 = parts[2].rstrip(',')[1:]   # RS1
        imm = parts[3]                   # IMM
    elif instr_type == "flow":
        if operation == "pcset":
            if len(parts) < 3:
                return None, None, None, None, None
            rs1 = parts[1].rstrip(',')[1:]  # RS1
            imm = parts[2]                  # IMM
        elif operation == "jump":
            if len(parts) < 4:
                return None, None, None, None, None
            rd = parts[1].rstrip(',')[1:]    # RD
            rs1 = parts[2].rstrip(',')[1:]   # RS1
            imm = parts[3]                    # IMM
        else:
            if len(parts) < 4:
                return None, None, None, None, None
            rs1 = parts[1].rstrip(',')[1:]   # RS1
            rs2 = parts[2].rstrip(',')[1:]   # RS2
            imm = parts[3]                    # IMM
    elif instr_type == "arithmetic":
        if len(parts) < 4:
            return None, None, None, None, None
        rd = parts[1].rstrip(',')[1:]      # RD
        rs1 = parts[2].rstrip(',')[1:]     # RS1
        if operation.endswith('i'):
            imm = parts[3]                 # IMM
        else:
            rs2 = parts[3].rstrip(',')[1:] # RS2
    elif instr_type == "glitch":
        # 'break' instruction has no operands
        rd = rs1 = rs2 = imm = '0'
    else:
        return None, None, None, None, None
    return operation, rd, rs1, rs2, imm

def to_binary(value, bits):
    try:
        if isinstance(value, str) and value.startswith('0x'):
            val = int(value, 16)
        else:
            val = int(value)
    except ValueError:
        return None
    if val < 0:
        val = (1 << bits) + val
    return format(val, f'0{bits}b')[-bits:]

def convert_to_binary(fields, operation):
    task_id = INSTRUCTION_SET[operation]['task_id']    # bits 0-1 (LSB)
    modtag = INSTRUCTION_SET[operation]['modtag']      # bits after task_id

    if INSTRUCTION_SET[operation]["type"] == "memo":
        imm_bin = to_binary(fields['imm'], 12)         # bits 23-12
        rs1_bin = to_binary(fields['rs1'], 4)          # bits 11-8
        rd_bin = to_binary(fields['rd'], 4)            # bits 7-4
        binary_representation = imm_bin + rs1_bin + rd_bin + modtag + task_id
    elif INSTRUCTION_SET[operation]["type"] == "flow":
        if operation == "pcset":
            imm_bin = to_binary(fields['imm'], 12)     # bits 23-12
            padding = '0' * 4                          # bits 11-8
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 7-4
            binary_representation = imm_bin + padding + rs1_bin + modtag + task_id
        elif operation == "jump":
            imm_bin = to_binary(fields['imm'], 16)     # Assuming 16-bit imm for jump
            if imm_bin is None:
                return None
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 15-12
            rd_bin = to_binary(fields['rd'], 4)        # bits 11-8
            binary_representation = imm_bin + rs1_bin + rd_bin + modtag + task_id
        else:
            imm_bin = to_binary(fields['imm'], 11)     # bits 23-13 for other flow instructions
            rs2_bin = to_binary(fields['rs2'], 4)      # bits 12-9
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 8-5
            binary_representation = imm_bin + rs2_bin + rs1_bin + modtag + task_id
    elif INSTRUCTION_SET[operation]["type"] == "arithmetic":
        rd_bin = to_binary(fields['rd'], 4)            # bits 17-14
        rs1_bin = to_binary(fields['rs1'], 4)          # bits 13-10
        if operation.endswith('i'):
            imm_bin = to_binary(fields['imm'], 10)     # bits 23-14
            if imm_bin is None:
                return None
            binary_representation = imm_bin + rs1_bin + rd_bin + modtag + task_id
        else:
            padding = '0' * 6                          # bits 23-18
            rs2_bin = to_binary(fields['rs2'], 4)      # bits 17-14
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 13-10
            rd_bin = to_binary(fields['rd'], 4)        # bits 9-6
            binary_representation = padding + rs2_bin + rs1_bin + rd_bin + modtag + task_id
    elif INSTRUCTION_SET[operation]["type"] == "glitch":
        # 'break' instruction: all zeros except modtag and task_id
        padding = '0' * 20
        binary_representation = padding + modtag + task_id
    else:
        return None
    return binary_representation

def binary_to_hex(binary):
    if binary is None:
        return None
    hex_representation = hex(int(binary, 2))[2:].zfill(6)
    return hex_representation.upper()

def main():
    if len(sys.argv) < 2:
        print("Usage: python isa24filetohex.py input_file [output_file]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = None
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]

    # First pass: collect label addresses
    labels = {}
    instructions = []
    address = 0
    inside_block_comment = False
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # Remove inline comments
            instruction = line.split('#', 1)[0].strip()

            # Check for block comment start/end
            if '###' in instruction:
                inside_block_comment = not inside_block_comment
                continue
            if inside_block_comment:
                continue  # Ignore lines within block comments

            if not instruction:
                continue  # Skip empty lines

            if ':' in instruction:
                label, instruction = instruction.split(':', 1)
                label = label.strip()
                instruction = instruction.strip()
                if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', label):
                    print(f"Error: Invalid label '{label}' on line {line_num}.")
                    sys.exit(1)
                labels[label] = address
                if not instruction:
                    continue
            instructions.append((line_num, instruction))
            address += 1

    # Debug: Print label addresses
    print("Label Addresses:")
    for label, addr in labels.items():
        print(f"{label}: {addr}")

    # Second pass: convert instructions to binary and hex
    hex_codes = []
    for idx, (line_num, instruction) in enumerate(instructions):
        parts = instruction.split()
        if not parts:
            continue

        operation = parts[0].lower()
        if operation not in INSTRUCTION_SET:
            print(f"Error: Unknown operation '{operation}' on line {line_num}.")
            continue

        instr_type = INSTRUCTION_SET[operation]["type"]

        # Replace label operands based on instruction type
        for i, part in enumerate(parts[1:], 1):  # Skip operation part
            # Remove any potential commas or parentheses
            clean_part = re.sub(r'[(),]', '', part)
            if clean_part in labels:
                if instr_type == "flow":
                    if operation == "jump":
                        rs1 = parts[2].rstrip(',')[1:]
                        if rs1 == "0":  # Assuming rs1 is x0
                            imm = labels[clean_part] - idx
                        else:
                            # Warning: rs1 is not x0, assembler cannot compute imm
                            print(f"Warning: 'jump' with rs1={rs1} on line {line_num} cannot have imm automatically calculated.")
                            imm = 0  # Default or prompt the user to set imm manually
                        parts[i] = str(imm)
                    elif operation == "pcset":
                        # set_pc uses absolute addressing
                        imm = labels[clean_part]
                        parts[i] = str(imm)
                    else:
                        # Other flow instructions (branches) use relative offsets
                        imm = labels[clean_part] - (idx + 1)
                        parts[i] = str(imm)
                else:
                    # For non-flow instructions, treat as immediate
                    imm = labels[clean_part] - (idx + 1)
                    parts[i] = str(imm)
        instruction = ' '.join(parts)
        operation, rd, rs1, rs2, imm = parse_instruction(instruction)
        if operation is None:
            print(f"Error parsing instruction on line {line_num}: {instruction}")
            continue
        fields = {'rd': rd, 'rs1': rs1, 'rs2': rs2, 'imm': imm}
        binary_representation = convert_to_binary(fields, operation)
        if binary_representation is None:
            print(f"Error converting instruction on line {line_num}: {instruction}")
            continue
        hex_representation = binary_to_hex(binary_representation)
        if hex_representation is None:
            print(f"Error converting binary to hex on line {line_num}: {instruction}")
            continue
        hex_codes.append(hex_representation)

    hex_output = ' '.join(hex_codes)
    print("\nHex Output:")
    print(hex_output)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(hex_output)

if __name__ == "__main__":
    main()
