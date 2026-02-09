import json
import logging
import asyncio
from pprint import pprint
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.prompt_config import PromptConfig
from app.models.omni_ch_insights import OmniChannelInsights

logger = logging.getLogger(__name__)


def load_prompt_config(prompt_file: str) -> PromptConfig:
    """Load and validate prompt configuration from YAML file"""
    prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file
    with open(prompt_path, 'r') as f:
        config_data = yaml.safe_load(f)
    return PromptConfig(**config_data)


async def generate_summary_with_prompt(
    bedrock_client,
    prompt_variables: Dict[str, Any],
    bedrock_mode: str,
    prompt_version_arn: Optional[str] = None,
    inference_profile_arn: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt_yaml_file: str = "primary.yaml",
    guardrail_config: Optional[Dict[str, str]] = None
) -> OmniChannelInsights:
    """
    Generate a summary using Bedrock Converse API.
    
    Supports 3 modes (in priority order):
    1. Prompt Management: Use prompt_version_arn (includes template + inference config)
    2. Inference Profile: Use inference_profile_arn (requires loading config from YAML)
    3. Direct Model: Use model_id (requires loading config from YAML)
    
    Args:
        bedrock_client: Boto3 Bedrock Runtime client
        prompt_variables: Dictionary of variables to fill in the prompt template
        prompt_version_arn: ARN of prompt version (Mode 1)
        inference_profile_arn: ARN of inference profile (Mode 2)
        model_id: Foundation model ID (Mode 3)
        prompt_yaml_file: YAML file to load config from for modes 2 & 3
        guardrail_config: Optional guardrail configuration
    
    Returns:
        OmniChannelInsights containing the model response
    """
    try:
        # Determine which mode to use
        if bedrock_mode == "prompt_management" and prompt_version_arn:
            # Mode 1: Prompt Management (includes template + inference config)
            logger.info(f"Using Prompt Management: {prompt_version_arn}")
            model_identifier = prompt_version_arn
            use_prompt_variables = True
            inference_config = None
            messages = None
            
        elif bedrock_mode in ["inference_profile", "direct_model"] and (inference_profile_arn or model_id):
            # Mode 2 or 3: Load config from YAML
            selected_id = inference_profile_arn if bedrock_mode == "inference_profile" else model_id
            mode_name = "Inference Profile" if bedrock_mode == "inference_profile" else "Direct Model"
            logger.info(f"Using {mode_name}: {selected_id}")
            logger.info(f"Loading configuration from {prompt_yaml_file}")
            
            # Load prompt config from YAML
            prompt_config = load_prompt_config(prompt_yaml_file)
            model_identifier = selected_id
            use_prompt_variables = False
            
            # Build inference configuration
            inference_config = {
                "maxTokens": prompt_config.inference_config.max_tokens,
                "temperature": prompt_config.inference_config.temperature,
                "topP": prompt_config.inference_config.top_p,
            }
            if prompt_config.inference_config.stop_sequences:
                inference_config["stopSequences"] = prompt_config.inference_config.stop_sequences
            
            # Substitute variables in template
            template = prompt_config.template
            for key, value in prompt_variables.items():
                placeholder = f"{{{{{key}}}}}"
                template = template.replace(placeholder, str(value))
            
            # Build messages for Converse API
            messages = [
                {
                    "role": "user",
                    "content": [{"text": template},  {"cachePoint": {"type": "default"}}]
                }
            ]
            
        else:
            raise ValueError("Must provide one of: prompt_version_arn, inference_profile_arn, or model_id")
        
        logger.debug(f"Prompt variables: {json.dumps(prompt_variables, indent=2)}")
        
        # Prepare Converse API request
        request_params = {"modelId": model_identifier}
        
        if use_prompt_variables:
            # Mode 1: Transform variables for prompt management
            formatted_variables = {}
            for key, value in prompt_variables.items():
                if isinstance(value, dict) and "text" in value:
                    formatted_variables[key] = value
                else:
                    formatted_variables[key] = {"text": str(value)}
            request_params["promptVariables"] = formatted_variables
        else:
            # Mode 2 & 3: Use messages + inference config
            request_params["messages"] = messages
            request_params["inferenceConfig"] = inference_config
        
        # Add guardrail config if provided
        if guardrail_config and guardrail_config.get("guardrailIdentifier"):
            request_params["guardrailConfig"] = guardrail_config
            logger.info(f"Using guardrail: {guardrail_config['guardrailIdentifier']}")
        
        # Call Bedrock Converse API asynchronously (boto3 is synchronous, so run in thread pool)
        response = await asyncio.to_thread(
            bedrock_client.converse,
            **request_params
        )
        
        logger.info("Successfully received response from Bedrock")
        logger.debug(f"Response metadata: {response.get('ResponseMetadata', {})}")
        
        # Extract the generated text from response
        output = response.get("output", {})
        usage = response.get("usage", {})
        message = output.get("message", {})
        content = message.get("content", [])

        # pprint(usage)
        
        pprint(response.get("trace", {}))

        if content and len(content) > 0:
            generated_text = content[0].get("text", "No content generated.").strip()
            logger.info(f"Generated summary length: {len(generated_text)} characters")
            logger.debug(f"Generated summary: {generated_text}")
        else:
            generated_text = "No content generated."
            logger.warning("No content in response")
            
        generated_text = generated_text.replace("The customer's activities are summarized as follows:", "").strip()
        
        # Return structured response
        return OmniChannelInsights(
            model_id=model_identifier,
            guardrail_version=guardrail_config.get("guardrailVersion", "NA") if guardrail_config else "NA",
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            cached_read_tokens=usage.get("cacheReadInputTokens", 0),
            cached_write_tokens=usage.get("cacheWriteInputTokens", 0),
            summary_text=generated_text,
            source_trigger_interaction_id="NA",
            summarized_interaction_count=0,
            summary_window_start_dt=datetime.now(),
            summary_window_end_dt=datetime.now(),
            generated_at_dt=datetime.now()
        )
        
    except Exception as e:
        error_msg = str(e)
        
        # Check for specific error types
        if "AccessDeniedException" in error_msg:
            logger.error("Access denied to Bedrock Converse API with prompts. Ensure IAM permissions include bedrock:InvokeModel with prompt resources.")
            logger.error("Required permissions: bedrock:Converse, bedrock:InvokeModel")
        elif "ValidationException" in error_msg:
            logger.error(f"Validation error in Bedrock request: {error_msg}")
        
        logger.error(f"Error calling Bedrock Converse API: {error_msg}", exc_info=True)
        raise
