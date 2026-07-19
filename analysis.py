import os
import time
import warnings
import numpy as np
import pandas as pd

from itertools import combinations
from multiprocessing import Pool
from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import normalized_mutual_info_score


RESULT_COLUMNS = ["feature1", "feature2", "score", "score_abs", "method", "n_valid"]
WORKER_DF = None
INPUT = "data/processed/data_2.csv"


def init_worker(data):
    global WORKER_DF
    WORKER_DF = data


def analyze_pair(args):
    feature1, feature2, method, threshold, min_n_valid = args
    df = WORKER_DF

    try:
        if method == "cramers_v":
            score = cramers_v(df[feature1], df[feature2])
        elif method == "eta_squared":
            score = correlation_ratio(df[feature1], df[feature2])
        elif method == "mutual_information_num_num":
            score = mutual_info_num_num(df[feature1], df[feature2])
        elif method == "mutual_information_cat_cat":
            score = mutual_info_cat_cat(df[feature1], df[feature2])
        elif method == "mutual_information_cat_num":
            score = mutual_info_cat_num(df[feature1], df[feature2])
        elif method == "distance_correlation":
            score = distance_corr(df[feature1], df[feature2])
        else:
            score = np.nan

        n_valid = df[[feature1, feature2]].dropna().shape[0]
        if pd.notna(score) and n_valid >= min_n_valid and abs(score) >= threshold:
            return {
                "feature1": feature1,
                "feature2": feature2,
                "score": score,
                "score_abs": abs(score),
                "method": method,
                "n_valid": n_valid,
            }

    except Exception as e:
        warnings.warn(f"{method} failed for {feature1} vs {feature2}: {e}")

    return None


def merge_files(folder="correlations", out_filename="CORRELATIONS.csv", pattern="correlation"):
    os.makedirs(folder, exist_ok=True)
    files = []
    for fname in os.listdir(folder):
        if not fname.lower().endswith(".csv"):
            continue
        if pattern not in fname.lower():
            continue
        full = os.path.join(folder, fname)
        try:
            df = pd.read_csv(full)
        except Exception:
            continue
        if not (
            "feature1" in df.columns
            and "feature2" in df.columns
            and "score" in df.columns
        ):
            continue
        if "score_abs" not in df.columns:
            df["score_abs"] = df["score"].abs()
        for col in RESULT_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        files.append(df[RESULT_COLUMNS])

    if not files:
        # write empty file with headers
        out_path = os.path.join(folder, out_filename)
        pd.DataFrame(columns=RESULT_COLUMNS).to_csv(out_path, index=False)
        return pd.DataFrame(columns=RESULT_COLUMNS)

    combined = pd.concat(files, ignore_index=True)

    combined["_pair_key"] = combined.apply(
        lambda row: pair_key(row["feature1"], row["feature2"], row["method"]),
        axis=1,
    )
    combined = combined.sort_values(["score_abs", "score"], ascending=[False, False])
    combined = combined.drop_duplicates(subset=["_pair_key"], keep="first").drop(
        columns=["_pair_key"]
    )

    out_path = os.path.join(folder, out_filename)
    combined.to_csv(out_path, index=False)
    return combined


def encode_category(s):
    return s.astype("category").cat.codes.replace(-1, np.nan)


def pair_key(feature1, feature2, method):
    return (*sorted((str(feature1), str(feature2))), str(method))


def matrix_to_pair_list(
    corr_matrix,
    data,
    method,
    threshold=0.3,
    top_n=None,
):
    corr_top = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    pairs = corr_top.stack().reset_index()
    pairs.columns = ["feature1", "feature2", "score"]
    pairs["score_abs"] = pairs["score"].abs()
    pairs["method"] = method
    pairs = pairs[pairs["score_abs"] >= threshold].dropna(subset=["score"])

    pairs["n_valid"] = [
        data[[f1, f2]].dropna().shape[0]
        for f1, f2 in pairs[["feature1", "feature2"]].to_numpy()
    ]

    pairs = pairs.sort_values("score_abs", ascending=False)
    pairs = pairs.head(top_n) if top_n else pairs
    return pairs[RESULT_COLUMNS]


def cramers_v(x, y):
    table = pd.crosstab(x, y)
    if table.shape[0] < 2 or table.shape[1] < 2:
        return np.nan
    chi2, _, _, _ = chi2_contingency(table)
    n = table.to_numpy().sum()
    r, k = table.shape
    return np.sqrt((chi2 / n) / min(r - 1, k - 1))


