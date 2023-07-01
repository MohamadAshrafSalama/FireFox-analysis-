"""
Bugzilla REST API data collection module.

Fetches bug reports, comments, and metadata from Mozilla's Bugzilla instance
for Firefox-related components.
"""

import requests
import pandas as pd
import time
import os
import json
from datetime import datetime, timedelta
from tqdm import tqdm


BUGZILLA_API = "https://bugzilla.mozilla.org/rest"

# Firefox product components of interest
FIREFOX_COMPONENTS = [
    "General",
    "Untriaged",
    "Address Bar",
    "Developer Tools",
    "Migration",
    "Preferences",
    "Session Restore",
    "Tabbed Browser",
    "Theme",
    "Toolbars and Customization",
]


def fetch_bugs(product="Firefox", component=None, start_date=None, end_date=None,
               limit=500, status=None):
    """
    Fetch bug reports from Bugzilla REST API.

    Parameters
    ----------
    product : str
        Product name (default: "Firefox")
    component : str or list, optional
        Component name(s) to filter by
    start_date : str, optional
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
    limit : int
        Maximum number of bugs to fetch per request
    status : str or list, optional
        Bug status filter (e.g., "RESOLVED", "NEW")

    Returns
    -------
    pd.DataFrame
        DataFrame containing bug metadata
    """
    params = {
        "product": product,
        "limit": limit,
        "include_fields": "id,summary,status,resolution,creation_time,last_change_time,"
                          "assigned_to,component,severity,priority,op_sys,platform,"
                          "creator,keywords,whiteboard",
    }

    if component:
        params["component"] = component
    if start_date:
        params["creation_time"] = start_date
    if end_date:
        params["creation_time_end"] = end_date
    if status:
        params["status"] = status

    all_bugs = []
    offset = 0

    while True:
        params["offset"] = offset
        resp = requests.get(f"{BUGZILLA_API}/bug", params=params, timeout=45)
        resp.raise_for_status()
        data = resp.json()

        bugs = data.get("bugs", [])
        if not bugs:
            break

        all_bugs.extend(bugs)
        offset += limit

        if len(bugs) < limit:
            break

        time.sleep(0.5)  # rate limiting

    df = pd.DataFrame(all_bugs)
    if not df.empty:
        df["creation_time"] = pd.to_datetime(df["creation_time"])
        df["last_change_time"] = pd.to_datetime(df["last_change_time"])

    return df


def fetch_bug_comments(bug_ids, batch_size=50):
    """
    Fetch comments for a list of bug IDs.

    Parameters
    ----------
    bug_ids : list
        List of bug IDs to fetch comments for
    batch_size : int
        Number of bugs to query per API call

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: bug_id, comment_id, author, created, text, count
    """
    all_comments = []

    for i in tqdm(range(0, len(bug_ids), batch_size), desc="Fetching comments"):
        batch = bug_ids[i:i + batch_size]

        for bug_id in batch:
            try:
                resp = requests.get(
                    f"{BUGZILLA_API}/bug/{bug_id}/comment",
                    timeout=45,
                )
                resp.raise_for_status()
                data = resp.json()

                comments = data.get("bugs", {}).get(str(bug_id), {}).get("comments", [])

                for c in comments:
                    all_comments.append({
                        "bug_id": bug_id,
                        "comment_id": c.get("id"),
                        "author": c.get("author"),
                        "created": c.get("creation_time"),
                        "text": c.get("text", ""),
                        "count": c.get("count", 0),
                    })

            except requests.RequestException as e:
                print(f"Error fetching comments for bug {bug_id}: {e}")
                continue

            time.sleep(0.3)

    df = pd.DataFrame(all_comments)
    if not df.empty:
        df["created"] = pd.to_datetime(df["created"])

    return df


def fetch_bug_history(bug_ids):
    """
    Fetch change history for bugs.

    Parameters
    ----------
    bug_ids : list
        List of bug IDs

    Returns
    -------
    pd.DataFrame
        DataFrame of status changes and field modifications
    """
    all_changes = []

    for bug_id in tqdm(bug_ids, desc="Fetching history"):
        try:
            resp = requests.get(
                f"{BUGZILLA_API}/bug/{bug_id}/history",
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()

            for entry in data.get("bugs", [{}])[0].get("history", []):
                for change in entry.get("changes", []):
                    all_changes.append({
                        "bug_id": bug_id,
                        "who": entry.get("who"),
                        "when": entry.get("when"),
                        "field": change.get("field_name"),
                        "removed": change.get("removed"),
                        "added": change.get("added"),
                    })

        except requests.RequestException as e:
            print(f"Error fetching history for bug {bug_id}: {e}")

        time.sleep(0.3)

    df = pd.DataFrame(all_changes)
    if not df.empty:
        df["when"] = pd.to_datetime(df["when"])

    return df


def collect_dataset(product="Firefox", components=None, year=2021,
                    output_dir="data"):
    """
    Collect a complete dataset of bugs and comments for analysis.

    Parameters
    ----------
    product : str
        Bugzilla product name
    components : list, optional
        List of components (defaults to FIREFOX_COMPONENTS)
    year : int
        Year to collect data for
    output_dir : str
        Directory to save output CSV files

    Returns
    -------
    tuple
        (bugs_df, comments_df) DataFrames
    """
    if components is None:
        components = FIREFOX_COMPONENTS

    os.makedirs(output_dir, exist_ok=True)

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    print(f"Collecting {product} bugs for {year}...")
    bugs_df = fetch_bugs(
        product=product,
        component=components,
        start_date=start_date,
        end_date=end_date,
    )
    print(f"  Found {len(bugs_df)} bugs")

    bug_ids = bugs_df["id"].tolist() if not bugs_df.empty else []

    print(f"Collecting comments for {len(bug_ids)} bugs...")
    comments_df = fetch_bug_comments(bug_ids)
    print(f"  Found {len(comments_df)} comments")

    # save
    bugs_path = os.path.join(output_dir, f"firefox_bugs_{year}.csv")
    comments_path = os.path.join(output_dir, f"firefox_comments_{year}.csv")

    bugs_df.to_csv(bugs_path, index=False)
    comments_df.to_csv(comments_path, index=False)

    print(f"Saved bugs to {bugs_path}")
    print(f"Saved comments to {comments_path}")

    return bugs_df, comments_df


if __name__ == "__main__":
    bugs, comments = collect_dataset(year=2021)
    print(f"\nCollection complete: {len(bugs)} bugs, {len(comments)} comments")
