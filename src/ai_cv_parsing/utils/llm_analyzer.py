from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVExtractedFields(BaseModel):
    """Pydantic model for structured CV data extraction"""
    years_of_employment: List[int] = Field(description="List of years of employment")
    skills: List[str] = Field(description="List of skills")
    languages: List[str] = Field(description="List of languages spoken")


def parse_json_response(text: str) -> dict:
    """
    Multi-level JSON parsing strategy with fallback handling.
    
    Args:
        text: Raw LLM output text
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If all parsing attempts fail
    """
    # Level 1: Try direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.debug("Direct JSON parsing failed, trying extraction")

    # Level 2: Extract JSON substring using boundary detection (greedy)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            json_str = json_match.group().strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON extraction from text failed: {e}")
            logger.debug(f"Attempted to parse: {json_str[:100]}...")

    # Level 3: Try to find JSON between specific markers
    for pattern in [r'```json\s*(\{.*?\})\s*```', r'```\s*(\{.*?\})\s*```']:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                json_str = match.group(1).strip()
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    # Level 4: Raise exception
    raise ValueError(f"Unable to parse JSON from LLM response: {text[:200]}...")


def get_llm(
    model: str = "qwen3:4b",
    temperature: float = 0.2,
    max_tokens: int = 2048,
    seed: int = 42
) -> ChatOpenAI:
    """
    Initialize LLM model via Ollama OpenAI compatibility layer.
    
    Args:
        model: Model name (default: qwen3:4b)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        seed: Random seed for reproducible outputs
    
    Returns:
        Configured ChatOpenAI instance
    """
    import os
    logger.info(f"[LOOP-DEBUG] Initializing LLM with model: {model}")
    
    # Support both local and Kubernetes deployment
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
    
    params = {
        "base_url": ollama_base_url,
        "api_key": "ollama",
        "model": model,
        "temperature": temperature,
        "seed": seed
    }
    
    if max_tokens:
        params["max_tokens"] = max_tokens
    
    logger.info(f"[LOOP-DEBUG] LLM initialization completed with base_url: {ollama_base_url}")
    return ChatOpenAI(**params)



def extract_structured_cv_data(text: str) -> dict:
    """
    Extract structured CV data using LangChain with robust JSON output.
    
    Args:
        text: Extracted text from CV/PDF
    
    Returns:
        Validated CVExtractedFields as dictionary
        
    Raises:
        ValueError: If extraction or validation fails
    """
    logger.info("[LOOP-DEBUG] Starting structured CV data extraction")
    llm = get_llm(model="qwen3:4b")
    
    # Create complete prompt optimized for Qwen3
    complete_prompt = f"""user:
# Qwen3 4B CV Extraction Prompt

**Instruction**: Extract structured CV data into strict JSON.

### Years of Employment
- Expand all **explicit numeric date ranges** into full years.
  - Example: `2015-2017 → [2015, 2016, 2017]`
  - Example: `2022 → [2022]`
- Concat all extracted years of employment into one **flat list**.

### Skills
- Identify the "Skills" section.
- Each skill must be a separate string.

### Languages
- Extract language names only.
- Return as a flat list of strings.

### Output
- Return ONLY valid JSON, no additional text.

CV Text to process:

{text}

A:
{{
  "years_of_employment": [list of years],
  "skills": [list of skills],
  "languages": [list of languages]
}}"""
    
    try:
        # Primary approach: Try with_structured_output for compatible models
        logger.info("[LOOP-DEBUG] Attempting structured output with Pydantic schema")
        structured_llm = llm.with_structured_output(CVExtractedFields)
        result = structured_llm.invoke(complete_prompt)
        logger.info("[LOOP-DEBUG] Structured output succeeded")
        return result.model_dump()
        
    except Exception as e:
        logger.warning(f"[LOOP-DEBUG] Structured output failed: {e}, falling back to JSON parsing")
        
        # Fallback approach: Use JsonOutputParser
        try:
            from langchain_core.output_parsers import JsonOutputParser
            parser = JsonOutputParser(pydantic_object=CVExtractedFields)
            # Direct invocation with complete prompt
            response = llm.invoke(complete_prompt)
            result = parser.parse(response.content)
            
            # Validate with Pydantic
            validated_result = CVExtractedFields(**result)
            logger.info("[LOOP-DEBUG] JSON parsing fallback succeeded")
            return validated_result.model_dump()
            
        except Exception as fallback_error:
            logger.warning(f"[LOOP-DEBUG] JSON parser fallback failed: {fallback_error}, using manual parsing")



            # Final fallback: Manual parsing
            response = llm.invoke(complete_prompt)
            
            # Parse JSON with multi-level strategy
            parsed_json = parse_json_response(response.content)
            
            # Validate with Pydantic
            validated_result = CVExtractedFields(**parsed_json)
            logger.info("[LOOP-DEBUG] Manual parsing succeeded")
            return validated_result.model_dump()

