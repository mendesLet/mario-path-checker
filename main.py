import subprocess
import os

ROOT_PATH = os.getcwd()

# Example: Generate a simple map and save it to a .txt file
def generate_map(map_data, file_name):
    
    map_dir = os.path.join(ROOT_PATH, "Mario-AI-Framework", "levels", "test")
    os.makedirs(map_dir, exist_ok=True)
    map_path = os.path.join(map_dir, file_name)
    
    map_data = map_data.replace("P", 't')
    map_data = map_data.replace("x", 'S')
    
    with open(map_path, 'w') as file:
        file.write(map_data)

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
            print(f"Error: Base directory not found: {base_dir}")
            return None

        # Step 1: Compile the Java program
        compile_command = [
            "javac", "-cp", java_src_dir,
            os.path.join(java_src_dir, "PlayLevel.java")
        ]
        print(f"Compile command: {' '.join(compile_command)}")
        print("Compiling Java files...")

        compile_result = subprocess.run(
            compile_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base_dir  # Compile in the correct directory
        )

        if compile_result.returncode != 0:
            print("Compilation failed:")
            print(compile_result.stderr)
            return None

        print("Compilation successful.")

        # Step 2: Run the Java program
        run_command = [
            "java", "-cp", java_src_dir, main_class, map_path
        ]
        print(f"Run command: {' '.join(run_command)}")
        print("Running the Java program...")

        result = subprocess.run(
            run_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base_dir  # Run in the correct directory
        )

        # Step 3: Handle results
        print("Java stdout:")
        print(result.stdout)
        print("Java stderr:")
        print(result.stderr)

        if result.returncode != 0:
            print("Java program execution failed.")
            return None

        return result.stdout

    except FileNotFoundError as e:
        print(f"Error: File not found during execution - {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def parse_result(output):
    """
    Parse the Mario game result output and extract the Mario path as a list.

    Args:
        output (str): The raw output string from the Mario game.

    Returns:
        list: A list of tuples representing the Mario path.
    """
    mario_path = []
    path_start = False

    for line in output.splitlines():
        # Check if the path section has started
        if line.strip() == "Mario Path:":
            path_start = True
            continue
        if path_start:
            # If the line is empty, we've reached the end of the path section
            if not line.strip():
                break
            # Parse the path coordinates
            coordinates = line.strip("[]").split(", ")
            if len(coordinates) == 2:
                x, y = map(int, coordinates)
                mario_path.append((x, y))
    
    return mario_path

def mario_pipeline():
    # Step 1: Generate the map
    map_data = """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
--------------------------------ooooR---------------------ooo----------R------------------------------------------------------------------------------------------------------------------------------
----------------------oo-------xxxx?x---------------------ooo-----------------------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------xxx-----------------------------x?xxxxx------------------------------------------R--------------------------------------##------------------
------------------??--PP--------------------------------R-------xxxxxx----xxx---##-----------------------------------------------------------------------------------------------###------------------
--------------oo------PP--------------------------------------------------------###----------?--------B###---------------------xxxx------------xxxx------xxxx-------------------####------------------
--------x?x-----------PP----PP---PP----PP------------R-------------xoook--------####------xxxxx?x-----B--------------------------------xxxx------------------------------------#####------------------
--------------PP------PP----PP-g-PP-k-gPP--Roo-S----xxx------------xxxxx--------#####----------------BB?-------PP------xxxx-------------------------------------PP--xx?x------######------------------
--------------PP--XX--PP--XXXXXXXPPXXXXPPXXXX####-------------------------------######---------------BB--------PP-----------------------------------------------PP-----------#######------------------
--------------PP--XX--PP--XXXXXXXPPXXXXPPXXXX####-----------xxxx-------R--------#######--------?-----BB----g-G-PP-----------------------------------------------PP--gg------########------------------
XXXXXXXXXXXX--PP--XX--PP--XXXXXXXXXXXXXPPXXXX##-----------------------xxxx------XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX-------------------------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXX--PP--XX--PP--XXXXXXXXXXXXXXXXXXX##---------------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX-------------------------------------------XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"""

    map_name = "map.txt"
    map_path = generate_map(map_data, map_name)
    print(map_path)
    
    # Step 2: Run the Java program
    output = run_mario_ai(map_path)
    if output is None:
        print("Error: Could not run the Java program.")
        return
    
    # Step 3: Parse the result
    coordinates = parse_result(output)
    # Split the map into a list of lines
    map_lines = map_data.splitlines()

    # Convert each line into a mutable list of characters
    map_grid = [list(line) for line in map_lines]

    # Place "m" at the specified (x, y) coordinates
    for x, y in coordinates:
        if 0 <= y < len(map_grid) and 0 <= x < len(map_grid[y]):  # Ensure coordinates are within bounds
            map_grid[y][x] = "m"  # Use y for the row and x for the column

    # Convert the modified grid back to a single string
    modified_map = "\n".join("".join(line) for line in map_grid)

    print(modified_map)
    return modified_map

if __name__ == "__main__":
    mario_pipeline()