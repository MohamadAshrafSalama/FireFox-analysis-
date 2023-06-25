"""
Summary statistics and response time analysis for Bugzilla data.
"""

import pandas as pd
import numpy as np


def bug_summary_stats(bugs_df):
    """
    Compute summary statistics for a bug dataset.

    Parameters
    ----------
    bugs_df : pd.DataFrame
        DataFrame from data_collector.fetch_bugs

    Returns
    -------
    dict
        Summary statistics
    """
    stats = {
        "total_bugs": len(bugs_df),
        "unique_reporters": bugs_df["creator"].nunique() if "creator" in bugs_df else None,
        "unique_assignees": bugs_df["assigned_to"].nunique() if "assigned_to" in bugs_df else None,
    }

    if "status" in bugs_df:
        stats["status_counts"] = bugs_df["status"].value_counts().to_dict()

    if "resolution" in bugs_df:
        resolved = bugs_df[bugs_df["resolution"].notna() & (bugs_df["resolution"] != "")]
        stats["resolution_counts"] = resolved["resolution"].value_counts().to_dict()
        stats["resolution_rate"] = len(resolved) / len(bugs_df) if len(bugs_df) > 0 else 0

    if "severity" in bugs_df:
        stats["severity_counts"] = bugs_df["severity"].value_counts().to_dict()

    if "component" in bugs_df:
        stats["top_components"] = bugs_df["component"].value_counts().head(10).to_dict()

    if "creation_time" in bugs_df:
        bugs_df["creation_time"] = pd.to_datetime(bugs_df["creation_time"])
        stats["date_range"] = {
            "start": str(bugs_df["creation_time"].min()),
            "end": str(bugs_df["creation_time"].max()),
        }
        monthly = bugs_df.set_index("creation_time").resample("M").size()
        stats["monthly_avg"] = monthly.mean()
        stats["monthly_std"] = monthly.std()
        stats["busiest_month"] = str(monthly.idxmax())

    return stats


def comment_summary_stats(comments_df, text_col="text"):
    """
    Compute summary statistics for comments.

    Parameters
    ----------
    comments_df : pd.DataFrame
    text_col : str

    Returns
    -------
    dict
    """
    stats = {
        "total_comments": len(comments_df),
        "unique_authors": comments_df["author"].nunique() if "author" in comments_df else None,
        "unique_bugs": comments_df["bug_id"].nunique() if "bug_id" in comments_df else None,
    }

    if text_col in comments_df:
        lengths = comments_df[text_col].fillna("").str.len()
        word_counts = comments_df[text_col].fillna("").str.split().str.len()

        stats["avg_char_length"] = lengths.mean()
        stats["median_char_length"] = lengths.median()
        stats["avg_word_count"] = word_counts.mean()
        stats["median_word_count"] = word_counts.median()
        stats["empty_comments"] = int((word_counts == 0).sum())

    if "author" in comments_df:
        author_counts = comments_df["author"].value_counts()
        stats["top_commenters"] = author_counts.head(10).to_dict()
        stats["comments_per_author_mean"] = author_counts.mean()
        stats["comments_per_author_median"] = author_counts.median()

    if "bug_id" in comments_df:
        bug_counts = comments_df.groupby("bug_id").size()
        stats["comments_per_bug_mean"] = bug_counts.mean()
        stats["comments_per_bug_median"] = bug_counts.median()
        stats["max_comments_on_single_bug"] = int(bug_counts.max())

    return stats


