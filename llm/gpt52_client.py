from openai import OpenAI
import os
import json

try:
    import numpy as np
except Exception:
    np = None


def _json_safe(obj):
    # numpy -> python types
    if np is not None:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
    return str(obj)


class GPT52Client:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def generate_creative(self, system_prompt: str, user_payload: dict) -> dict:
        payload_str = json.dumps(user_payload, ensure_ascii=False, default=_json_safe)

        # 1) Try Responses API (preferred)
        try:
            resp = self.client.responses.create(
                model="gpt-5.2",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload_str},
                ],
                # JSON mode (older) — works on many models; json_schema is even better later
                response_format={"type": "json_object"},
            )

            text = getattr(resp, "output_text", None)
            if not text:
                # fallback if SDK returns output differently
                text = str(resp)

            return json.loads(text)

        except TypeError as e:
            # 2) Fallback: Chat Completions API (older SDK compatibility)
            cc = self.client.chat.completions.create(
                model="gpt-5.2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload_str},
                ],
                response_format={"type": "json_object"},
            )
            content = cc.choices[0].message.content
            return json.loads(content)
