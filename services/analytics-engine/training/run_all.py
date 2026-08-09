"""Train every GuideU model and print a consolidated report.

    python -m training.run_all --dataset-dir "../../../Travel Planning"
    python -m training.run_all --report results.json

The printed report is the source of the numbers quoted in docs/ml.md and in the
thesis evaluation chapter, so it deliberately includes the baseline comparisons
next to each model rather than the winning figure alone.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

MODELS = ("scam_classifier", "route_recommender", "guide_ranker", "arrivals_forecaster", "tourist_segments")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all GuideU models.")
    parser.add_argument("--dataset-dir", default=None, help="Override the Travel Planning dataset directory.")
    parser.add_argument("--report", default=None, help="Also write the full report to this JSON file.")
    parser.add_argument(
        "--only", nargs="*", choices=MODELS, default=None, help="Train only the named models."
    )
    args = parser.parse_args()

    if args.dataset_dir:
        os.environ["GUIDEU_DATASET_DIR"] = args.dataset_dir

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    # Imported after the env override so settings pick up the right dataset dir.
    from training import train_forecast, train_guides, train_recommender, train_scam, train_segments

    trainers = {
        "scam_classifier": train_scam.train,
        "route_recommender": train_recommender.train,
        "guide_ranker": train_guides.train,
        "arrivals_forecaster": train_forecast.train,
        "tourist_segments": train_segments.train,
    }
    selected = args.only or list(MODELS)

    report: dict[str, dict] = {}
    for name in selected:
        result = trainers[name]()
        report[name] = {key: value for key, value in result.items() if key != "card"}

    print("\n===== GuideU model training report =====")
    print(json.dumps({name: block.get("metrics", {}) for name, block in report.items()}, indent=2, default=str))

    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nFull report with baseline comparisons written to {args.report}")


if __name__ == "__main__":
    main()
