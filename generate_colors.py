import os
import time
from PIL import Image
import sys 
import zipfile # New import for compression
import shutil  # New import for directory deletion

# --- Configuration ---
# The top-level directory where all R folders will be saved.
OUTPUT_DIR = "all_rgb_colors"
# File to store the last successfully completed index for resuming.
RESUME_FILE = os.path.join(OUTPUT_DIR, "resume_index.txt")

# Setting the range (0 to 255 inclusive).
COLOR_RANGE = 256
# Total images = 256 * 256 * 256 = 16,777,216

# IMAGE RESOLUTION: 256x256 pixels
IMAGE_SIZE = (256, 256)

# BATCH CONFIGURATION for I/O Optimization
# Set to 2048 images for frequent checkpoints.
BATCH_SIZE = 2048
# The hard start parameter has been removed. The program now relies entirely on resume_index.txt.


def index_to_rgb(index: int) -> tuple[int, int, int]:
    """Converts a linear index (0 to 16777215) back into (R, G, B) tuple."""
    r_multiplier = COLOR_RANGE ** 2
    g_multiplier = COLOR_RANGE

    r = index // r_multiplier
    g = (index % r_multiplier) // g_multiplier
    b = index % g_multiplier
    return r, g, b

def save_resume_index(index: int):
    """Writes the last completed linear index to the resume file."""
    try:
        # Write the index of the last *completed* image
        with open(RESUME_FILE, 'w') as f:
            f.write(str(index))
    except Exception as e:
        print(f"Error saving resume index: {e}")

