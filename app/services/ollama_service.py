import json
import time
from typing import Any, Dict, Iterator, List
import httpx

from app.config import settings
from app.schemas.triage import (
    PromptEnhanceRequest,
    PromptEnhanceResponse,
    TicketRequest,
    TicketTriageResponse,
)

SYSTEM_TRIAGE_PROMPT = """You are an expert, empathetic Senior Customer Support Lead and Ticket Triage AI.
Analyze the customer's incoming ticket and respond ONLY with a valid JSON object matching this exact schema:

{
  "sentiment": "Frustrated",
  "urgency": "HIGH",
  "category": "Shipping & Delivery",
  "summary": "One sentence summary of the issue",
  "suggested_reply": "A warm, empathetic, highly professional customer response draft addressing the customer by name."
}

Classification Rules:
- sentiment: Must be one of: "Positive", "Neutral", "Frustrated", "Angry"
- urgency: Must be one of: "LOW", "MEDIUM", "HIGH", "CRITICAL"
- category: Must be one of: "Shipping & Delivery", "Billing & Refunds", "Technical Support", "General Inquiry"
- suggested_reply: Write a complete, empathetic reply ready to send to the customer. Acknowledge their emotion, offer an action step, and sign off as 'Support Team'.
Do not return any explanations or markdown backticks outside of the JSON.
"""

SYSTEM_PROMPT_ENHANCER = """You are a World-Class AI Prompt Director and Concept Artist specializing in Midjourney, Stable Diffusion, Flux, and DALL-E 3.
Given a raw user concept, art style, and target engine, engineer a production-ready, highly detailed image generation prompt package.

You MUST respond ONLY with a valid JSON object matching this exact schema:
{
  "enhanced_positive_prompt": "Cinematic wide shot of Deadpool and Spider-Man standing shoulder-to-shoulder on a rain-slicked cyberpunk street, vibrant neon magenta and cyan reflections, intricate suit textures, steam rising from grates, 8k resolution, photorealistic, dramatic volumetric lighting",
  "negative_prompt": "blurry, low quality, oversaturated, deformed hands, extra fingers, mutated anatomy, bad proportions, watermark, signature, ugly face",
  "suggested_aspect_ratio": "16:9",
  "lighting_and_atmosphere": "Moody volumetric neon glow with deep shadows and street puddle reflections",
  "camera_and_composition": "Low-angle dynamic cinematic wide shot, 35mm lens, shallow depth of field",
  "style_tags": ["cyberpunk", "cinematic", "8k", "photorealistic", "volumetric lighting"]
}

Guidelines:
- enhanced_positive_prompt: Write an immersive, vivid description of subjects, environment, lighting, texture, and mood. Avoid generic buzzwords; use tangible visual details.
- negative_prompt: List unwanted artifacts, distortions, and flaws to avoid.
- suggested_aspect_ratio: Choose the ideal ratio for the scene (e.g. "16:9" for landscapes/cinematic, "9:16" for portraits/posters, "1:1" for square icons).
Do NOT include any text or markdown outside of the JSON.
"""


