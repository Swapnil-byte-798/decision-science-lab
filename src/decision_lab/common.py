import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def report_dir(root: Path, name: str):
    path = root / "reports" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, data):
    def convert(value):
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
        raise TypeError(f"Cannot serialize {type(value)}")

    path.write_text(json.dumps(data, indent=2, default=convert, allow_nan=False) + "\n")


def save_chart(fig, path):
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
