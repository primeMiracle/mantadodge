# ИИ-агент для работы с документами

Составляет отчёты, акты, справки; читает docx/pdf/xlsx/csv/txt; сохраняет результат в `.docx`.

## Запуск
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python main.py                      # диалог
python main.py "Составь акт выполненных работ по данным из input/data.xlsx"
```
Входные файлы — в `workspace/input/`, результат — в `workspace/output/`.
Шаблоны `.docx` с `{{плейсхолдерами}}` кладите в `workspace/templates/`.

## Веб-интерфейс
```bash
python -m web.app   # затем откройте http://localhost:5000
```

## Структура
- `docagent/prompts.py` — системный промпт и структура типовых документов
- `docagent/tools.py` — инструменты (чтение, создание docx, заполнение шаблона), доступ только внутри workspace
- `docagent/agent.py` — цикл агента (Claude tool use)

## Модели и ключи
Без ключа Anthropic можно использовать любую OpenAI-совместимую модель (нужна поддержка tool calling):

| Провайдер | Переменные окружения |
|---|---|
| OpenAI | `LLM_PROVIDER=openai`, `LLM_API_KEY=sk-...`, `LLM_MODEL=gpt-4o` |
| OpenRouter (есть бесплатные модели) | `LLM_PROVIDER=openai`, `LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_API_KEY=...`, `LLM_MODEL=<модель>` |
| Google Gemini (бесплатный тариф) | `LLM_PROVIDER=openai`, `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`, `LLM_API_KEY=...`, `LLM_MODEL=gemini-flash-latest` |
| Ollama (локально, бесплатно) | `LLM_PROVIDER=openai`, `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=qwen2.5:14b` |
| Anthropic | `ANTHROPIC_API_KEY=sk-ant-...` |