class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_DEFAULT_MODEL

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetch all models currently installed on the Ollama host (192.168.1.16)."""
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                res.raise_for_status()
                data = res.json()
                models = data.get("models", [])
                return [
                    {
                        "name": m.get("name"),
                        "size_gb": round(m.get("size", 0) / (1024**3), 2),
                        "modified_at": m.get("modified_at"),
                    }
                    for m in models
                ]
        except Exception as e:
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}: {str(e)}")

    def triage_ticket(self, request: TicketRequest) -> TicketTriageResponse:
        """
        Submits the support ticket to Ollama with a system prompt and structured JSON enforcement.
        """
        model = request.model or self.default_model
        user_content = (
            f"Customer Name: {request.customer_name}\n"
            f"Subject: {request.subject}\n"
            f"Message Body:\n{request.message}"
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_TRIAGE_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }

        print(f"\n[Ollama Triage] 🚀 Analyzing ticket from '{request.customer_name}' with '{model}'...")
        start_time = time.time()

        url = f"{self.base_url}/api/chat"
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                result = res.json()
        except httpx.ConnectError:
            raise RuntimeError(f"Failed to connect to Ollama at {self.base_url}. Ensure Ollama is running on your LAN.")
        except httpx.TimeoutException:
            raise RuntimeError(f"Ollama took more than 60s to process the ticket on model '{model}'.")

        elapsed = round(time.time() - start_time, 2)
        print(f"[Ollama Triage] ✅ Triaged in {elapsed}s!")

        raw_content = result.get("message", {}).get("content", "{}")
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            parsed = {
                "sentiment": "Neutral",
                "urgency": "MEDIUM",
                "category": "General Inquiry",
                "summary": request.subject,
                "suggested_reply": raw_content,
            }

        return TicketTriageResponse(
            sentiment=parsed.get("sentiment", "Neutral"),
            urgency=parsed.get("urgency", "MEDIUM"),
            category=parsed.get("category", "General Inquiry"),
            summary=parsed.get("summary", request.subject),
            suggested_reply=parsed.get("suggested_reply", "Thank you for reaching out."),
            model_used=model,
            processing_time_seconds=elapsed,
        )

    def stream_ticket_reply(self, request: TicketRequest) -> Iterator[str]:
        """Streams a live AI response for real-time customer reply generation."""
        model = request.model or self.default_model
        user_content = (
            f"Write an empathetic customer support resolution reply to:\n"
            f"Customer: {request.customer_name}\n"
            f"Subject: {request.subject}\n"
            f"Issue: {request.message}"
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a warm, helpful customer support representative. Write a complete resolution email."},
                {"role": "user", "content": user_content},
            ],
            "stream": True,
        }

        url = f"{self.base_url}/api/chat"
        with httpx.Client(timeout=90.0) as client:
            with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk_json = json.loads(line)
                        content = chunk_json.get("message", {}).get("content", "")
                        if content:
                            yield content

    def enhance_image_prompt(self, request: PromptEnhanceRequest) -> PromptEnhanceResponse:
        """
        Uses the selected Ollama model to turn a simple idea into an expert Midjourney/SD prompt package.
        100% private, local, zero third-party image API bottlenecks!
        """
        model = request.model or self.default_model
        start_time = time.time()

        user_content = (
            f"Concept to enhance: {request.raw_prompt}\n"
            f"Art Style: {request.style}\n"
            f"Target Image Generator: {request.target_engine}"
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_ENHANCER},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.5},
        }

        print(f"\n[Ollama Prompt Enhancer] 🎨 Enhancing prompt with '{model}'...")
        url = f"{self.base_url}/api/chat"

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                result = res.json()
        except httpx.ConnectError:
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}.")
        except httpx.TimeoutException:
            raise RuntimeError(f"Ollama took more than 60s to enhance prompt on '{model}'.")

        elapsed = round(time.time() - start_time, 2)
        print(f"[Ollama Prompt Enhancer] ✅ Prompt enhanced in {elapsed}s!")

        raw_content = result.get("message", {}).get("content", "{}")
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            parsed = {
                "enhanced_positive_prompt": f"{request.raw_prompt}, {request.style}, 8k resolution, cinematic lighting, photorealistic, intricate details",
                "negative_prompt": "blurry, low quality, oversaturated, deformed anatomy, bad proportions, watermark",
                "suggested_aspect_ratio": "16:9",
                "lighting_and_atmosphere": "Cinematic volumetric lighting with rich ambient shadows",
                "camera_and_composition": "Wide-angle shot with shallow depth of field",
                "style_tags": [request.style.lower(), "8k", "cinematic"],
            }

        return PromptEnhanceResponse(
            original_prompt=request.raw_prompt,
            enhanced_positive_prompt=parsed.get(
                "enhanced_positive_prompt",
                f"{request.raw_prompt}, {request.style}, 8k, cinematic lighting"
            ),
            negative_prompt=parsed.get(
                "negative_prompt",
                "blurry, low quality, distorted, extra limbs, watermark"
            ),
            suggested_aspect_ratio=parsed.get("suggested_aspect_ratio", "16:9"),
            lighting_and_atmosphere=parsed.get("lighting_and_atmosphere", "Cinematic lighting"),
            camera_and_composition=parsed.get("camera_and_composition", "Dynamic composition"),
            style_tags=parsed.get("style_tags", []),
            model_used=model,
            processing_time_seconds=elapsed,
        )


ollama_service = OllamaService()


def get_ollama_service() -> OllamaService:
    return ollama_service
