"""Train every GuideU model and print a consolidated report.

    python -m training.run_all --dataset-dir "../../../Travel Planning"
"""
from __future__ import annotations

import argparse
import json
import logging
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all GuideU models.")
    parser.add_argument("--dataset-dir", default=None, help="Override the Travel Planning dataset directory.")
    args = parser.parse_args()

    if args.dataset_dir:
        os.environ["GUIDEU_DATASET_DIR"] = args.dataset_dir

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    # Imported after the env override so settings pick up the right dataset dir.
    from training import train_recommender, train_scam

    report = {
        "scam_classifier": train_scam.train()["metrics"],
        "route_recommender": train_recommender.train()["metrics"],
    }
    print("\n===== GuideU model training report =====")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