def correlation_ratio(categories, values):
    temp = pd.DataFrame({"category": categories, "value": values}).dropna()
    if temp["category"].nunique() < 2 or temp["value"].nunique() < 2:
        return np.nan
    grand_mean = temp["value"].mean()
    ss_between = sum(
        len(g) * (g["value"].mean() - grand_mean) ** 2
        for _, g in temp.groupby("category", observed=False)
    )
    ss_total = ((temp["value"] - grand_mean) ** 2).sum()
    return np.nan if ss_total == 0 else ss_between / ss_total


def mutual_info_to_unit_interval(score):
    if pd.isna(score):
        return np.nan
    return 1 - np.exp(-max(score, 0))


def mutual_info_num_num(x, y):
    temp = pd.DataFrame({"x": x, "y": y}).dropna()
    if temp["x"].nunique() < 2 or temp["y"].nunique() < 2 or len(temp) < 5:
        return np.nan
    score = mutual_info_regression(
        temp[["x"]].astype(float),
        temp["y"].astype(float),
    )[0]
    return mutual_info_to_unit_interval(score)


def mutual_info_cat_cat(x, y):
    temp = pd.DataFrame({"x": encode_category(x), "y": encode_category(y)}).dropna()
    if temp["x"].nunique() < 2 or temp["y"].nunique() < 2:
        return np.nan
    return normalized_mutual_info_score(temp["x"], temp["y"])


def mutual_info_cat_num(cat, num):
    temp = pd.DataFrame({"cat": encode_category(cat), "num": num}).dropna()
    if temp["cat"].nunique() < 2 or temp["num"].nunique() < 2 or len(temp) < 5:
        return np.nan
    score = mutual_info_regression(
        temp[["cat"]],
        temp["num"].astype(float),
        discrete_features=True,
    )[0]
    return mutual_info_to_unit_interval(score)


def distance_corr(x, y):
    temp = pd.DataFrame({"x": x, "y": y}).dropna()
    if temp["x"].nunique() < 2 or temp["y"].nunique() < 2 or len(temp) < 3:
        return np.nan
    try:
        import dcor

        return dcor.distance_correlation(
            temp["x"].to_numpy(dtype=float),
            temp["y"].to_numpy(dtype=float),
        )
    except Exception:
        return np.nan


def save_batch(rows, path):
    if not path or not rows:
        return
    df = pd.DataFrame(rows)
    write_header = not os.path.exists(path)
    df.to_csv(path, mode="a", header=write_header, index=False)


def clean_result_frame(df, threshold=0.0, top_n=None, min_n_valid=0):
    if df.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    if "score_abs" not in df.columns:
        df["score_abs"] = df["score"].abs()
    if "n_valid" not in df.columns:
        df["n_valid"] = np.nan

    df["_pair_key"] = df.apply(
        lambda row: pair_key(row["feature1"], row["feature2"], row["method"]),
        axis=1,
    )
    df = df.drop_duplicates(subset=["_pair_key"], keep="last").drop(columns=["_pair_key"])
    df = df.dropna(subset=["score"])
    df = df[df["score_abs"] >= threshold]
    df = df[df["n_valid"].isna() | (df["n_valid"] >= min_n_valid)]
    df = df.sort_values(["score_abs", "score"], ascending=[False, False])
    if top_n:
        df = df.head(top_n)
    return df[RESULT_COLUMNS]


def clean_results(path, threshold=0.0, top_n=None, min_n_valid=0):
    if not path or not os.path.exists(path):
        return pd.DataFrame(columns=RESULT_COLUMNS)

    df = pd.read_csv(path)
    df = clean_result_frame(df, threshold, top_n, min_n_valid)
    df.to_csv(path, index=False)
    return df


