import anthropic  # noqa

from .prompts import SYSTEM_PROMPT
from .tools import HANDLERS, TOOL_SCHEMAS, Workspace

MODEL = "claude-sonnet-5-5"


class DocAgent:
    def __init__(self, workspace: str = "workspace", model: str = MODEL, verbose: bool = True):
        self.client = anthropic.Anthropic()
        self.ws = Workspace(workspace)
        self.model = model
        self.verbose = verbose
        self.messages: list = []

    def _run_tool(self, name: str, args: dict) -> tuple[str, bool]:
        try:
            return str(HANDLERS[name](self.ws, **args)), False
        except Exception as e:  # ошибка возвращается модели, чтобы она могла исправиться
            return f"Ошибка: {e}", True

    def ask(self, text: str, max_steps: int = 20) -> str:
        self.messages.append({"role": "user", "content": text})
        for _ in range(max_steps):
            resp = self.client.messages.create(
                model=self.model, max_tokens=8000, system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS, messages=self.messages,
            )
            self.messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                return "".join(b.text for b in resp.content if b.type == "text")
            results = []
            for b in resp.content:
                if b.type == "tool_use":
                    if self.verbose:
                        print(f"  → {b.name}({list(b.input)})")
                    out, err = self._run_tool(b.name, b.input)
                    results.append({"type": "tool_result", "tool_use_id": b.id,
                                    "content": out, "is_error": err})
            self.messages.append({"role": "user", "content": results})
        return "Достигнут лимит шагов."


class OpenAIDocAgent:
    """Тот же агент, но для любых OpenAI-совместимых API (OpenAI, OpenRouter, Gemini, Ollama...)."""

    def __init__(self, workspace="workspace", model=None, verbose=True):
        import os
        from openai import OpenAI
        self.client = OpenAI(
            api_key=os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or "none",
            base_url=os.environ.get("LLM_BASE_URL") or None,
        )
        self.model = model or os.environ.get("LLM_MODEL") or "gpt-4o"
        self.ws = Workspace(workspace)
        self.verbose = verbose
        self.tools = [{"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in TOOL_SCHEMAS]
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def ask(self, text: str, max_steps: int = 20) -> str:
        import json
        self.messages.append({"role": "user", "content": text})
        for _ in range(max_steps):
            resp = self.client.chat.completions.create(
                model=self.model, messages=self.messages, tools=self.tools)
            msg = resp.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))
            if not msg.tool_calls:
                return msg.content or ""
            for call in msg.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                    out = str(HANDLERS[call.function.name](self.ws, **args))
                except Exception as e:
                    out = f"Ошибка: {e}"
                if self.verbose:
                    print(f"  → {call.function.name}")
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": out})
        return "Достигнут лимит шагов."


def make_agent(workspace="workspace", verbose=True):
    """Выбор провайдера: LLM_PROVIDER=anthropic|openai (по умолчанию — anthropic, если есть
    ANTHROPIC_API_KEY, иначе openai-совместимый)."""
    import os
    provider = os.environ.get("LLM_PROVIDER")
    if not provider:
        provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "openai"
    if provider == "anthropic":
        return DocAgent(workspace, verbose=verbose)
    return OpenAIDocAgent(workspace, verbose=verbose)
