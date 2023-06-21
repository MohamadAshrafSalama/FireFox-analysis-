# Firefox Bugzilla Comment Analysis

Analysis of Firefox bug report comments from Mozilla's Bugzilla issue tracker, focusing on community interaction patterns, sentiment trends, and discussion topics across different browser components.

## Data Source

All data is collected from the [Bugzilla REST API](https://bugzilla.mozilla.org/rest/) for the Firefox product. The dataset covers bug reports and their associated comments, including metadata like timestamps, authors, severity levels, and component assignments.

## Analysis Methodology

### Data Collection
- Automated collection via Bugzilla REST API with rate limiting
- Covers multiple Firefox components (General, Developer Tools, Address Bar, Session Restore, etc.)
- Includes bug metadata, full comment threads, and change history

### Text Analysis
- **Sentiment Analysis**: TextBlob polarity scoring on cleaned comment text, categorized into positive/neutral/negative
- **Topic Modeling**: Latent Dirichlet Allocation (LDA) to identify recurring discussion themes
- **Keyword Extraction**: TF-IDF weighted keyword and bigram extraction with domain-specific stopword filtering

### Statistical Analysis
- Comment volume and activity patterns (weekly, daily, hourly)
- First-response time distributions across components
- Contributor inequality (Gini coefficient, top-N% share)
- Severity vs. resolution cross-tabulation

## Project Structure

```
src/
    data_collector.py    Bugzilla API data collection
    text_analysis.py     NLP pipeline (sentiment, topics, keywords)
    visualizations.py    Plotting functions and dashboards
    stats.py             Summary statistics and response time analysis
notebooks/
    firefox_analysis.ipynb   Full exploratory analysis notebook
```

## Findings

- Comment activity follows strong weekday patterns, peaking during European/US business hours
- Sentiment is mostly neutral to slightly positive, consistent with technical discussion norms
- LDA reveals topic clusters around crash reports, rendering issues, UI feedback, and developer tooling
- Contribution is highly concentrated: the top 5% of commenters produce the majority of all comments
- Median first-response time varies significantly across components, suggesting uneven triage coverage

## Setup

```bash
pip install -r requirements.txt
python -m src.data_collector   # fetch data from Bugzilla API
jupyter notebook notebooks/firefox_analysis.ipynb
```

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies

## License

MIT
