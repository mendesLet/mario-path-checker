import pandas as pd
import subprocess
import ast
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ROOT_PATH = os.getcwd()

TOKEN_MAPPING = {
    "-": "-",  # Sky
    "o": "o",  # Coin
    "X": "X",  # Ground
    "#": "#",  # Hard Block
    "S": "S",  # Brick
    "C": "C",  # Coin Brick Block
    "U": "U",  # Mushroom Brick Block
    "?": "?",  # Special Question Block
    "!": "Q",  # Coin Question Block
    "1": "1",  # Invisible 1 up block
    "2": "2",  # Invisible coin block
    "g": "g",  # Goomba
    "G": "G",  # Winged Goomba
    "k": "k",  # Green Koopa
    "K": "K",  # Winged Green Koopa
    "r": "r",  # Red Koopa
    "R": "R",  # Winged Red Koopa
    "y": "y",  # Spiky
    "B": "B",  # Bullet Billington head
    "b": "b",  # Bullet Billington body
    "<": "<",  # Top left pipe
    ">": ">",  # Top right pipe
    "(": "T",  # Top left pipe with plant
    ")": "T",  # Top right pipe with plant
    "[": "[",  # Left pipe
    "]": "]",  # Right pipe
    "x": "S",  # Path
    "Y": "Y",  # Black Square
    "N": "-"   # N (mapped to Sky for Mario AI compatibility)
}

def convert_map_tokens(level_data):
    logging.info("Converting map tokens.")
    return [
        "".join(TOKEN_MAPPING.get(char, char) for char in line)
        for line in level_data
    ]


def find_mario_start(map_data):
    """
    Finds the first valid position for Mario (M) in the map.
    Starts from the bottom of the first column and moves up.
    If the first column is all blocks, moves to the next column.
    """
    rows = len(map_data)
    cols = len(map_data[0]) if rows > 0 else 0

    for col in range(cols):  # Iterate through columns
        for row in range(rows - 1, -1, -1):  # Start from the bottom row
            if map_data[row][col] == "-":  # Sky is a valid spot for Mario
                return row, col
    return None  # No valid spot found


def generate_map(map_data, file_name):
    logging.info(f"Generating map file: {file_name}")
    map_dir = os.path.join(ROOT_PATH, "Mario-AI-Framework", "levels", "test")
    os.makedirs(map_dir, exist_ok=True)
    map_path = os.path.join(map_dir, file_name)

    # Process the map data
    map_data = ast.literal_eval(map_data)
    
    # Find a valid start position for Mario
    mario_start = find_mario_start(map_data)
    if mario_start:
        row, col = mario_start
        map_data[row] = map_data[row][:col] + "M" + map_data[row][col + 1:]
        logging.info(f"Mario placed at ({row}, {col}).")
    else:
        logging.warning("No valid position found to place Mario.")

    map_data = convert_map_tokens(map_data)

    # Write the map data to the file
    with open(map_path, 'w') as file:
        file.write("\n".join(map_data) + '\n')
        logging.info(f"Map successfully written to {map_path}.")

    return map_path



def run_mario_ai(map_path):
    """
    Compiles and runs the Mario AI Java program with the specified map file.
    Ensures the correct working directory and handles errors gracefully.
    """
    # Define paths
    java_src_dir = os.path.join(ROOT_PATH, "Mario-AI-Framework", "src")
    base_dir = os.path.join(ROOT_PATH, "Mario-AI-Framework")
    main_class = "PlayLevel"

    try:
        # Ensure base_dir exists
        if not os.path.exists(base_dir):
            logging.error(f"Base directory not found: {base_dir}")
            return None

        # Step 1: Compile the Java program
        compile_command = [
            "javac", "-cp", java_src_dir,
            os.path.join(java_src_dir, "PlayLevel.java")
        ]
        logging.info(f"Compile command: {' '.join(compile_command)}")
        logging.info("Compiling Java files...")

        compile_result = subprocess.run(
            compile_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base_dir  # Compile in the correct directory
        )

        if compile_result.returncode != 0:
            logging.error("Compilation failed:")
            logging.error(compile_result.stderr)
            return None

        logging.info("Compilation successful.")

        # Step 2: Run the Java program
        run_command = [
            "java", "-cp", java_src_dir, main_class, map_path
        ]
        logging.info(f"Run command: {' '.join(run_command)}")
        logging.info("Running the Java program...")

        result = subprocess.run(
            run_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base_dir  # Run in the correct directory
        )

        # Step 3: Handle results
        # logging.info("Java stdout:")
        # logging.info(result.stdout)
        # logging.info("Java stderr:")
        # logging.info(result.stderr)

        if result.returncode != 0:
            logging.error("Java program execution failed.")
            return None

        return result.stdout

    except FileNotFoundError as e:
        logging.error(f"File not found during execution: {e}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return None

def parse_coordinates(output):
    logging.info("Parsing result output from Mario AI.")
    mario_path = []
    path_start = False

    for line in output.splitlines():
        if line.strip() == "Mario Path:":
            path_start = True
            continue
        if path_start:
            if not line.strip():
                break
            coordinates = line.strip("[]").split(", ")
            if len(coordinates) == 2:
                x, y = map(int, coordinates)
                mario_path.append((x, y))
                logging.debug(f"Added path coordinate: ({x}, {y}).")

    return mario_path

def parse_result(output):
    logging.info("Parsing result output from Mario AI.")

    # Check for WIN or LOSE in the output
    if "WIN" in output:
        logging.info("Mario completed the level (WIN detected).")
        return True
    elif "LOSE" in output:
        logging.info("Mario failed the level (LOSE detected).")
        return False
    else:
        logging.warning("No WIN or LOSE detected in the output.")
        return None

def check_level_completion(level_data):
    logging.info("Checking level completion.")
    map_name = "map_temp.txt"
    map_path = generate_map(level_data, map_name)
    
    MAX_ATTEMPTS = 1  # Maximum number of attempts
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logging.info(f"Attempt {attempt} for level.")
        output = run_mario_ai(map_path)

        if output is None:
            logging.warning("Level failed to execute properly.")
        else:
            completion_status = parse_result(output)

            if completion_status:  # WIN detected
                logging.info(f"Level completed successfully on attempt {attempt}.")
                return True
            elif completion_status is False:  # LOSE detected
                logging.info(f"Level failed on attempt {attempt}.")

        # Retry logic: If MAX_ATTEMPTS is reached, break out of the loop
        if attempt == MAX_ATTEMPTS:
            logging.warning(f"Level not completed after {MAX_ATTEMPTS} attempts.")
            return False

    return False

def analyze_levels(csv_path):
    logging.info(f"Analyzing levels from CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    if 'level' not in df.columns:
        logging.error("The CSV file must contain a 'level' column.")
        raise ValueError("The CSV file must contain a 'level' column.")

    completed_count = 0
    total_count = len(df)

    for index, row in df.iterrows():
        level_data = row['level']
        if check_level_completion(level_data):
            completed_count += 1
            logging.info(f"Level {index + 1}/{total_count} completed.")
        else:
            logging.info(f"Level {index + 1}/{total_count} not completed.")

    completion_percentage = (completed_count / total_count) * 100 if total_count > 0 else 0
    logging.info(f"{completed_count}/{total_count} levels completed ({completion_percentage:.2f}%).")
    return completion_percentage

if __name__ == "__main__":
    csv_file_path = "/home/lettuce/code/college/nlp/trabalho_final/tmp/mario-gpt/notebooks/generated_levels.csv"  # Replace with your CSV file path
    analyze_levels(csv_file_path)
