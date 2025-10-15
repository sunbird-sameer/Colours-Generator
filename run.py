import subprocess
import time
import sys
import os

def run_generator_loop():
    """
    Continuously executes generate_colors.py in a loop, pausing 1 second between runs.
    
    It checks the return code of the child process (generate_colors.py) to handle
    errors or detect completion.
    """
    print("--- Starting Continuous Color Image Generation (via Python) ---")
    print("Press Ctrl+C to stop the process.")

    # Define the command to execute the generator script
    # We use sys.executable to ensure the correct Python interpreter is used
    command = [sys.executable, 'generate_colors.py']
    
    # Define the path to the resume file to check for final completion
    resume_file_path = os.path.join("all_rgb_colors", "resume_index.txt")
    
    while True:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"\n--- {timestamp} --- Starting next batch...")
        
        try:
            # Execute the color generation script
            # check=False prevents Python from raising an error if the return code is non-zero
            # The child script will exit with code 0 on success, or non-zero on error.
            result = subprocess.run(command, check=False) 
            
            # Check for errors in the child script
            if result.returncode != 0:
                # The generator is complete when it deletes the resume file.
                if not os.path.exists(resume_file_path):
                    print("Generation appears complete (resume file deleted). Exiting continuous loop.")
                else:
                    print(f"FATAL ERROR: The child process 'generate_colors.py' exited with return code {result.returncode}. Stopping loop.")
                break

            # The generator successfully completed a batch and exited with code 0.
            print("Batch complete. Waiting 1 second before resuming...")
            
            # ADDED: 1-second delay, as requested
            time.sleep(1)

        except FileNotFoundError:
            print(f"ERROR: The file 'generate_colors.py' was not found. Ensure it is in the same directory.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Stopping loop.")
            break

if __name__ == '__main__':
    run_generator_loop()

