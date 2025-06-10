# Getting Started with Firefox Analysis

This guide explains how to set up the Firefox Analysis project and make the most of its features.

## Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher installed
- Git installed
- Basic understanding of Jupyter notebooks
- Basic understanding of Python programming

## Installation

Follow these steps to set up your development environment:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/firefox-analysis.git
   cd firefox-analysis
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

- `notebook.ipynb`: Main Jupyter notebook for analysis
- `requirements.txt`: Python package dependencies
- `.env`: Environment variables (create from .env.example)
- `docs/`: Documentation files
- `analyze_repo.sh`: Shell script used to generate commit data from the Firefox repository

## Running the Analysis

Once you have cloned both this repository and the Firefox source, you can create commit statistics with:
```bash
./analyze_repo.sh ../path/to/firefox-repo commit_data.json
```

After generating the data, run the Python analysis script:
```bash
python firefox_analysis.py
```

## Best Practices

1. **Version Control**
   - Always create a new branch for features/changes
   - Write meaningful commit messages
   - Don't commit sensitive data

2. **Environment Variables**
   - Never commit `.env` file
   - Use `.env.example` as a template
   - Keep sensitive information in `.env`

3. **Documentation**
   - Document your code
   - Update README.md when needed
   - Keep documentation up to date

## Getting Help

If you need help:
1. Check the existing documentation
2. Look for similar issues in the repository
3. Create a new issue with detailed information

## Contributing

See the main README.md file for contribution guidelines. 