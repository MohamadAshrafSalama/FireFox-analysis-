# Mozela Project

## Overview
This repository contains a data analysis and exploration project using Jupyter notebooks. The project is structured to follow best practices in data science and software development.

## Prerequisites

Before running this project, you need to:

1. Clone this repository
2. Clone the Firefox repository (required for analysis):
```bash
git clone https://github.com/mozilla/gecko-dev.git firefox-repo
```

## Project Structure
```
mozela/
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
git clone https://github.com/yourusername/mozela.git
cd mozela
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

6. Start Jupyter Notebook:
```bash
jupyter notebook
```

## Environment Variables
Create a `.env` file based on `.env.example` and fill in your credentials:
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