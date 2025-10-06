<p align="center">
  <img src="https://img.shields.io/badge/DARE%20Framework-Gemini-blueviolet?style=for-the-badge&logo=google" alt="DARE">
  <img src="https://img.shields.io/badge/Task-Multimodal%20Emotion%20Recognition-ff3366?style=for-the-badge&logo=google-analytics" alt="Task">
  <img src="https://img.shields.io/badge/Status-Research%20Prototype-orange?style=for-the-badge&logo=fluentd" alt="Status">
  <a href="https://doi.org/10.1145/3746270.3760223"><img src="https://img.shields.io/badge/Paper-ACM%20MRAC%2025-0069d9?style=for-the-badge&logo=read-the-docs" alt="Paper DOI"></a>
</p>

<div align="center">
  <h1>DARE to Disagree</h1>
  <h3>A Multi-Agent Adversarial Debate Framework for Open-Vocabulary Multimodal Emotion Recognition</h3>
  <p><strong>Gemini-oriented research code</strong> accompanying the paper <em>DARE to Disagree: A Multi-Agent Adversarial Debate Framework for Open-Vocabulary Multimodal Emotion Recognition</em>.</p>
</div>

> **Heads up:** This repository provides a Gemini debate workflow framework. Bring your own Google AI Studio API keys and request access to the MERChallenge/MER2025 dataset on Hugging Face before running experiments.

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration Checklist](#configuration-checklist)
- [Dataset Preparation](#dataset-preparation)
- [Project Layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)
- [License](#license)

## Overview
DARE (Debate-based Adversarial Reasoning Engine) orchestrates three role-specialized Gemini agents &mdash; a Liberal Analyst, a Conservative Critic, and a Judge-Moderator &mdash; to reason over multimodal clips. Each video is processed through iterative debate rounds, producing an open-set list of emotions grounded in both visual and textual evidence.

## Key Features
- **Gemini-first workflow:** Built around `models/gemini-2.5-flash-latest`, ready to swap for newer Gemini multimodal checkpoints.
- **Structured debate loop:** Role-specific prompts live in `dare_package/prompts.py`, enabling controlled agent behaviors.
- **Parallel processing:** Spawns one worker per API key, complete with retry logic and resumable progress tracking.
- **Workspace sandbox:** Keeps inputs, intermediate artifacts, outputs, and status files under `workspace/` for reproducibility.
- **Config-centric design:** A single configuration file exposes debate depth, failure thresholds, and filesystem paths.

## Architecture
```
+-----------------+      +----------------------+      +------------------+
| Liberal Analyst | ---> | Judge-Moderator Loop | <--- | Conservative Critic |
+-----------------+      +----------------------+      +------------------+
         ^                         |                          ^
         |                         v                          |
         +----------- Gemini API & debate history ------------+
```

- `VideoProcessor` uploads the video, seeds the debate, and synthesizes the final verdict.
- `processing_worker` coordinates multithreaded execution and result persistence.
- Status is checkpointed to `workspace/dare_gemini_status.json` so runs can resume where they stopped.

## Quick Start
1. **Create environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install google-generativeai
   ```
2. **Configure secrets**
   - Open `dare_package/config.py`.
   - Replace all empty strings in `API_KEYS` with your Google Gemini API keys.
3. **Stage data**
   - Request and download [MERChallenge/MER2025](https://huggingface.co/datasets/MERChallenge/MER2025).
   - Place MP4 clips in `workspace/sample_videos/` and transcripts in `workspace/input_data.csv`.
4. **Run the debate pipeline**
   ```bash
   python main.py
   ```
5. **Collect outputs**
   - Predictions: `workspace/dare_output_data.csv`
   - Run log: `workspace/dare_gemini_status.json`

## Configuration Checklist
> Edit `dare_package/config.py` before your first run.

| Setting | Purpose | Default |
| --- | --- | --- |
| `API_KEYS` | Gemini key pool; one worker per entry | `['', '', '', '']` |
| `MAX_DEBATE_ROUNDS` | Debate iterations after initial proposals | `3` |
| `MAX_FAILURES_PER_THREAD` | Consecutive failures before a worker exits | `3` |
| `LLM_MODEL_NAME` | Gemini model identifier | `'models/gemini-2.5-flash-latest'` |
| `INPUT_CSV` | Transcript/task manifest | `workspace/input_data.csv` |
| `OUTPUT_CSV` | Emotion predictions | `workspace/dare_output_data.csv` |
| `STATUS_FILE` | Resume metadata | `workspace/dare_gemini_status.json` |
| `VIDEO_FOLDER` | Video staging directory | `workspace/sample_videos` |

## Dataset Preparation
1. **Request approval** on the MER2025 Hugging Face page and download the assigned assets.
2. **Name alignment:** Ensure every `name` column entry in `workspace/input_data.csv` has a matching `<name>.mp4` in `workspace/sample_videos/`.
3. **Transcript column:** Keep blank if you want video-only reasoning; otherwise provide contextual text.

Example `workspace/input_data.csv`:

```csv
name,transcript
samplenew3_00000004,""
samplenew3_00000005,"Subject describes a tense encounter."
```

## Project Layout
| Path | Description |
| --- | --- |
| `main.py` | Entry point that dispatches the processing workflow. |
| `dare_package/config.py` | Central configuration for keys, debate knobs, and paths. |
| `dare_package/debate_framework.py` | Core debate orchestration and Gemini API calls. |
| `dare_package/processing_worker.py` | Threaded task management and result writing. |
| `dare_package/prompts.py` | Role-specific system prompts for the agent triad. |
| `workspace/` | Data sandbox (videos, CSVs, run metadata). |

## Troubleshooting
- **API authentication errors:** A worker exits immediately if its key is invalid. Confirm every entry in `API_KEYS` is populated with a valid Gemini key.
- **Missing videos:** The loader warns when a CSV entry has no matching `.mp4`. Verify filename casing and extensions.
- **Stalled processing:** If you need a clean rerun, delete `workspace/dare_gemini_status.json` and restart `python main.py`.
- **Rate limits:** Distribute tasks across multiple keys or throttle runs if the API starts returning quota errors.

## Citation
If this framework supports your research, please cite:

```bibtex
@inproceedings{huang2025dare,
  author    = {Yuesheng Huang and Meiqi Feng and Zhenming He and Yueyuan Peng and Jiawen Li},
  title     = {DARE to Disagree: A Multi-Agent Adversarial Debate Framework for Open-Vocabulary Multimodal Emotion Recognition},
  booktitle = {Proceedings of the 3rd International Workshop on Multimodal and Responsible Affective Computing (MRAC '25)},
  year      = {2025},
  address   = {Dublin, Ireland},
  publisher = {ACM},
  pages     = {1--10},
  doi       = {10.1145/3746270.3760223}
}
```
## License
Distributed under the [MIT License](LICENSE).




