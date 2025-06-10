import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import calendar
import json
import numpy as np

# Read the main commits data
print("Loading and analyzing commit data...")
df = pd.read_csv('firefox_commits.csv')

# Convert date column to datetime with explicit parsing and UTC conversion
df['date'] = pd.to_datetime(df['date'], format="%a %b %d %H:%M:%S %Y %z", utc=True)

# Extract year and month
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

def plot_monthly_commits_2021():
    """Plot monthly commit frequency for 2021"""
    # Create figure
    plt.style.use('seaborn')  # Use a nicer style
    plt.figure(figsize=(15, 8))

    # Month names for x-axis
    month_names = list(calendar.month_abbr)[1:]

    # Get data for 2021
    year_data = df[df['year'] == 2021]
    monthly_commits = year_data.groupby('month').size().reindex(range(1, 13), fill_value=0)

    # Create bar plot
    bars = plt.bar(range(1, 13), monthly_commits.values, color='#3498db', alpha=0.7)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom')

    # Customize the plot
    plt.title('Monthly Commit Frequency in Firefox Repository (2021)', fontsize=16, pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Number of Commits', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')

    # Set x-axis ticks to show month names
    plt.xticks(range(1, 13), month_names)

    # Add year total commits annotation
    total_commits = monthly_commits.sum()
    avg_monthly = total_commits / 12
    stats_text = f'Total commits in 2021: {total_commits:,}\nMonthly average: {avg_monthly:.1f}'
    plt.text(0.02, 0.95, stats_text,
            transform=plt.gca().transAxes, fontsize=12,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    plt.tight_layout()
    plt.show()

    # Print detailed statistics for 2021
    print("\nCommit Statistics for 2021:")
    print("-" * 30)
    print(f"Total commits: {total_commits:,}")
    print(f"Monthly average: {avg_monthly:.1f}")
    print("\nCommits by month:")
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        commit_count = monthly_commits[month]
        print(f"{month_name:10} : {commit_count:,}")

def create_first_time_contributors_dataset():
    """Create and save first-time contributors dataset"""
    # Sort by date to ensure we get the earliest commit for each author
    df_sorted = df.sort_values('date')

    # Get the first commit for each unique author
    first_commits = df_sorted.drop_duplicates(subset=['author'], keep='first')

    # Sort the first commits by date
    first_commits = first_commits.sort_values('date')

    # Save to CSV for future use
    first_commits.to_csv('firefox_first_commits.csv', index=False)
    print("\nSaved first commits dataset to 'firefox_first_commits.csv'")
    return first_commits

def analyze_new_contributors():
    """Analyze and visualize new contributors data"""
    # Read the first commits dataset
    first_commits_df = pd.read_csv('firefox_first_commits.csv')

    # Convert date column to datetime using ISO format parsing
    first_commits_df['date'] = pd.to_datetime(first_commits_df['date'], utc=True)

    # Extract year and month
    first_commits_df['year'] = first_commits_df['date'].dt.year
    first_commits_df['month'] = first_commits_df['date'].dt.month

    # Create figure
    plt.style.use('seaborn')
    plt.figure(figsize=(15, 8))

    # Month names for x-axis
    month_names = list(calendar.month_abbr)[1:]

    # Get data for 2021
    year_data = first_commits_df[first_commits_df['year'] == 2021]
    monthly_commits = year_data.groupby('month').size().reindex(range(1, 13), fill_value=0)

    # Create bar plot
    bars = plt.bar(range(1, 13), monthly_commits.values, color='#e74c3c', alpha=0.7)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom')

    # Customize the plot
    plt.title('Monthly New Contributors in Firefox (2021)', fontsize=16, pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Number of New Contributors', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')

    # Set x-axis ticks to show month names
    plt.xticks(range(1, 13), month_names)

    # Add year total commits annotation
    total_contributors = monthly_commits.sum()
    avg_monthly = total_contributors / 12
    stats_text = f'Total new contributors in 2021: {total_contributors:,}\nMonthly average: {avg_monthly:.1f}'
    plt.text(0.02, 0.95, stats_text,
            transform=plt.gca().transAxes, fontsize=12,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    plt.tight_layout()
    plt.show()

    # Print detailed statistics for 2021
    print("\nNew Contributor Statistics for 2021:")
    print("-" * 40)
    print(f"Total new contributors: {total_contributors:,}")
    print(f"Monthly average: {avg_monthly:.1f}")
    print("\nNew contributors by month:")
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        contributor_count = monthly_commits[month]
        print(f"{month_name:10} : {contributor_count:,}")

    return first_commits_df

def analyze_phabricator_data():
    """Analyze Phabricator review data"""
    # Define the year we want to analyze
    YEAR = 2021

    try:
        # Load the JSON file
        with open(f"phab_firefox_revisions_{YEAR}.json", "r") as file:
            revisions = json.load(file)

        # Flatten the transactions data
        all_transactions = []
        for rev in revisions:
            if "transactions" in rev:
                for txn in rev["transactions"]:
                    all_transactions.append({
                        "date": datetime.fromtimestamp(txn["dateCreated"]),
                        "type": txn["type"]
                    })

        # Create DataFrame and resample by week
        df_txn = pd.DataFrame(all_transactions)
        weekly_counts = df_txn.resample('W', on='date').size()

        # Filter data for the year 2021
        weekly_counts_2021 = weekly_counts['2021']

        # Apply smoothing using a rolling average
        smoothed_counts = weekly_counts_2021.rolling(window=4, center=True).mean()

        # Create the plot
        plt.figure(figsize=(15, 8))
        plt.style.use('seaborn')

        # Plot smoothed weekly transaction counts
        plt.plot(smoothed_counts.index, smoothed_counts.values, linewidth=2)

        # Customize the plot
        plt.title('Firefox Code Review Transactions per Week (2021)', fontsize=14, pad=20)
        plt.xlabel('Week', fontsize=12)
        plt.ylabel('Number of Transactions', fontsize=12)
        plt.grid(True, alpha=0.3)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)

        # Add some padding to prevent label cutoff
        plt.tight_layout()
        plt.show()

    except FileNotFoundError:
        print(f"Warning: Could not find phab_firefox_revisions_{YEAR}.json")
        print("Skipping Phabricator data analysis.")

def main():
    """Main function to run all analyses"""
    # Plot monthly commits for 2021
    print("\n1. Analyzing monthly commits for 2021...")
    plot_monthly_commits_2021()

    # Create first-time contributors dataset
    print("\n2. Creating first-time contributors dataset...")
    create_first_time_contributors_dataset()

    # Analyze new contributors
    print("\n3. Analyzing new contributors...")
    analyze_new_contributors()

    # Analyze Phabricator data
    print("\n4. Analyzing Phabricator review data...")
    analyze_phabricator_data()

if __name__ == "__main__":
    main() 