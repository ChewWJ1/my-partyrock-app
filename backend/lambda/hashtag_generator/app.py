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


def call_bedrock(system_prompt, user_prompt, max_tokens=800, temperature=0.7):
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
            "You are a hashtag strategist for social media. "
            "Generate a curated set of hashtags optimized for reach and engagement. "
            "Organize them into three tiers:\n"
            "1. **High-Volume (Popular):** 5 widely-used hashtags with millions of posts for broad reach.\n"
            "2. **Mid-Range (Niche):** 5 moderately popular hashtags that target a specific community.\n"
            "3. **Low-Competition (Growth):** 5 smaller, emerging hashtags for discoverability.\n\n"
            "Also provide a ready-to-copy block of all 15 hashtags on one line.\n"
            "Tailor hashtags to the specific platform's culture and algorithm preferences."
        )

        user_prompt = (
            f"Generate optimized hashtags for:\n"
            f"- Topic: {topic}\n"
            f"- Platform: {platform}\n"
            f"- Tone: {tone}\n\n"
            f"Provide 15 hashtags in 3 tiers plus a copy-paste block."
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
