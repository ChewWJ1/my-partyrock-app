import json
import os
import boto3
from botocore.exceptions import ClientError

DEFAULT_MODELS = [
    os.environ.get("BEDROCK_MODEL_ID", "").strip(),
    "anthropic.claude-3-haiku-20240307-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v2:0",
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


def call_bedrock(system_prompt, user_prompt, max_tokens=600, temperature=0.8):
    bedrock = get_bedrock_client()
    last_error = None
    for model_id in DEFAULT_MODELS:
        try:
            response = bedrock.converse(
                modelId=model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={"maxTokens": max_tokens, "temperature": temperature}
            )
            return response["output"]["message"]["content"][0]["text"], model_id
        except ClientError as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    raise RuntimeError("No available Bedrock model.")


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"status": "ok"})}

    try:
        body = event.get("body", "{}")
        data = json.loads(body) if isinstance(body, str) else (body or {})

        topic = data.get("topic", "").strip()
        platform = data.get("platform", "Instagram").strip()
        tone = data.get("tone", "Catchy & Engaging").strip()

        if not topic:
            return {"statusCode": 400, "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "Missing required field 'topic'"})}

        system_prompt = (
            "You are an emoji styling expert for social media content. "
            "Your job is to suggest the perfect emoji combinations that enhance captions. "
            "Provide:\n"
            "1. **Opener Emojis:** 3-5 emojis to start a caption with visual impact.\n"
            "2. **Inline Accent Emojis:** 5-8 emojis to sprinkle throughout the caption for emphasis.\n"
            "3. **Closer/CTA Emojis:** 3-5 emojis to end with that drive action (clicks, comments, shares).\n"
            "4. **Emoji Sentence:** A creative all-emoji mini-story (5-8 emojis) that captures the post's vibe.\n\n"
            "Explain briefly what each emoji conveys in context. "
            "Adapt choices to the platform's emoji culture."
        )

        user_prompt = (
            f"Suggest perfect emojis for:\n"
            f"- Topic: {topic}\n"
            f"- Platform: {platform}\n"
            f"- Tone: {tone}\n\n"
            f"Provide organized emoji suggestions with explanations."
        )

        result_text, used_model = call_bedrock(system_prompt, user_prompt)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"success": True, "result": result_text, "model": used_model})
        }
    except Exception as e:
        return {"statusCode": 500, "headers": CORS_HEADERS,
                "body": json.dumps({"success": False, "error": str(e)})}
