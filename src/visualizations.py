"""
Visualization module for Firefox Bugzilla analysis.

Generates plots for comment volume trends, sentiment distributions,
contributor activity, and topic modeling results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from wordcloud import WordCloud


# consistent style
plt.rcParams.update({
    "figure.figsize": (12, 6),
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 100,
})

PALETTE = sns.color_palette("Set2", 10)


def plot_comment_volume(comments_df, date_col="created", freq="W",
                        title="Comment Volume Over Time", ax=None):
    """
    Plot comment volume aggregated by time period.

    Parameters
    ----------
    comments_df : pd.DataFrame
    date_col : str
        Datetime column
    freq : str
        Resampling frequency (D, W, M)
    title : str
    ax : matplotlib.axes.Axes, optional
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 5))

    df = comments_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    volume = df.set_index(date_col).resample(freq).size()

    ax.fill_between(volume.index, volume.values, alpha=0.3, color=PALETTE[0])
    ax.plot(volume.index, volume.values, color=PALETTE[0], linewidth=1.5)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Comments")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return ax


def plot_sentiment_distribution(comments_df, polarity_col="polarity",
                                 label_col="sentiment_label", ax=None):
    """
    Plot sentiment polarity distribution as histogram + pie chart.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # histogram
    axes[0].hist(comments_df[polarity_col].dropna(), bins=50,
                 color=PALETTE[1], alpha=0.7, edgecolor="white")
    axes[0].axvline(0, color="red", linestyle="--", alpha=0.5)
    axes[0].set_title("Sentiment Polarity Distribution")
    axes[0].set_xlabel("Polarity")
    axes[0].set_ylabel("Count")

    # pie
    counts = comments_df[label_col].value_counts()
    colors_map = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
    colors = [colors_map.get(label, PALETTE[0]) for label in counts.index]
    axes[1].pie(counts.values, labels=counts.index, colors=colors,
                autopct="%1.1f%%", startangle=140)
    axes[1].set_title("Sentiment Label Distribution")

    plt.tight_layout()
    return fig


def plot_sentiment_trend(comments_df, date_col="created", polarity_col="polarity",
                          freq="W", ax=None):
    """
    Plot average sentiment polarity over time with rolling mean.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 5))

    df = comments_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    weekly = df.set_index(date_col)[polarity_col].resample(freq).mean()

    ax.plot(weekly.index, weekly.values, alpha=0.4, color=PALETTE[2], linewidth=1)

    # 4-period rolling average
    rolling = weekly.rolling(4, center=True).mean()
    ax.plot(rolling.index, rolling.values, color=PALETTE[2], linewidth=2,
            label="4-week rolling mean")

    ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax.set_title("Sentiment Trend Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Mean Polarity")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return ax


def plot_contributor_activity(comments_df, author_col="author", top_n=20, ax=None):
    """
    Bar chart of most active commenters.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 7))

    top_authors = comments_df[author_col].value_counts().head(top_n)

    bars = ax.barh(range(len(top_authors)), top_authors.values, color=PALETTE[3])
    ax.set_yticks(range(len(top_authors)))

    # truncate long email addresses for display
    labels = [a.split("@")[0] if "@" in a else a for a in top_authors.index]
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_title(f"Top {top_n} Contributors by Comment Count")
    ax.set_xlabel("Number of Comments")
    ax.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()

    return ax


def plot_topic_distribution(topic_words, doc_topics, ax=None):
    """
    Plot topic distribution across documents.

    Parameters
    ----------
    topic_words : dict
        {topic_name: [word_list]} from extract_topics
    doc_topics : np.ndarray
        Document-topic matrix
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # dominant topic per document
    dominant = np.argmax(doc_topics, axis=1)
    topic_counts = pd.Series(dominant).value_counts().sort_index()

    topic_labels = [f"Topic {i}" for i in topic_counts.index]
    bars = ax.bar(topic_labels, topic_counts.values, color=PALETTE[:len(topic_counts)])

    ax.set_title("Document Distribution Across Topics")
    ax.set_xlabel("Topic")
    ax.set_ylabel("Number of Comments")
    ax.grid(True, alpha=0.3, axis="y")

    # add top words as annotation
    for i, (label, count) in enumerate(zip(topic_labels, topic_counts.values)):
        words = topic_words.get(label, [])[:3]
        ax.annotate(", ".join(words), (i, count), ha="center", va="bottom",
                    fontsize=7, rotation=30)

    plt.tight_layout()
    return ax


def plot_comment_length_dist(comments_df, text_col="text", ax=None):
    """
    Histogram of comment lengths (word count).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))

    lengths = comments_df[text_col].fillna("").str.split().str.len()
    # cap at 99th percentile for readability
    cap = int(lengths.quantile(0.99))
    lengths_capped = lengths[lengths <= cap]

    ax.hist(lengths_capped, bins=60, color=PALETTE[4], alpha=0.7, edgecolor="white")
    ax.axvline(lengths.median(), color="red", linestyle="--", label=f"Median: {lengths.median():.0f}")
    ax.set_title("Comment Length Distribution")
    ax.set_xlabel("Word Count")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    return ax


def plot_wordcloud(word_freq, title="Most Common Words", ax=None):
    """
    Generate a word cloud from word frequency data.

    Parameters
    ----------
    word_freq : list of tuple or dict
        Word frequency data
    title : str
    """
    if isinstance(word_freq, list):
        word_freq = dict(word_freq)

    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=200,
        colormap="viridis",
    ).generate_from_frequencies(word_freq)

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))

    ax.imshow(wc, interpolation="bilinear")
    ax.set_title(title)
    ax.axis("off")
    plt.tight_layout()

    return ax


def plot_activity_heatmap(comments_df, date_col="created"):
    """
    Heatmap of comment activity by day of week and hour.
    """
    df = comments_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["hour"] = df[date_col].dt.hour
    df["dayofweek"] = df[date_col].dt.day_name()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
    pivot = df.groupby(["dayofweek", "hour"]).size().unstack(fill_value=0)
    pivot = pivot.reindex(day_order)

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(pivot, cmap="YlOrRd", ax=ax, linewidths=0.5)
    ax.set_title("Comment Activity by Day of Week and Hour (UTC)")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("")
    plt.tight_layout()

    return fig


def create_summary_dashboard(comments_df, sentiment_df=None, topic_results=None,
                              word_freq=None, save_path=None):
    """
    Create a multi-panel summary dashboard.
    """
    fig = plt.figure(figsize=(18, 14))

    # comment volume
    ax1 = fig.add_subplot(3, 2, 1)
    plot_comment_volume(comments_df, ax=ax1)

    # comment length
    ax2 = fig.add_subplot(3, 2, 2)
    plot_comment_length_dist(comments_df, ax=ax2)

    # sentiment
    if sentiment_df is not None:
        ax3 = fig.add_subplot(3, 2, 3)
        plot_sentiment_trend(sentiment_df, ax=ax3)

        ax4 = fig.add_subplot(3, 2, 4)
        plot_contributor_activity(sentiment_df, ax=ax4, top_n=10)

    # topics
    if topic_results is not None:
        ax5 = fig.add_subplot(3, 2, 5)
        plot_topic_distribution(
            topic_results["topic_words"],
            topic_results["doc_topics"],
            ax=ax5,
        )

    # word cloud
    if word_freq is not None:
        ax6 = fig.add_subplot(3, 2, 6)
        plot_wordcloud(word_freq, ax=ax6)

    fig.suptitle("Firefox Bugzilla Comment Analysis Dashboard", fontsize=16, y=1.01)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=150)
        print(f"Dashboard saved to {save_path}")

    return fig
