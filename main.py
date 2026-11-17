"""CLI: python main.py "Составь акт по файлам из input/" или без аргументов — диалог."""
import sys

from docagent.agent import DocAgent


def main():
    agent = DocAgent("workspace")
    if len(sys.argv) > 1:
        print(agent.ask(" ".join(sys.argv[1:])))
        return
    print("Агент по документам. Файлы кладите в workspace/input. Выход: Ctrl+C / 'exit'.")
    while True:
        try:
            q = input("\nВы: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("exit", "quit", "выход"):
            break
        if q:
            print("\nАгент:", agent.ask(q))


if __name__ == "__main__":
    main()
