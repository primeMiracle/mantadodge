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
