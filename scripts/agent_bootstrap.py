from __future__ import annotations

import os
from pathlib import Path

from swing_trader.context_builder import write_context
from swing_trader.handoff import write_handoff


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    allow_remote = os.getenv("SWING_TRADER_OFFLINE", "0") not in {"1", "true", "TRUE"}

    context_path = write_context(root)
    handoff_path = write_handoff(root, allow_remote=allow_remote)

    print(f"context={context_path.relative_to(root)}")
    print(f"handoff={handoff_path.relative_to(root)}")
    print(f"remote_discovery={'enabled' if allow_remote else 'disabled'}")


if __name__ == "__main__":
    main()
