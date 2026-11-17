import anthropic

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