def response_time_analysis(comments_df, date_col="created"):
    """
    Analyze response times between comments on bugs.

    Computes time between the initial bug report (comment 0) and
    the first response (comment 1), as well as inter-comment intervals.

    Parameters
    ----------
    comments_df : pd.DataFrame
        Must have bug_id, count (comment index), and a datetime column

    Returns
    -------
    dict
        Response time statistics
    """
    df = comments_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    if "count" not in df.columns:
        # derive comment order within each bug
        df = df.sort_values([date_col])
        df["count"] = df.groupby("bug_id").cumcount()

    # first response time: time between comment 0 and comment 1
    first_comments = df[df["count"] == 0].set_index("bug_id")[date_col].rename("t0")
    second_comments = df[df["count"] == 1].set_index("bug_id")[date_col].rename("t1")

    merged = pd.concat([first_comments, second_comments], axis=1).dropna()
    merged["first_response_hours"] = (merged["t1"] - merged["t0"]).dt.total_seconds() / 3600

    # inter-comment times
    df_sorted = df.sort_values(["bug_id", date_col])
    df_sorted["prev_time"] = df_sorted.groupby("bug_id")[date_col].shift(1)
    df_sorted["interval_hours"] = (
        (df_sorted[date_col] - df_sorted["prev_time"]).dt.total_seconds() / 3600
    )
    intervals = df_sorted["interval_hours"].dropna()

    stats = {
        "first_response": {
            "mean_hours": merged["first_response_hours"].mean(),
            "median_hours": merged["first_response_hours"].median(),
            "std_hours": merged["first_response_hours"].std(),
            "p25_hours": merged["first_response_hours"].quantile(0.25),
            "p75_hours": merged["first_response_hours"].quantile(0.75),
            "p90_hours": merged["first_response_hours"].quantile(0.90),
            "bugs_analyzed": len(merged),
            "responded_within_1h": int((merged["first_response_hours"] <= 1).sum()),
            "responded_within_24h": int((merged["first_response_hours"] <= 24).sum()),
        },
        "inter_comment": {
            "mean_hours": intervals.mean(),
            "median_hours": intervals.median(),
            "std_hours": intervals.std(),
        },
    }

    return stats


def contributor_analysis(comments_df, bugs_df=None, author_col="author"):
    """
    Analyze contributor patterns.

    Parameters
    ----------
    comments_df : pd.DataFrame
    bugs_df : pd.DataFrame, optional
    author_col : str

    Returns
    -------
    dict
    """
    author_counts = comments_df[author_col].value_counts()

    # contribution distribution
    total = len(comments_df)
    top_1_pct = int(max(1, len(author_counts) * 0.01))
    top_5_pct = int(max(1, len(author_counts) * 0.05))
    top_10_pct = int(max(1, len(author_counts) * 0.10))

    stats = {
        "total_contributors": len(author_counts),
        "top_1pct_share": author_counts.head(top_1_pct).sum() / total,
        "top_5pct_share": author_counts.head(top_5_pct).sum() / total,
        "top_10pct_share": author_counts.head(top_10_pct).sum() / total,
        "single_comment_authors": int((author_counts == 1).sum()),
        "gini_coefficient": _gini(author_counts.values),
    }

    # bugs per contributor
    if "bug_id" in comments_df:
        bugs_per_author = comments_df.groupby(author_col)["bug_id"].nunique()
        stats["avg_bugs_per_contributor"] = bugs_per_author.mean()
        stats["median_bugs_per_contributor"] = bugs_per_author.median()

    return stats


def _gini(values):
    """Compute Gini coefficient for inequality measurement."""
    values = np.sort(np.array(values, dtype=float))
    n = len(values)
    if n == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * values) - (n + 1) * np.sum(values)) / (n * np.sum(values))


def severity_resolution_crosstab(bugs_df):
    """
    Cross-tabulation of severity vs resolution status.
    """
    if "severity" not in bugs_df or "resolution" not in bugs_df:
        return None

    ct = pd.crosstab(bugs_df["severity"], bugs_df["resolution"], margins=True)
    return ct


def weekly_activity_summary(comments_df, date_col="created"):
    """
    Summarize activity by week.
    """
    df = comments_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    weekly = df.set_index(date_col).resample("W").agg(
        comment_count=("bug_id", "size"),
        unique_authors=("author", "nunique"),
        unique_bugs=("bug_id", "nunique"),
    )

    return weekly
