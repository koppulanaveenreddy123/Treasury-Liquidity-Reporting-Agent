from __future__ import annotations

from app.tools.positions_tool import PositionsTool


def main() -> None:
    """Load the outlier scenario dataset."""
    positions = PositionsTool(data_dir="app/data").load_positions("outlier")
    print(f"Outlier positions loaded: {len(positions)}")


if __name__ == "__main__":
    main()
