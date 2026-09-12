from __future__ import annotations

from pathlib import Path

from swing_trader.context_builder import write_context


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = write_context(root)
    print(output.relative_to(root))


if __name__ == "__main__":
    main()
