"""Pure functions: transcription + LLM QA → dict result"""
import os
import json
import textwrap
import openai
from utils.logger import logger
from prompts import SYSTEM_PROMPTS

openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")

# ---------- helpers ----------

def whisper_transcribe(file_bytes: bytes) -> str:
    """
    Call Whisper API and return full transcript string
    
    Args:
        file_bytes (bytes): Audio file bytes
        
    Returns:
        str: Full transcript text
    """
    resp = openai.audio.transcriptions.create(
        model=WHISPER_MODEL,
        file=("audio.wav", file_bytes, "audio/wav")
    )
    return resp.text


def _chat(system_prompt, user_prompt, *, expect_json=False, temperature=0.0):
    """
    Send a request to OpenAI Chat API
    
    Args:
        system_prompt (str): System prompt for the LLM
        user_prompt (str): User prompt for the LLM
        expect_json (bool, optional): Whether to expect JSON response. Defaults to False.
        temperature (float, optional): Temperature for generation. Defaults to 0.0.
        
    Returns:
        str: LLM response content
    """
    params = dict(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
    )
    if expect_json:
        params["response_format"] = {"type": "json_object"}
    return openai.chat.completions.create(**params).choices[0].message.content.strip()

# ---------- node wrappers ----------

def node_replace(transcript: str) -> str:
    """
    Clean up transcript by removing filler words and improving readability
    
    Args:
        transcript (str): Raw transcript text
        
    Returns:
        str: Cleaned transcript text
    """
    system_prompt = SYSTEM_PROMPTS["replace"]
    return _chat(system_prompt, transcript)


def node_speaker_separation(transcript: str) -> str:
    """
    Separate transcript into speakers (営業担当 and お客様)
    
    Args:
        transcript (str): Transcript text
        
    Returns:
        str: Transcript with speaker labels
    """
    system_prompt = SYSTEM_PROMPTS["speaker"]
    return _chat(system_prompt, transcript)


def node_company_check(transcript: str) -> str:
    """
    Check if company name and call reason were properly introduced
    
    Args:
        transcript (str): Transcript with speaker labels
        
    Returns:
        str: JSON string with company check results
    """
    system_prompt = SYSTEM_PROMPTS["company_check"]
    return _chat(system_prompt, transcript, expect_json=True)


def node_approach_check(transcript: str) -> str:
    """
    Evaluate sales approach quality
    
    Args:
        transcript (str): Transcript with speaker labels
        
    Returns:
        str: JSON string with approach evaluation results
    """
    system_prompt = SYSTEM_PROMPTS["approach_check"]
    return _chat(system_prompt, transcript, expect_json=True)


def node_longcall_check(transcript: str) -> str:
    """
    Analyze if the call was unnecessarily long
    
    Args:
        transcript (str): Transcript with speaker labels
        
    Returns:
        str: JSON string with call length analysis
    """
    system_prompt = SYSTEM_PROMPTS["longcall"]
    return _chat(system_prompt, transcript, expect_json=True)


def node_customer_reaction(transcript: str) -> str:
    """
    Analyze customer engagement and reactions
    
    Args:
        transcript (str): Transcript with speaker labels
        
    Returns:
        str: JSON string with customer reaction analysis
    """
    system_prompt = SYSTEM_PROMPTS["customer_react"]
    return _chat(system_prompt, transcript, expect_json=True)


def node_manner_check(transcript: str) -> str:
    """
    Evaluate sales rep's manner and communication style
    
    Args:
        transcript (str): Transcript with speaker labels
        
    Returns:
        str: JSON string with manner evaluation results
    """
    system_prompt = SYSTEM_PROMPTS["manner"]
    return _chat(system_prompt, transcript, expect_json=True)


def node_to_json(results: dict[str, str]) -> dict:
    """
    Convert all evaluation results to a single JSON object
    
    Args:
        results (dict[str, str]): Dictionary of evaluation results
        
    Returns:
        dict: Combined JSON results
    """
    combined_text = "\n\n".join([f"## {k}\n{v}" for k, v in results.items()])
    json_str = _chat(SYSTEM_PROMPTS["to_json"], combined_text, expect_json=True)
    return json.loads(json_str)

# ---------- public entrypoint ----------

def run_workflow(transcript: str) -> dict:
    """
    Run the full evaluation workflow on a transcript
    
    Args:
        transcript (str): Raw transcript text
        
    Returns:
        dict: Evaluation results as JSON
    """
    logger.info("Starting workflow")
    
    # Preprocessing
    cleaned = node_replace(transcript)
    logger.info("Cleaned transcript")
    
    with_speakers = node_speaker_separation(cleaned)
    logger.info("Added speaker labels")
    
    # Evaluation nodes
    company = node_company_check(with_speakers)
    logger.info("Completed company check")
    
    approach = node_approach_check(with_speakers)
    logger.info("Completed approach check")
    
    longcall = node_longcall_check(with_speakers)
    logger.info("Completed call length analysis")
    
    customer = node_customer_reaction(with_speakers)
    logger.info("Completed customer reaction analysis")
    
    manner = node_manner_check(with_speakers)
    logger.info("Completed manner check")
    
    # Combine results
    results = {
        "自社紹介": company,
        "アプローチ": approach,
        "通話時間": longcall,
        "顧客反応": customer,
        "マナー": manner
    }
    
    final_json = node_to_json(results)
    logger.info("Created final JSON output")
    
    return final_json


def run_pipeline(file_bytes: bytes) -> dict:
    """
    Run the complete pipeline from audio to evaluation results
    
    Args:
        file_bytes (bytes): Audio file bytes
        
    Returns:
        dict: Evaluation results as JSON
    """
    txt = whisper_transcribe(file_bytes)
    logger.info("Whisper done (%d chars)", len(txt))
    result_json = run_workflow(txt)
    return result_json 