import os
import time
import tempfile
import shutil

def generate_large_log(filepath, size_mb=50):
    """Generates a log file of approximately size_mb MB."""
    print(f"Generating {size_mb}MB log file at {filepath}...")
    start_gen = time.time()
    with open(filepath, 'w', encoding='utf-8') as f:
        # standard line approx 100 bytes
        line = "2023-10-27 10:00:00 - systems_engineer - INFO - This is a standard log line that takes up some space to simulate a real log file content.\n"
        chunk = line * 1000 # ~100KB
        target_size = size_mb * 1024 * 1024
        current_size = 0
        while current_size < target_size:
            f.write(chunk)
            current_size += len(chunk)

        # Add some errors at the end
        for i in range(10):
            f.write(f"2023-10-27 10:05:00 - systems_engineer - ERROR - Critical failure {i}\n")
    print(f"Generation took {time.time() - start_gen:.2f}s")

def original_read_last_lines(filepath, n=50):
    start = time.time()
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()[-n:]
    duration = time.time() - start
    return lines, duration

def optimized_read_last_lines(filepath, n=50):
    """Reads the last n lines of a file efficiently."""
    start = time.time()

    lines = []
    if not os.path.exists(filepath):
        return [], 0

    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return [], time.time() - start

    block_size = 4096
    with open(filepath, 'rb') as f:
        # Case 1: File is smaller than block size
        if file_size <= block_size:
            f.seek(0)
            content = f.read()
            # Decode and split
            try:
                decoded = content.decode('utf-8', errors='ignore')
            except:
                decoded = ""
            lines = decoded.splitlines(keepends=True)[-n:]
            return lines, time.time() - start

        # Case 2: File is larger, seek from end
        f.seek(0, os.SEEK_END)
        file_end = f.tell()
        current_pos = file_end
        blocks = []

        while current_pos > 0 and len(blocks) * (block_size / 100) < n * 2: # Rough heuristic, check line count later
            step = min(block_size, current_pos)
            current_pos -= step
            f.seek(current_pos)
            chunk = f.read(step)
            blocks.append(chunk)

            # Quick check if we have enough newlines
            # This is an optimization to avoid reading too much
            # Join reversed blocks to check
            # (But careful with multibyte chars split across blocks, though utf-8 self-synchronizes mostly)

            # Simple approach: Read enough blocks until we are sure we have N lines
            # Count newlines in current chunk
            if chunk.count(b'\n') >= n:
                 break

            # If we collected a lot of data, maybe check properly
            total_data = b"".join(reversed(blocks))
            if total_data.count(b'\n') >= n:
                break

        # Process the collected bytes
        total_data = b"".join(reversed(blocks))

        try:
            text = total_data.decode('utf-8', errors='ignore')
        except:
            text = ""

        lines = text.splitlines(keepends=True)
        if len(lines) > n:
            lines = lines[-n:]

    duration = time.time() - start
    return lines, duration


def main():
    temp_dir = tempfile.mkdtemp()
    try:
        log_file = os.path.join(temp_dir, "test.log")

        # 1. Generate Log
        generate_large_log(log_file, size_mb=100) # 100MB to be noticeable

        # 2. Test Original
        print("\nTesting Original Method...")
        lines_orig, time_orig = original_read_last_lines(log_file, 50)
        print(f"Original Time: {time_orig:.6f}s")
        print(f"Lines Read: {len(lines_orig)}")
        print(f"Last Line: {lines_orig[-1].strip()}")

        # 3. Test Optimized
        print("\nTesting Optimized Method...")
        lines_opt, time_opt = optimized_read_last_lines(log_file, 50)
        print(f"Optimized Time: {time_opt:.6f}s")
        print(f"Lines Read: {len(lines_opt)}")
        print(f"Last Line: {lines_opt[-1].strip()}")

        # 4. Compare
        print(f"\nSpeedup: {time_orig / time_opt:.2f}x")

        # Correctness check
        if lines_orig == lines_opt:
            print("✅ Output matches exactly.")
        else:
            print("❌ Output differs!")
            # Debugging
            print(f"Orig first: {lines_orig[0].strip()}")
            print(f"Opt first:  {lines_opt[0].strip()}")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
