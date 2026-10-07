import json
import os
import boto3
from botocore.exceptions import ClientError

# Bedrock models to try in order of priority / availability
DEFAULT_MODELS = [
    os.environ.get("BEDROCK_MODEL_ID", "").strip(),
    "anthropic.claude-3-haiku-20240307-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v2:0",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "amazon.nova-micro-v1:0",
    "amazon.nova-lite-v1:0"
]
DEFAULT_MODELS = [m for m in DEFAULT_MODELS if m]

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-api-key",
    "Access-Control-Allow-Methods": "POST,OPTIONS"
}

def get_bedrock_client():
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    return boto3.client("bedrock-runtime", region_name=region)

def call_bedrock(system_prompt: str, user_prompt: str, max_tokens: int = 1500, temperature: float = 0.7):
    """
    Invokes Bedrock using the model-agnostic Converse API with fallback models.
    """
    bedrock = get_bedrock_client()
    last_error = None
    
    for model_id in DEFAULT_MODELS:
        try:
            response = bedrock.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}]
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            )
            output_text = response["output"]["message"]["content"][0]["text"]
            return output_text, model_id
        except ClientError as e:
            last_error = e
            # Try next fallback model
            continue
            
    if last_error:
        raise last_error
    raise RuntimeError("No available Bedrock model could be invoked.")

def handler(event, context):
    """
    CaptionCraft - Engaging Caption Generator Lambda Handler
    """
    # Handle CORS preflight OPTIONS request
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"status": "ok"})
        }

    try:
        # Parse body
        body = event.get("body", "{}")
        if isinstance(body, str):
            data = json.loads(body) if body else {}
        else:
            data = body or {}

        topic = data.get("topic", "").strip()
        platform = data.get("platform", "Instagram").strip()
        tone = data.get("tone", "Catchy & Engaging").strip()
        audience = data.get("audience", "General audience").strip()
        cta = data.get("cta", "Comment below and share").strip()

        if not topic:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing required field 'topic'"})
            }

        system_prompt = (
            "You are CaptionCraft AI, an elite social media copywriter and growth strategist. "
            "Your mission is to craft viral, high-converting social media captions tailored to specific platforms. "
            "Follow these platform principles:\n"
            "- Instagram: Strong hook in the first 1-2 lines, clean whitespace/line breaks, relatable storytelling, clear CTA.\n"
            "- TikTok: Short, punchy, curiosity-inducing hook, conversational Gen Z/millennial friendly tone.\n"
            "- LinkedIn: Professional yet authentic thought-leadership, spacing between short sentences, actionable insight, open conversation.\n"
            "- Twitter/X: Ultra-concise, bold opening statement, under 260 characters per option, punchy CTA.\n"
            "- Facebook: Warm, community-oriented, questions that prompt comments and shares.\n"
            "- Threads: Casual, conversational, witty, unpolished authenticity.\n\n"
            "Format your output clearly with three distinct options:\n"
            "### Option 1: The Hook & Punch (Short & Catchy)\n"
            "<caption text>\n\n"
            "### Option 2: The Storyteller & Value (Narrative & Engaging)\n"
            "<caption text>\n\n"
            "### Option 3: The Conversation Starter (Question & Community-Driven)\n"
            "<caption text>\n\n"
            "Keep formatting clean with aesthetic emojis where appropriate."
        )

        user_prompt = (
            f"Please generate 3 high-impact social media caption options with the following details:\n\n"
            f"- Topic / Content Description: {topic}\n"
            f"- Target Platform: {platform}\n"
            f"- Tone of Voice: {tone}\n"
            f"- Target Audience: {audience}\n"
            f"- Call-to-Action Goal: {cta}\n\n"
            f"Provide 3 distinct, creative, and fully fleshed out caption options."
        )

        result_text, used_model = call_bedrock(system_prompt, user_prompt, max_tokens=1500, temperature=0.7)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": True,
                "result": result_text,
                "platform": platform,
                "tone": tone,
                "model": used_model
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
