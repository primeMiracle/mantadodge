"""Инструменты агента. Все пути ограничены рабочей папкой (workspace)."""
import csv
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH


class Workspace:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        (self.root / "output").mkdir(parents=True, exist_ok=True)

    def path(self, p: str) -> Path:
        full = (self.root / p).resolve()
        if full != self.root and self.root not in full.parents:
            raise ValueError(f"Путь вне рабочей папки: {p}")
        return full


def list_files(ws: Workspace, directory: str = ".") -> str:
    base = ws.path(directory)
    files = sorted(str(f.relative_to(ws.root)) for f in base.rglob("*") if f.is_file())
    return "\n".join(files) or "(пусто)"


def read_document(ws: Workspace, path: str) -> str:
    f = ws.path(path)
    ext = f.suffix.lower()
    if ext in (".txt", ".md", ".json"):
        return f.read_text(encoding="utf-8", errors="replace")
    if ext == ".csv":
        with f.open(encoding="utf-8", errors="replace", newline="") as fh:
            return "\n".join(" | ".join(r) for r in csv.reader(fh))
    if ext == ".docx":
        d = Document(str(f))
        out = [p.text for p in d.paragraphs if p.text.strip()]
        for i, t in enumerate(d.tables, 1):
            out.append(f"\n[Таблица {i}]")
            out += [" | ".join(c.text.strip() for c in r.cells) for r in t.rows]
        return "\n".join(out)
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join(p.extract_text() or "" for p in PdfReader(str(f)).pages)
    if ext in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(str(f), data_only=True)
        out = []
        for s in wb.worksheets:
            out.append(f"[Лист: {s.title}]")
            for row in s.iter_rows(values_only=True):
                if any(c is not None for c in row):
                    out.append(" | ".join("" if c is None else str(c) for c in row))
        return "\n".join(out)
    raise ValueError(f"Неподдерживаемый формат: {ext}")


def create_docx(ws: Workspace, path: str, title: str, blocks: list) -> str:
    d = Document()
    d.add_heading(title, level=0)
    for b in blocks:
        t = b.get("type")
        if t == "heading":
            d.add_heading(b["text"], level=int(b.get("level", 1)))
        elif t == "paragraph":
            p = d.add_paragraph(b["text"])
            if b.get("align") == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif b.get("align") == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif t == "bullets":
            for item in b["items"]:
                d.add_paragraph(item, style="List Bullet")
        elif t == "numbered":
            for item in b["items"]:
                d.add_paragraph(item, style="List Number")
        elif t == "table":
            rows = b["rows"]
            tbl = d.add_table(rows=1, cols=len(b["header"]), style="Table Grid")
            for c, h in zip(tbl.rows[0].cells, b["header"]):
                c.text = str(h)
                for r in c.paragraphs[0].runs:
                    r.bold = True
            for row in rows:
                cells = tbl.add_row().cells
                for c, v in zip(cells, row):
                    c.text = str(v)
        elif t == "signatures":
            tbl = d.add_table(rows=1, cols=len(b["parties"]))
            for c, party in zip(tbl.rows[0].cells, b["parties"]):
                c.text = f"{party}\n\n_______________ / ______________"
        else:
            raise ValueError(f"Неизвестный тип блока: {t}")
    out = ws.path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(out))
    return f"Сохранено: {out.relative_to(ws.root)}"


def fill_template(ws: Workspace, template: str, output: str, values: dict) -> str:
    """Заменяет {{ключ}} в .docx-шаблоне (абзацы и таблицы)."""
    d = Document(str(ws.path(template)))

    def sub(par):
        text = "".join(r.text for r in par.runs)
        new = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(values.get(m.group(1), m.group(0))), text)
        if new != text and par.runs:
            par.runs[0].text = new
            for r in par.runs[1:]:
                r.text = ""

    for p in d.paragraphs:
        sub(p)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    sub(p)
    out = ws.path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(out))
    return f"Сохранено: {out.relative_to(ws.root)}"


TOOL_SCHEMAS = [
    {"name": "list_files", "description": "Список файлов в папке рабочего пространства.",
     "input_schema": {"type": "object", "properties": {"directory": {"type": "string"}}}},
    {"name": "read_document", "description": "Прочитать документ (txt, md, csv, json, docx, pdf, xlsx) и вернуть текст.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "create_docx", "description": "Создать .docx. blocks — список блоков: "
     "{type:heading,text,level} | {type:paragraph,text,align?} | {type:bullets|numbered,items:[..]} | "
     "{type:table,header:[..],rows:[[..]]} | {type:signatures,parties:[..]}.",
     "input_schema": {"type": "object", "properties": {
         "path": {"type": "string", "description": "например output/akt_001.docx"},
         "title": {"type": "string"},
         "blocks": {"type": "array", "items": {"type": "object"}}},
         "required": ["path", "title", "blocks"]}},
    {"name": "fill_template", "description": "Заполнить .docx-шаблон с плейсхолдерами {{ключ}} значениями.",
     "input_schema": {"type": "object", "properties": {
         "template": {"type": "string"}, "output": {"type": "string"},
         "values": {"type": "object"}}, "required": ["template", "output", "values"]}},
]

HANDLERS = {
    "list_files": list_files,
    "read_document": read_document,
    "create_docx": create_docx,
    "fill_template": fill_template,
}