def load_resume_index() -> int:
    """Reads the last completed linear index from the resume file."""
    if not os.path.exists(RESUME_FILE):
        return 0 # Start from the beginning

    try:
        with open(RESUME_FILE, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                # Resume at the index *after* the last one successfully saved
                return int(content) + 1 
            return 0
    except Exception as e:
        print(f"Error loading resume index: {e}. Starting from index 0.")
        return 0

def zip_and_delete_folder(folder_path: str, r_dir: str):
    """Zips the specified R-folder and deletes the original folder."""
    zip_filename = f"{r_dir}.zip"
    zip_filepath = os.path.join(os.path.dirname(folder_path), zip_filename)
    
    print(f"\n--- ZIPPING folder '{r_dir}' to '{zip_filepath}' ---")
    
    try:
        # Create the zip archive
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # os.walk walks down the directory tree
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Create an archive name relative to the parent directory (e.g., 008/000/000.png)
                    archive_name = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zipf.write(file_path, archive_name)
        
        print(f"Successfully zipped folder '{r_dir}'. Deleting original directory...")
        
        # Delete the original R-folder
        shutil.rmtree(folder_path)
        print(f"Deleted original directory: '{folder_path}'")
        
    except Exception as e:
        print(f"CRITICAL ERROR during zip/delete of folder '{r_dir}': {e}")
        # Halt execution to prevent data loss if zipping fails
        sys.exit(1)


def flush_images(image_buffer: dict, output_dir: str, current_total_count: int, max_total: int):
    """
    Saves all images currently held in the buffer to disk, creates nested
    directories, and clears the buffer. Writes the resume index on successful completion.
    """
    if not image_buffer:
        return
        
    start_flush = time.time()
    batch_size = len(image_buffer) 
    
    # Track the last index successfully saved in this batch
    last_completed_index = 0
    
    # Perform the burst of I/O operations
    for index, data in image_buffer.items():
        r, g, b = data['r'], data['g'], data['b']
        img = data['img']
        
        # 1. Define the nested directory path: OUTPUT_DIR/RRR/GGG/
        r_dir = f"{r:03d}"
        g_dir = f"{g:03d}"
        dir_path = os.path.join(output_dir, r_dir, g_dir)
        
        # 2. Ensure the full R/G directory structure exists (recursive mkdir)
        os.makedirs(dir_path, exist_ok=True)
        
        # 3. Define the filename and full path: RRR_GGG_BBB.png
        filename = f"{r:03d}_{g:03d}_{b:03d}.png"
        filepath = os.path.join(dir_path, filename)
        
        # 4. Save the image
        img.save(filepath, format='PNG')
        
        last_completed_index = index

    # Clear the buffer to free up memory for the next batch
    image_buffer.clear()
    
    # --- RESUME SAFETY: Only save index if the entire file write loop completed successfully ---
    if last_completed_index > 0:
        save_resume_index(last_completed_index)

    end_flush = time.time()
    current_count = last_completed_index + 1 
    print(f"\nFlushed batch of {batch_size:,} images (Total saved: {current_count:,} / {max_total:,}) in {end_flush - start_flush:.2f} seconds.")


def create_color_images(limit=COLOR_RANGE):
    """
    Generates a 256x256 pixel PNG image for every RGB combination,
    using a memory buffer and nested folders, with zip-and-delete cleanup.
    """
    if limit > COLOR_RANGE:
        limit = COLOR_RANGE

    total_images_to_generate = limit ** 3
    
    # Load the index of the image *next* to be generated (starts at 0 if no resume file exists)
    start_index = load_resume_index() 
    
    r_start, g_start, b_start = index_to_rgb(start_index)
    
    print(f"--- Starting image generation up to R, G, B = {limit-1} ---")
    print(f"Resolution: {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]}. Batch Size: {BATCH_SIZE} files.")
    print(f"Total images to generate: {total_images_to_generate:,}")
    
    if start_index > 0:
        print(f"--- Resuming from index {start_index:,} (Color: R={r_start}, G={g_start}, B={b_start}) ---")
        
    # 1. Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: '{OUTPUT_DIR}'")

    start_time = time.time()
    image_buffer = {} # Dictionary to store image metadata and objects

    # 2. Iterate through all remaining indices
    for current_index in range(start_index, total_images_to_generate):
        r, g, b = index_to_rgb(current_index)
        color = (r, g, b)

        try:
            # Create the image in memory
            img = Image.new('RGB', IMAGE_SIZE, color)
            
            # Store the image and metadata in the buffer, keyed by its linear index
            image_buffer[current_index] = {'r': r, 'g': g, 'b': b, 'img': img}
            
            # Check if the buffer is full (batch size reached)
            if len(image_buffer) >= BATCH_SIZE:
                
                # Write all buffered images to disk in one go and update resume file
                flush_images(image_buffer, OUTPUT_DIR, current_index + 1, total_images_to_generate)

                # --- CLEANUP LOGIC: Check if an R-folder was just completed ---
                
                # last_saved_index is the last index written and checkpointed
                last_saved_index = load_resume_index() - 1 
                
                # Check if the next index to be generated is exactly the start of a new R folder.
                # If (last_saved_index + 1) is exactly divisible by 256*256, the previous R folder is complete.
                if (last_saved_index + 1) % (COLOR_RANGE**2) == 0:
                    r_completed = index_to_rgb(last_saved_index)[0]
                    
                    r_dir_to_zip = f"{r_completed:03d}"
                    folder_to_zip_path = os.path.join(OUTPUT_DIR, r_dir_to_zip)
                    
                    # Only zip and delete if the folder actually exists
                    if os.path.exists(folder_to_zip_path):
                        zip_and_delete_folder(folder_to_zip_path, r_dir_to_zip)


                # Provide progress feedback after a successful flush
                elapsed = time.time() - start_time
                avg_rate = (current_index + 1 - start_index) / elapsed
                remaining_time_sec = (total_images_to_generate - (current_index + 1)) / avg_rate if avg_rate > 0 else 0
                
                hours = int(remaining_time_sec // 3600)
                minutes = int((remaining_time_sec % 3600) // 60)
                
                print(f"Overall Progress: {current_index + 1:,} total images saved. Rate: {avg_rate:.2f} img/s. Estimated time remaining: {hours}h {minutes}m.")
                
                # --- Self-Kill for automatic restart/resumption after batch completion ---
                print("\n--- Batch completed and index saved. Triggering self-exit for controlled resumption ---")
                sys.exit(0)


        except Exception as e:
            print(f"Fatal Error processing image {r},{g},{b} (Index {current_index}): {e}")
            # Attempt to flush what was generated before exiting on error
            flush_images(image_buffer, OUTPUT_DIR, current_index, total_images_to_generate)
            # Exit with an error code so the run script can potentially detect it
            sys.exit(1) 

    # 3. Flush any remaining images after the loops finish
    if image_buffer:
        flush_images(image_buffer, OUTPUT_DIR, total_images_to_generate, total_images_to_generate)
        
    # --- Final Cleanup of the last R-folder ---
    # The last folder might not have triggered the zip/delete if the job completed
    # exactly at the total image count boundary.
    last_r_index = limit - 1
    r_dir_to_zip = f"{last_r_index:03d}"
    folder_to_zip_path = os.path.join(OUTPUT_DIR, r_dir_to_zip)
    if os.path.exists(folder_to_zip_path):
        zip_and_delete_folder(folder_to_zip_path, r_dir_to_zip)
            
    # Clean up the resume file since the job is complete
    if os.path.exists(RESUME_FILE):
        os.remove(RESUME_FILE)

    end_time = time.time()
    duration = end_time - start_time

    print("\n--- Generation Complete ---")
    print(f"Total images saved: {total_images_to_generate:,}")
    print(f"Time taken (for this run): {duration:.2f} seconds")


if __name__ == '__main__':
    # Run the full process (0 to 255 = 16,777,216 files)
    # The program will now start at index 0 or the index saved in resume_index.txt.
    create_color_images(limit=COLOR_RANGE)

