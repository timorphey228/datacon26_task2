from pathlib import Path

PDF_PATH = Path('papers/article1/1-s2.0-S0960894X08008214-main.pdf')
ROOT_PATH = Path('.')

TABLES = [
    {
        'name':'table1',
        'page':2,
        'top_mm':30,
        'left_mm':11.54,
        'width_mm':183.46,
        'height_mm':59.14
    }
]

IMAGES = [
    {
        'name':'image1',
        'page':1,
        'top_mm':23.42,
        'left_mm':37.8,
        'width_mm':128.52,
        'height_mm':29.5
    },
    {
        'name':'image2',
        'page':1,
        'top_mm':71.38,
        'left_mm':14.73,
        'width_mm':80.04,
        'height_mm':23.39
    },
    {
        'name':'image3',
        'page':1,
        'top_mm':190.41,
        'left_mm':34.02,
        'width_mm':130.42,
        'height_mm':72.04
    },
    {
        'name':'image4',
        'page':2,
        'top_mm':100,
        'left_mm':12.08,
        'width_mm':81.61,
        'height_mm':26.31
    }
]

GRAPHS = [
    {
        'name':'graph1',
        'page':2,
        'top_mm':177.95,
        'left_mm':20.48,
        'width_mm':76.17,
        'height_mm':55.61,
        "x_min":7,
        "x_max":11,
        "y_min":3,
        "y_max":9
    }
]

PATTERNS = {
    "Ki":r"(?i)(K\s*i|K_i|Ki)\s*[:=]?\s*(\d+\.?\d*(?:\s*(?:±|\+/-)\s*\d+\.?\d*)?)\s*(nM|µM|μM|uM|pM|M)?",
    "concentration":r"(?i)(\d+\.?\d*)\s*(pM|nM|µM|μM|uM|mM|M)\b",
    "temperature":r"(?i)(\d+\.?\d*)\s*(°C|℃|K)\b",
    "pH":r"(?i)\bpH\s*[:=]?\s*(\d+\.?\d*)",
    "mu":r"(?i)(μ|µ|mu)\s*[:=]\s*(\d+\.?\d*)\s*(nM|µM|μM|uM|M)?",
    "time":r"(?i)(\d+\.?\d*)\s*(s|sec|min|h|hr)\b"
}