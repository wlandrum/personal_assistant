import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def category_bar(data: list[dict], out_path: str) -> str:
    _ensure_dir(out_path)
    cats = [d["category"] for d in data]
    totals = [d["total"] for d in data]
    plt.figure(figsize=(8, 5))
    plt.bar(cats, totals)
    plt.ylabel("Spending")
    plt.title("Spending by category")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path


def monthly_trend(data: list[dict], out_path: str) -> str:
    _ensure_dir(out_path)
    months = [d["month"] for d in data]
    totals = [d["total"] for d in data]
    plt.figure(figsize=(8, 5))
    plt.plot(months, totals, marker="o")
    plt.ylabel("Spending")
    plt.title("Spending by month")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path
