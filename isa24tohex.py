import re

# Define the instruction set with specifications for each instruction
INSTRUCTION_SET = {
    # Task ID '11' - Arithmetic Instructions
    "addi": {"task_id": "11", "modtag": "1000", "type": "arithmetic"},
    "add":  {"task_id": "11", "modtag": "0000", "type": "arithmetic"},
    "subi": {"task_id": "11", "modtag": "1001", "type": "arithmetic"},
    "sub":  {"task_id": "11", "modtag": "0001", "type": "arithmetic"},
    "muli": {"task_id": "11", "modtag": "1010", "type": "arithmetic"},
    "mul":  {"task_id": "11", "modtag": "0010", "type": "arithmetic"},
    "divi": {"task_id": "11", "modtag": "1011", "type": "arithmetic"},
    "div":  {"task_id": "11", "modtag": "0011", "type": "arithmetic"},
    # Task ID '01' - Memory Instructions
    "st":    {"task_id": "01", "modtag": "00", "type": "memo"},
    "ld":    {"task_id": "01", "modtag": "01", "type": "memo"},
    "lui":   {"task_id": "01", "modtag": "10", "type": "memo"},
    "ldm":   {"task_id": "01", "modtag": "11", "type": "memo"},
    # Task ID '10' - Flow Instructions
    "beq":    {"task_id": "10", "modtag": "000", "type": "flow"},
    "bne":    {"task_id": "10", "modtag": "001", "type": "flow"},
    "blt":    {"task_id": "10", "modtag": "010", "type": "flow"},
    "bge":    {"task_id": "10", "modtag": "011", "type": "flow"},
    "bgt":    {"task_id": "10", "modtag": "100", "type": "flow"},
    "ble":    {"task_id": "10", "modtag": "101", "type": "flow"},
    "pcset":  {"task_id": "10", "modtag": "110", "type": "flow"},
    "jump":   {"task_id": "10", "modtag": "111", "type": "flow"}
}

def parse_instruction(instruction):
    parts = instruction.strip().split()
    operation = parts[0].lower()
    if operation not in INSTRUCTION_SET:
        return None, None, None, None, None
    instr_type = INSTRUCTION_SET[operation]["type"]
    rd = rs1 = rs2 = imm = '0'  # Initialize all variables to default values

    if instr_type == "memo":
        rd = parts[1].rstrip(',')[1:]    # RD
        rs1 = parts[2].rstrip(',')[1:]   # RS1
        imm = parts[3]                   # IMM
    elif instr_type == "flow":
        if operation == "pcset":
            rs1 = parts[1].rstrip(',')[1:]  # RS1
            imm = parts[2]                  # IMM
        elif operation == "jump":
            rs2 = parts[1].rstrip(',')[1:]  # RS2
            rs1 = parts[2].rstrip(',')[1:]  # RS1
            imm = parts[3]                  # IMM
        else:
            rs1 = parts[1].rstrip(',')[1:]  # RS1
            rs2 = parts[2].rstrip(',')[1:]  # RS2
            imm = parts[3]                  # IMM
    elif instr_type == "arithmetic":
        rd = parts[1].rstrip(',')[1:]      # RD
        rs1 = parts[2].rstrip(',')[1:]     # RS1
        if operation.endswith('i'):
            imm = parts[3]                 # IMM
        else:
            rs2 = parts[3].rstrip(',')[1:] # RS2
    return operation, rd, rs1, rs2, imm

def to_binary(value, bits):
    val = int(value)
    if val < 0:
        val = (1 << bits) + val
    return format(val, f'0{bits}b')

