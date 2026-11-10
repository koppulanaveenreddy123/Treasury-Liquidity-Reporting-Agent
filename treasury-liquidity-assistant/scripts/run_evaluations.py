from __future__ import annotations

from app.services.evaluation_service import EvaluationService


def main() -> None:
    """Run the evaluation dataset and print summary results."""
    service = EvaluationService(data_dir="app/data")
    dataset = service.load_dataset()
    print(dataset)


if __name__ == "__main__":
    main()
