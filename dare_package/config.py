# dare_analyzer/config.py
import os

# --- 1. Critical Configuration ---
# IMPORTANT: Please fill in your API keys here.
API_KEYS = [
    '',
    '',
    '',
    ''
]


# --- 2. Debate & Model Settings ---
MAX_DEBATE_ROUNDS = 3
MAX_FAILURES_PER_THREAD = 3  # Maximum consecutive failures per thread
LLM_MODEL_NAME = 'models/gemini-2.5-flash-latest' # It is recommended to use the latest flash model for speed and cost advantages


# --- 3. File Path Settings ---
# Use relative paths to make the project more portable
# All data files are placed in the 'workspace' folder under the project root directory
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workspace'))

VIDEO_FOLDER = os.path.join(WORKSPACE_DIR, "sample_videos")
# The input CSV should contain 'name' and 'transcript' columns
INPUT_CSV = os.path.join(WORKSPACE_DIR, "input_data.csv")
OUTPUT_CSV = os.path.join(WORKSPACE_DIR, "dare_output_data.csv")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "dare_gemini_status.json")

os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)