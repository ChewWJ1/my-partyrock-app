# CaptionCraft: Social Media Caption Generator 🚀

> A PartyRock AI app migrated to a real AWS deployment.  
> Original: [CaptionCraft on PartyRock](https://partyrock.aws/u/chewwj/EPJN6ILHh/CaptionCraft%3A-Social-Media-Caption-Generator)

## What It Does

CaptionCraft generates **engaging social media captions**, **optimized hashtags**, and **perfect emoji combinations** based on your post topic, target platform, and desired tone of voice.

### Widgets → AWS Components

| # | Widget | Type | AWS Component |
|---|--------|------|---------------|
| 1 | Post Topic | User Input | Frontend form textarea |
| 2 | Platform | User Input (Dropdown) | Frontend form select |
| 3 | Tone | User Input (Dropdown) | Frontend form select |
| 4 | Caption Generator | Text Generation ✨ | Lambda + Bedrock + API Gateway |
| 5 | Hashtag Generator | Text Generation ✨ | Lambda + Bedrock + API Gateway |
| 6 | Emoji Suggester | Text Generation ✨ | Lambda + Bedrock + API Gateway |

## Architecture

```
Browser  ──►  S3 Static Website (index.html)
                      │
                      ▼
             API Gateway REST API (prod, API Key protected)
    ├── POST /caption   →  caption_generator   →  Bedrock
    ├── POST /hashtags  →  hashtag_generator   →  Bedrock
    └── POST /emojis    →  emoji_suggester     →  Bedrock
```

## Project Structure

```
my-partyrock-app/
├── frontend/
│   └── index.html              # Single-page app (S3 hosted)
├── backend/
│   └── lambda/
│       ├── caption_generator/
│       │   └── app.py          # Generates 3 caption options
│       ├── hashtag_generator/
│       │   └── app.py          # Generates tiered hashtags
│       └── emoji_suggester/
│           └── app.py          # Suggests emoji combinations
├── infra/
│   └── template.yaml           # AWS SAM template
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD
└── README.md
```

## Deployment Guide

Follow the [PartyRock → Real App Tutorial](https://docs.eliteacademy.id/tutorials/partyrock-to-aws/tutorial.html).

### Quick Steps

1. **Enable Bedrock models** in your AWS region (ap-southeast-1):
   - `anthropic.claude-3-haiku-20240307-v1:0` (or any available Claude/Nova model)

2. **Create an S3 bucket** for SAM deployment artifacts.

3. **Add 5 GitHub Secrets** (Settings → Secrets → Actions):

   | Secret | Value |
   |--------|-------|
   | `AWS_ACCESS_KEY_ID` | IAM user access key |
   | `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
   | `SAM_DEPLOY_BUCKET` | S3 bucket name for SAM artifacts |
   | `AWS_REGION` | e.g. `ap-southeast-1` |
   | `API_KEY_VALUE` | Random string (20+ chars) you make up |

4. **Push to main** or click **Run workflow** in GitHub Actions.

5. **Visit your Frontend URL** printed in the deploy output.

## API Endpoints

All endpoints require `x-api-key` header.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/caption` | Generate 3 caption options |
| POST | `/hashtags` | Generate tiered hashtag suggestions |
| POST | `/emojis` | Suggest emoji combinations |

### Request Body

```json
{
  "topic": "Launching our new eco-friendly water bottle",
  "platform": "Instagram",
  "tone": "Catchy & Engaging",
  "audience": "Gen Z environmentalists",
  "cta": "Shop now"
}
```

### Response

```json
{
  "success": true,
  "result": "### Option 1: The Hook & Punch\n...",
  "model": "anthropic.claude-3-haiku-20240307-v1:0"
}
```

## Cost Estimate

For a personal app with light usage (~100 requests/day):
- **Lambda**: Free tier (1M requests/month)
- **API Gateway**: Free tier (1M calls/month for 12 months)
- **S3**: ~$0.01/month
- **Bedrock**: ~$0.01–0.05 per request (varies by model)

**Estimated total: < $5/month** for typical personal use.

## License

MIT