def analyze(
    data,
    output_csv,
    threshold=0.05,
    top_n=1000,
    methods=(
        "pearson",
        "spearman",
        "cramers_v",
        "eta_squared",
        "mutual_information",
        "distance_correlation",
    ),
    batch_size=500,
    min_n_valid=100,  # with <100 entries for some feature combination, correlation scores are somewhat meaningless and misleading
    max_categories=80,  # defuse id-like columns. ids always have a correlation of 1 xD
):
    print(f"\n\n", "=" * 60)
    start = time.time()
    df = data.copy()

    if os.path.exists(output_csv):
        os.remove(output_csv)

    num_cols = df.select_dtypes(include=["number", "Int64", "float64", "int64"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    cat_cols = [col for col in cat_cols if 1 < df[col].nunique(dropna=True) <= max_categories]
    bool_cols = df.select_dtypes(include=["bool", "boolean"]).columns.tolist()

    num_bool_cols = list(dict.fromkeys(num_cols + bool_cols))
    cat_bool_cols = list(dict.fromkeys(cat_cols + bool_cols))
    num_bool_cols = [c for c in num_bool_cols if df[c].nunique(dropna=True) > 1]
    cat_bool_cols = [c for c in cat_bool_cols if df[c].nunique(dropna=True) > 1]
    df_num_bool = df[num_bool_cols].astype(float) if num_bool_cols else pd.DataFrame(index=df.index)

    batch = []

    for method in ["pearson", "spearman"]:
        if method not in methods or len(num_bool_cols) < 2:
            continue

        print("=" * 20, f" {method.upper()} ", "=" * 20)
        corr = df_num_bool.corr(method=method)
        result = matrix_to_pair_list(corr, df_num_bool, method, threshold, top_n)

        save_batch(result.to_dict("records"), output_csv)

    pair_tasks = []

    if "cramers_v" in methods:
        pair_tasks += [(c1, c2, "cramers_v") for c1, c2 in combinations(cat_bool_cols, 2)]

    if "eta_squared" in methods:
        pair_tasks += [
            (cat, num, "eta_squared")
            for cat in cat_bool_cols
            for num in num_bool_cols
            if cat != num
        ]

    if "mutual_information" in methods:
        pair_tasks += [
            (c1, c2, "mutual_information_num_num")
            for c1, c2 in combinations(num_cols, 2)
        ]
        pair_tasks += [
            (c1, c2, "mutual_information_cat_cat")
            for c1, c2 in combinations(cat_bool_cols, 2)
        ]
        pair_tasks += [
            (cat, num, "mutual_information_cat_num")
            for cat in cat_bool_cols
            for num in num_cols
        ]

    if "distance_correlation" in methods:
        pair_tasks += [
            (c1, c2, "distance_correlation")
            for c1, c2 in combinations(num_bool_cols, 2)
        ]

    pool_tasks = [
        (feature1, feature2, method, threshold, min_n_valid)
        for feature1, feature2, method in pair_tasks
    ]

    print(f"Processing {len(pool_tasks)} pair_tasks.")
    with Pool(8, initializer=init_worker, initargs=(df,)) as pool:
        for idx, result in enumerate(pool.imap_unordered(analyze_pair, pool_tasks), start=1):
            if idx % batch_size == 0:
                print(f"{idx // batch_size}/{len(pair_tasks) // batch_size} batches")

            if result is not None:
                batch.append(result)

            if len(batch) >= batch_size:
                save_batch(batch, output_csv)
                batch = []

    if batch:
        save_batch(batch, output_csv)

    final = clean_results(
        output_csv,
        threshold=threshold,
        top_n=top_n,
        min_n_valid=min_n_valid,
    )

    elapsed = time.time() - start
    print(f"numeric columns: {len(num_cols)}, categorical columns: {len(cat_cols)}, boolean columns: {len(bool_cols)}")
    print(f"results: {len(final)}")
    print(f"elapsed: {elapsed:.1f}s")

    return final[RESULT_COLUMNS]


def run_suite(df, output_dir="output", sample_n=100, dcor_n=100):
    os.makedirs(output_dir, exist_ok=True)

    jobs = [
        ("pearson", df.sample(n=100), 0.02),
        ("spearman", df.sample(n=100), 0.02),
        ("cramers_v", df.sample(n=100), 0.02),
        ("eta_squared", df.sample(n=100), 0.1),
        ("mutual_information", df.sample(n=100), 0.1),
        ("distance_correlation", df.sample(n=100), 0.1),
    ]

    for method, data, threshold in jobs:
        analyze(
            data,
            f"{output_dir}/correlation_{method}.csv",
            threshold=threshold,
            methods=(method),
            min_n_valid=10,
        )


if __name__ == "__main__":
    df = pd.read_csv(INPUT)

    # analyze(df, "output/correlation.csv", methods=("pearson", "spearman"))
    analyze(df, "output/correlation.csv", methods=("pearson", "spearman", "cramers_v", "eta_squared", "mutual_information", "distance_correlation"))