def convert_to_binary(fields, operation):
    task_id = INSTRUCTION_SET[operation]['task_id']    # bits 0-1 (LSB)
    modtag = INSTRUCTION_SET[operation]['modtag']      # bits 2-4

    if INSTRUCTION_SET[operation]["type"] == "memo":
        imm_bin = to_binary(fields['imm'], 12)         # bits 23-12
        rs1_bin = to_binary(fields['rs1'], 4)          # bits 11-8
        rd_bin = to_binary(fields['rd'], 4)            # bits 7-4
        binary_representation = imm_bin + rs1_bin + rd_bin + modtag + task_id
    elif INSTRUCTION_SET[operation]["type"] == "flow":
        if operation == "pcset":
            imm_bin = to_binary(fields['imm'], 12)     # bits 23-12
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 7-4 (bits 5-8)
            padding = '0' * 4                          # bits 11-8
            binary_representation = imm_bin + padding + rs1_bin + modtag + task_id
        elif operation == "jump":
            imm_bin = to_binary(fields['imm'], 11)     # bits 23-13
            rs2_bin = to_binary(fields['rs2'], 4)      # bits 12-9
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 8-5
            binary_representation = imm_bin + rs2_bin + rs1_bin + modtag + task_id
        else:
            imm_bin = to_binary(fields['imm'], 11)     # bits 23-13
            rs2_bin = to_binary(fields['rs2'], 4)      # bits 12-9
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 8-5 (bits 5-8)
            binary_representation = imm_bin + rs2_bin + rs1_bin + modtag + task_id
    else:
        rd_bin = to_binary(fields['rd'], 4)            # bits 17-14
        rs1_bin = to_binary(fields['rs1'], 4)          # bits 13-10
        if operation.endswith('i'):
            imm_bin = to_binary(fields['imm'], 10)     # bits 23-14
            binary_representation = imm_bin + rs1_bin + rd_bin + modtag + task_id
        else:
            padding = '0' * 6                          # bits 23-18
            rs2_bin = to_binary(fields['rs2'], 4)      # bits 17-14
            rs1_bin = to_binary(fields['rs1'], 4)      # bits 13-10
            rd_bin = to_binary(fields['rd'], 4)        # bits 9-6
            binary_representation = padding + rs2_bin + rs1_bin + rd_bin + modtag + task_id
    return binary_representation

def segment_binary(binary, operation):
    segments = []
    if INSTRUCTION_SET[operation]["type"] == "memo":
        segments.append(f"IMM[23-12]: {binary[0:12]}")
        segments.append(f"RS1[11-8]: {binary[12:16]}")
        segments.append(f"RD[7-4]: {binary[16:20]}")
        segments.append(f"MODTAG+TASK_ID[3-0]: {binary[20:24]}")
    elif INSTRUCTION_SET[operation]["type"] == "flow":
        if operation == "pcset":
            segments.append(f"IMM[23-12]: {binary[0:12]}")
            segments.append(f"PADDING[11-8]: {binary[12:16]}")
            segments.append(f"RS1[7-4]: {binary[16:20]}")  # Bits 5-8
            segments.append(f"MODTAG+TASK_ID[3-0]: {binary[20:24]}")
        else:
            segments.append(f"IMM[23-13]: {binary[0:11]}")
            segments.append(f"RS2[12-9]: {binary[11:15]}")
            segments.append(f"RS1[8-5]: {binary[15:19]}")  # Bits 5-8
            segments.append(f"MODTAG+TASK_ID[4-0]: {binary[19:24]}")
    else:
        if operation.endswith('i'):
            segments.append(f"IMM[23-14]: {binary[0:10]}")
            segments.append(f"RS1[13-10]: {binary[10:14]}")
            segments.append(f"RD[9-6]: {binary[14:18]}")
            segments.append(f"MODTAG+TASK_ID[5-0]: {binary[18:24]}")
        else:
            segments.append(f"PADDING[23-18]: {binary[0:6]}")
            segments.append(f"RS2[17-14]: {binary[6:10]}")
            segments.append(f"RS1[13-10]: {binary[10:14]}")
            segments.append(f"RD[9-6]: {binary[14:18]}")
            segments.append(f"MODTAG+TASK_ID[5-0]: {binary[18:24]}")
    return segments

def binary_to_hex(binary):
    hex_representation = hex(int(binary, 2))[2:].zfill(6)
    return hex_representation.upper()

# Main program
instruction = input("Enter an instruction (e.g., pcset x1, 7): ")
operation, rd, rs1, rs2, imm = parse_instruction(instruction)
if operation is None:
    print("Invalid instruction format.")
else:
    fields = {'rd': rd, 'rs1': rs1, 'rs2': rs2, 'imm': imm}
    binary_representation = convert_to_binary(fields, operation)
    segmented_binary = segment_binary(binary_representation, operation)
    hex_representation = binary_to_hex(binary_representation)

    # Output the results
    print(f"Complete Binary (24 bits): {binary_representation}")
    print("Segmented Binary:")
    for segment in segmented_binary:
        print(segment)
    print(f"Hexadecimal: {hex_representation}")
