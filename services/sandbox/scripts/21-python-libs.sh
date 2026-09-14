#!/usr/bin/env bash
set -euo pipefail

python3 -m venv /opt/pytools
/opt/pytools/bin/pip install --upgrade pip wheel setuptools

/opt/pytools/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch
/opt/pytools/bin/pip install tensorflow-cpu

/opt/pytools/bin/pip install \
    numpy pandas polars scipy scikit-learn statsmodels pyarrow duckdb sqlite-utils \
    matplotlib seaborn plotly altair \
    Pillow opencv-python-headless scikit-image imageio \
    transformers sentence-transformers onnxruntime spacy nltk gensim \
    xgboost lightgbm catboost \
    requests httpx aiohttp beautifulsoup4 lxml parsel selectolax readability-lxml scrapy \
    sqlalchemy sqlmodel psycopg pymysql redis pymongo \
    ipython jupyterlab \
    easyocr paddleocr \
    openpyxl python-docx python-pptx xlsxwriter reportlab fpdf2 tabulate pikepdf \
    pydub mutagen

/opt/pytools/bin/python -m nltk.downloader -d /opt/nltk_data punkt stopwords || true