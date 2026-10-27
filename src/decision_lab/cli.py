import argparse
from pathlib import Path

from decision_lab import experiments, forecasting, retail, uplift
from decision_lab.common import write_json
from decision_lab.data import download, load_hillstrom, load_retail


def main():
    parser = argparse.ArgumentParser(description="Real-data decision-science case studies")
    parser.add_argument("command", choices=["download", "run"])
    parser.add_argument(
        "--project",
        choices=["all", "experiments", "uplift", "customers", "forecasting"],
        default="all",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "download":
        names = (
            ["hillstrom"]
            if args.project in ["experiments", "uplift"]
            else ["retail"]
            if args.project in ["customers", "forecasting"]
            else None
        )
        download(root, names)
        return
    results = {}
    if args.project in ["all", "experiments", "uplift"]:
        df = load_hillstrom(root)
        for name, module in [("experiments", experiments), ("uplift", uplift)]:
            if args.project in ["all", name]:
                results[name] = module.run(df, root)
                print(f"Completed {name}", flush=True)
    if args.project in ["all", "customers", "forecasting"]:
        df = load_retail(root)
        for name, module in [("customers", retail), ("forecasting", forecasting)]:
            if args.project in ["all", name]:
                results[name] = module.run(df, root)
                print(f"Completed {name}", flush=True)
    (root / "reports").mkdir(exist_ok=True)
    write_json(root / "reports" / f"run_{args.project}.json", results)


if __name__ == "__main__":
    main()
