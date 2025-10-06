# dare_analyzer/debate_framework.py

import os
from typing import List
import google.generativeai as genai

# Import configurations and prompts from the package
from . import config
from . import prompts


class VideoProcessor:
    """
    Responsible for executing the complete DARE debate process for a single video.
    This class handles the core API calls and debate logic.
    """

    def __init__(self, api_key: str, processor_id: str):
        """
        Initialize a video processor instance.
        :param api_key: Google Gemini API key for this instance.
        :param processor_id: Unique ID identifying this processor (e.g., "Processor-1").
        """
        genai.configure(api_key=api_key)
        # Fix: Use genai.GenerativeModel for type hinting and instantiation
        self.client: genai.GenerativeModel = genai.GenerativeModel(
            model_name=config.LLM_MODEL_NAME,
            generation_config={"temperature": 0.1},
        )
        self.processor_id = processor_id

    def _call_gemini_api(self, system_prompt: str, parts: List) -> List[str]:
        """An internal method encapsulated for calling the Gemini API."""
        # Fix: Use genai.GenerativeModel to create a session with a specific system prompt
        model_with_prompt = genai.GenerativeModel(
            model_name=config.LLM_MODEL_NAME,
            generation_config={"temperature": 0.1},
            system_instruction=system_prompt
        )
        response = model_with_prompt.generate_content(parts)
        content = response.text.strip()
        emotion_list = [label.strip() for label in content.split(',') if label.strip()]
        return emotion_list

    def run_debate_for_video(self, video_path: str, transcript: str) -> str:
        """Execute the complete DARE framework debate process for a single video."""
        print(f"-> [{self.processor_id}] Starting debate for {os.path.basename(video_path)}...")
        debate_log = []
        video_file = None

        try:
            # Prepare the initial multimodal input
            # print(f"   [{self.processor_id}] Uploading video: {video_path}...")
            video_file = genai.upload_file(path=video_path)
            # print(f"   [{self.processor_id}] Video uploaded successfully: {video_file.name}")
            initial_parts = [video_file, f"Transcript: {transcript}"]
            debate_log.append(f"CONTEXT:\nTranscript: {transcript}\n")

            # --- Round 1: Initial Proposals ---
            print(f"   [{self.processor_id}] Round 1: Fetching initial proposals...")
            la_proposal = self._call_gemini_api(prompts.LA_SYSTEM_PROMPT, initial_parts)
            cc_proposal = self._call_gemini_api(prompts.CC_SYSTEM_PROMPT, initial_parts)
            if not la_proposal or not cc_proposal:
                raise RuntimeError("Failed to fetch initial proposals.")
            debate_log.append(f"Round 1:\n- LA Proposal: {la_proposal}\n- CC Proposal: {cc_proposal}\n")

            # --- Iterative Debate Rounds ---
            for i in range(2, config.MAX_DEBATE_ROUNDS + 1):
                print(f"   [{self.processor_id}] Round {i}: Cross-examination...")
                history_str = "\n".join(debate_log)

                jm_query_to_la = f"DEBATE HISTORY SO FAR:\n{history_str}\n\nYOUR TASK: The Conservative Critic proposed a precise list: {cc_proposal}. Justify your broader proposal: {la_proposal} based on the evidence."
                jm_query_to_cc = f"DEBATE HISTORY SO FAR:\n{history_str}\n\nYOUR TASK: The Liberal Analyst proposed a broad list: {la_proposal}. Does your conservative list: {cc_proposal} miss any complexity? Defend your position."

                la_proposal = self._call_gemini_api(prompts.LA_SYSTEM_PROMPT, [jm_query_to_la])
                cc_proposal = self._call_gemini_api(prompts.CC_SYSTEM_PROMPT, [jm_query_to_cc])

                if not la_proposal or not cc_proposal:
                    raise RuntimeError(f"Failed to fetch proposals in Round {i}.")
                debate_log.append(f"Round {i}:\n- LA Revised: {la_proposal}\n- CC Revised: {cc_proposal}\n")

            # --- Final Verdict ---
            print(f"   [{self.processor_id}] Synthesizing final verdict...")
            final_history = "\n".join(debate_log)
            jm_final_prompt = f"Based on your role as Judge-Moderator, synthesize a final verdict from the following complete debate history.\n\n[START DEBATE HISTORY]\n{final_history}[END DEBATE HISTORY]\n\nSynthesize the final verdict now."

            final_verdict_list = self._call_gemini_api(prompts.JM_SYSTEM_PROMPT, [jm_final_prompt])
            if not final_verdict_list:
                raise RuntimeError("Failed to fetch the final verdict.")

            return ", ".join(final_verdict_list)

        finally:
            # Ensure temporary uploaded files are deleted
            if video_file:
                # print(f"   [{self.processor_id}] Cleaning up temporary file: {video_file.name}...")
                genai.delete_file(video_file.name)
                # print(f"   [{self.processor_id}] Temporary file cleaned up.")