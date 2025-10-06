# dare_analyzer/concurrent_processing.py

import os
import csv
import time
import json
import queue
import threading
from datetime import datetime
from typing import List, Dict

# Import configurations and other modules from the package
from . import config
from .debate_framework import VideoProcessor

# --- Thread-safe settings ---
csv_lock = threading.Lock()
status_lock = threading.Lock()
task_queue = queue.Queue()


def get_video_tasks() -> List[Dict[str, str]]:
    """Load tasks from the input CSV and skip already processed files."""
    if not os.path.exists(config.INPUT_CSV):
        print(
            f"❌ Error: Input file '{config.INPUT_CSV}' not found. Please create it in the 'workspace' folder with 'name' and 'transcript' columns.")
        return []

    processed = set()
    if os.path.exists(config.STATUS_FILE):
        try:
            with open(config.STATUS_FILE, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                processed = {name for name, data in status_data.items() if data.get('processed')}
        except (json.JSONDecodeError, IOError):
            print(f"⚠️ Warning: Unable to read status file '{config.STATUS_FILE}'. All tasks will be processed.")
            pass

    tasks = []
    total_rows = 0
    try:
        with open(config.INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                name = row.get('name', '').strip()
                transcript = row.get('transcript', '').strip()
                if not name:
                    continue

                if name not in processed:
                    video_path = os.path.join(config.VIDEO_FOLDER, f"{name}.mp4")
                    if os.path.exists(video_path):
                        tasks.append({'name': name, 'path': video_path, 'transcript': transcript})
                    else:
                        print(f"⚠️ Warning: Video file '{name}' not found at path: '{video_path}'. Skipped.")
    except FileNotFoundError:
        print(f"❌ Error: Input file '{config.INPUT_CSV}' not found.")
        return []

    print("\n📊 Task Summary:")
    print(f"   Total records in input CSV: {total_rows}")
    print(f"   Number of processed tasks: {len(processed)}")
    print(f"   Number of new tasks to process: {len(tasks)}")
    return tasks


def write_result(filename: str, result: str, processor_id: str):
    """Thread-safe method to write results to CSV and update the status file."""
    with csv_lock:
        file_exists = os.path.exists(config.OUTPUT_CSV)
        with open(config.OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'openset'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({'name': filename, 'openset': result})

    with status_lock:
        status_data = {}
        if os.path.exists(config.STATUS_FILE):
            try:
                with open(config.STATUS_FILE, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        status_data[filename] = {'processed': True, 'timestamp': datetime.now().isoformat(), 'processor': processor_id}
        with open(config.STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)


def worker_thread_task(api_key: str, thread_id: int):
    """The work function executed by each thread. It loops to fetch tasks from the queue and process them."""
    processor_id = f"Processor-{thread_id}"
    try:
        processor = VideoProcessor(api_key, processor_id)
    except Exception as e:
        print(f"❌ [{processor_id}] Initialization failed: {e}. Please check the API key. This thread will exit.")
        return

    failure_count = 0
    is_active = True

    while is_active:
        try:
            task_info = task_queue.get(timeout=1)
        except queue.Empty:
            is_active = False
            continue

        filename = task_info['name']
        print(f"🎬 [{processor_id}] Starting processing: {filename}")
        start_time = time.time()

        try:
            final_result = processor.run_debate_for_video(task_info['path'], task_info['transcript'])
            write_result(filename, final_result, processor_id)
            process_time = time.time() - start_time
            print(f"✅ [{processor_id}] Completed: {filename}, Time taken: {process_time:.1f}s. Result: {final_result}")
            failure_count = 0
        except Exception as e:
            failure_count += 1
            print(f"❌ [{processor_id}] Critical error while processing {filename}: {e}")
            task_queue.put(task_info)

            if failure_count >= config.MAX_FAILURES_PER_THREAD:
                print(f"⚠️ [{processor_id}] Maximum failure count reached. This processor will stop.")
                is_active = False
        finally:
            task_queue.task_done()


def run_processing():
    """Main function responsible for starting and managing the entire processing workflow."""
    if not any(config.API_KEYS) or 'YOUR_GEMINI_API_KEY' in config.API_KEYS[0]:
        print("❌ Error: API_KEYS list is empty or not configured. Please provide your Google Gemini API keys in 'dare_analyzer/config.py'.")
        return

    tasks = get_video_tasks()
    if not tasks:
        print("✨ All tasks are completed or no new tasks available!")
        return

    for task in tasks:
        task_queue.put(task)

    threads = []
    num_threads = len(config.API_KEYS)
    print(f"\n🚀 Launching {num_threads} processors...")

    for i, api_key in enumerate(config.API_KEYS):
        thread = threading.Thread(target=worker_thread_task, args=(api_key, i + 1))
        threads.append(thread)
        thread.start()

    task_queue.join()

    for thread in threads:
        thread.join()

    print("\n" + "=" * 50 + "\n✨ All tasks processed successfully!\n" + "=" * 50)