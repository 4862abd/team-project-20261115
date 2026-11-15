import json
import re
from typing import Any

import httpx

from app.core.config import AIAGENT_API_KEY, AIAGENT_API_URL, AIAGENT_MODEL
from app.services.errors import ProcessingError


class AIAgentClient:
    """Adapter for an OpenAI Chat Completions-compatible AIagent endpoint."""

    async def generate_json(
        self,
        client: httpx.AsyncClient,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if not AIAGENT_API_URL or not AIAGENT_MODEL:
            raise ProcessingError(
                "AIAGENT_NOT_CONFIGURED",
                "AI 분석 API 설정이 없습니다. .env에 AIAGENT_API_URL과 AIAGENT_MODEL을 설정해 주세요.",
                503,
            )

        headers = {"Content-Type": "application/json"}
        if AIAGENT_API_KEY:
            headers["Authorization"] = f"Bearer {AIAGENT_API_KEY}"

        request_body = {
            "model": AIAGENT_MODEL,
            "messages": [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            response = await client.post(AIAGENT_API_URL, headers=headers, json=request_body)
            response.raise_for_status()
            try:
                response_data = response.json()
            except json.JSONDecodeError as error:
                raise ProcessingError(
                    "AIAGENT_RESPONSE_NOT_JSON",
                    "AI API가 JSON이 아닌 응답을 반환했습니다. AIAGENT_API_URL이 문서 페이지가 아니라 /v1/chat/completions API 주소인지 확인해 주세요.",
                    502,
                ) from error
            content = self._extract_content(response_data)
            parsed = self._parse_json(content)
            if not isinstance(parsed, dict):
                raise ValueError("The AI response must be a JSON object.")
            return parsed
        except ProcessingError:
            raise
        except httpx.TimeoutException as error:
            raise ProcessingError(
                "AIAGENT_TIMEOUT",
                "AI 분석 요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.",
                504,
            ) from error
        except httpx.HTTPStatusError as error:
            detail = ""
            try:
                error_body = error.response.json()
                api_error = error_body.get("error") if isinstance(error_body, dict) else None
                if isinstance(api_error, dict):
                    error_message = str(api_error.get("message") or "").replace("\r", " ").replace("\n", " ")
                    error_message = error_message[:240]
                    if error_message:
                        detail = f" 세부 내용: {error_message}"
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
            raise ProcessingError(
                "AIAGENT_REQUEST_FAILED",
                f"AI 분석 API 요청이 실패했습니다 (HTTP {error.response.status_code}).{detail} 설정과 API 상태를 확인해 주세요.",
                502,
            ) from error
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as error:
            raise ProcessingError(
                "AIAGENT_RESPONSE_INVALID",
                "AI 분석 결과를 읽지 못했습니다. API 응답 형식과 설정을 확인해 주세요.",
                502,
            ) from error

    @staticmethod
    def _extract_content(response_data: dict[str, Any]) -> str:
        choices = response_data.get("choices") or []
        if not choices:
            raise ValueError("No choices were returned.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") in ("text", "output_text")
            )
        raise ValueError("The response content is missing.")

    @staticmethod
    def _parse_json(content: str) -> Any:
        cleaned = content.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            cleaned = fenced.group(1)
        return json.loads(cleaned)
