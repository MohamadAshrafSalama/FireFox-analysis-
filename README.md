# Mozilla Firefox Analysis

## Overview
This repository contains scripts and notebooks used to explore the Mozilla Firefox source code repository.  It includes commit statistics, bug tracker comments and Phabricator review data to help understand development activity over time.

## Prerequisites

Before running this project, ensure you have:

1. Python 3.8 or higher installed
2. Git installed
3. Clone this repository
4. Clone the Firefox repository (required for analysis):
```bash
git clone https://github.com/mozilla/gecko-dev.git firefox-repo
```

## Project Structure
```
firefox-analysis/
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore file
├── README.md            # This file
├── requirements.txt     # Python dependencies
├── notebook.ipynb       # Main analysis notebook
├── firefox-repo/        # Firefox repository (you need to clone this separately)
└── docs/               # Documentation files
```

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/firefox-analysis.git
cd firefox-analysis
```

2. Clone the Firefox repository (required):
```bash
git clone https://github.com/mozilla/gecko-dev.git firefox-repo
```

3. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Copy the environment variables file:
```bash
cp .env.example .env
```

6. Run the repository analysis script (optional):
```bash
./analyze_repo.sh firefox-repo commit_data.json
```

7. Start Jupyter Notebook:
```bash
jupyter notebook
```

## Environment Variables
Create a `.env` file based on `.env.example` and fill in your credentials:
- `GITHUB_TOKEN`: Token used for GitHub API access
- `API_KEY`: Your API key (if needed)
- Add other environment variables as needed

## Contributing
1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## Important Note
The Firefox repository (`firefox-repo/`) is not included in this repository and needs to be cloned separately using the instructions above. This is done to keep the repository size manageable and to ensure you always have the latest Firefox source code.

## License
This project is licensed under the MIT License - see the LICENSE file for details. 