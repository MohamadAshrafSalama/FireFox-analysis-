"""
NLP analysis module for Bugzilla comments.

Performs sentiment analysis, topic modeling, and keyword extraction
on Firefox bug report comments.
"""

import re
import pandas as pd
import numpy as np
from collections import Counter

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF

from textblob import TextBlob


# download nltk data if needed
for resource in ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger",
                 "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource
                       else f"corpora/{resource}" if resource in ("stopwords", "wordnet")
                       else f"taggers/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)


# Bugzilla-specific stop words to filter out noise
BUGZILLA_STOPWORDS = {
    "bug", "firefox", "mozilla", "browser", "http", "https", "www",
    "attachment", "comment", "created", "revision", "phabricator",
    "treeherder", "try", "autoland", "patch", "diff", "review",
    "commit", "push", "pushed", "merge", "merged",
}


def clean_comment_text(text):
    """
    Clean a raw Bugzilla comment for NLP processing.

    Removes URLs, email addresses, stack traces, code blocks,
    and Bugzilla-specific markup.
    """
    if not isinstance(text, str):
        return ""

    # remove quoted replies (lines starting with >)
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)

    # remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # remove email addresses
    text = re.sub(r"\S+@\S+\.\S+", "", text)

    # remove hex addresses and stack trace references
    text = re.sub(r"0x[0-9a-fA-F]+", "", text)
    text = re.sub(r"#\d+\s+0x[0-9a-fA-F]+", "", text)

    # remove file paths
    text = re.sub(r"[\w/]+\.\w{1,4}:\d+", "", text)

    # remove bug references (keep the text context)
    text = re.sub(r"bug\s*#?\d+", "bug_reference", text, flags=re.IGNORECASE)

    # remove attachment references
    text = re.sub(r"attachment\s*#?\d+", "", text, flags=re.IGNORECASE)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_and_filter(text, extra_stopwords=None):
    """
    Tokenize text and remove stopwords, short tokens, and numbers.
    """
    stop_words = set(stopwords.words("english")) | BUGZILLA_STOPWORDS
    if extra_stopwords:
        stop_words |= set(extra_stopwords)

    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())

    filtered = []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in stop_words:
            continue
        if t.isdigit():
            continue
        if not t.isalpha():
            continue
        lemma = lemmatizer.lemmatize(t)
        if lemma not in stop_words:
            filtered.append(lemma)

    return filtered


def analyze_sentiment(comments_df, text_col="text"):
    """
    Run sentiment analysis on comment text using TextBlob.

    Parameters
    ----------
    comments_df : pd.DataFrame
        DataFrame containing comment text
    text_col : str
        Column name for the text field

    Returns
    -------
    pd.DataFrame
        Original DataFrame with added sentiment columns:
        polarity (-1 to 1), subjectivity (0 to 1), sentiment_label
    """
    df = comments_df.copy()
    df["clean_text"] = df[text_col].apply(clean_comment_text)

    polarities = []
    subjectivities = []

    for text in df["clean_text"]:
        if not text.strip():
            polarities.append(0.0)
            subjectivities.append(0.0)
            continue
        blob = TextBlob(text)
        polarities.append(blob.sentiment.polarity)
        subjectivities.append(blob.sentiment.subjectivity)

    df["polarity"] = polarities
    df["subjectivity"] = subjectivities

    # label categories
    df["sentiment_label"] = pd.cut(
        df["polarity"],
        bins=[-1.01, -0.1, 0.1, 1.01],
        labels=["negative", "neutral", "positive"],
    )

    return df


def extract_topics(comments_df, text_col="text", n_topics=8, method="lda",
                   max_features=3000, n_top_words=15):
    """
    Extract topics from comments using LDA or NMF.

    Parameters
    ----------
    comments_df : pd.DataFrame
        DataFrame with comment text
    text_col : str
        Text column name
    n_topics : int
        Number of topics to extract
    method : str
        "lda" or "nmf"
    max_features : int
        Maximum vocabulary size for vectorizer
    n_top_words : int
        Number of top words to return per topic

    Returns
    -------
    dict
        Dictionary with keys: model, vectorizer, topic_words, doc_topics
    """
    df = comments_df.copy()
    df["clean_text"] = df[text_col].apply(clean_comment_text)

    # filter out very short comments
    mask = df["clean_text"].str.split().str.len() >= 5
    texts = df.loc[mask, "clean_text"].tolist()

    if method == "lda":
        vectorizer = CountVectorizer(
            max_features=max_features,
            stop_words="english",
            min_df=5,
            max_df=0.7,
        )
    else:
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            min_df=5,
            max_df=0.7,
        )

    doc_term_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    if method == "lda":
        model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20,
            learning_method="online",
        )
    else:
        model = NMF(
            n_components=n_topics,
            random_state=42,
            max_iter=300,
        )

    doc_topics = model.fit_transform(doc_term_matrix)

    topic_words = {}
    for idx, topic in enumerate(model.components_):
        top_indices = topic.argsort()[:-n_top_words - 1:-1]
        topic_words[f"Topic {idx}"] = [feature_names[i] for i in top_indices]

    return {
        "model": model,
        "vectorizer": vectorizer,
        "topic_words": topic_words,
        "doc_topics": doc_topics,
        "texts_mask": mask,
    }


def extract_keywords(comments_df, text_col="text", top_n=50):
    """
    Extract top keywords using TF-IDF scores.

    Parameters
    ----------
    comments_df : pd.DataFrame
    text_col : str
    top_n : int
        Number of top keywords to return

    Returns
    -------
    list of tuple
        (keyword, tfidf_score) pairs sorted by score
    """
    texts = comments_df[text_col].apply(clean_comment_text).tolist()

    tfidf = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        min_df=3,
        max_df=0.6,
        ngram_range=(1, 2),
    )

    matrix = tfidf.fit_transform(texts)
    feature_names = tfidf.get_feature_names_out()

    # average tfidf across all documents
    avg_scores = matrix.mean(axis=0).A1
    top_indices = avg_scores.argsort()[::-1][:top_n]

    return [(feature_names[i], avg_scores[i]) for i in top_indices]


def get_word_frequencies(comments_df, text_col="text", top_n=100):
    """
    Get word frequency counts after cleaning and tokenization.
    """
    all_tokens = []
    for text in comments_df[text_col]:
        cleaned = clean_comment_text(text)
        tokens = tokenize_and_filter(cleaned)
        all_tokens.extend(tokens)

    return Counter(all_tokens).most_common(top_n)


def comment_length_stats(comments_df, text_col="text"):
    """
    Compute comment length statistics.
    """
    lengths = comments_df[text_col].fillna("").str.split().str.len()
    return {
        "mean_words": lengths.mean(),
        "median_words": lengths.median(),
        "std_words": lengths.std(),
        "max_words": lengths.max(),
        "min_words": lengths.min(),
        "total_comments": len(lengths),
        "empty_comments": (lengths == 0).sum(),
    }
