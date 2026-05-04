from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS
import numpy as np
import re
from urllib.parse import urlparse
import joblib
from tensorflow.keras.models import load_model
import sqlite3
from datetime import datetime

# ==================================================
# Flask Setup
# ==================================================
app = Flask(__name__)
CORS(app)

# ==================================================
# Load ML Models
# ==================================================
xgb_model = joblib.load("xgb_model.pkl")
scaler = joblib.load("scaler.pkl")
ann_model = load_model("ann_model.keras")

THRESHOLD = 0.6
EXPECTED_FEATURES = scaler.n_features_in_

# ==================================================
# URL NORMALIZATION (IMPORTANT)
# ==================================================
def normalize_url(url):
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip("/")

# ==================================================
# Database Setup
# ==================================================
def init_db():
    conn = sqlite3.connect("phishing_results.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        xgb_prob REAL,
        ann_prob REAL,
        hybrid_prob REAL,
        prediction TEXT,
        created_at TEXT
    )
    """)

    # 🔥 Index for fast lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON results(url)")

    conn.commit()
    conn.close()


def save_result(url, xgb, ann, hybrid, prediction):
    conn = sqlite3.connect("phishing_results.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO results (url, xgb_prob, ann_prob, hybrid_prob, prediction, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (url, float(xgb), float(ann), float(hybrid), prediction, datetime.now()))

    conn.commit()
    conn.close()


def get_cached_result(url):
    conn = sqlite3.connect("phishing_results.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT prediction, hybrid_prob 
    FROM results 
    WHERE url = ?
    ORDER BY id DESC LIMIT 1
    """, (url,))

    row = cursor.fetchone()
    conn.close()

    return row  # None or (prediction, score)


init_db()

# ==================================================
# Feature Extraction
# ==================================================
def extract_features(url):

    features = []

    features.append(1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0)
    features.append(1 if len(url) > 75 else 0)
    features.append(1 if re.search(r'bit\.ly|tinyurl|goo\.gl', url) else 0)
    features.append(1 if "@" in url else 0)
    features.append(1 if urlparse(url).path.count("//") > 0 else 0)
    features.append(1 if "-" in urlparse(url).netloc else 0)
    features.append(1 if urlparse(url).netloc.count(".") > 2 else 0)
    features.append(1 if url.startswith("https") else 0)
    features.append(1 if re.search(r'login|secure|bank|verify|free|update', url.lower()) else 0)

    while len(features) < EXPECTED_FEATURES:
        features.append(0)

    return features


# ==================================================
# HTML Page
# ==================================================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Phishing Website Detection</title>

<style>
body{
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #e2e8f0;
    padding: 40px;
}

.box{
    background: #111827;
    width: 420px;
    margin: auto;
    padding: 35px;
    border-radius: 16px;
    box-shadow: 0 0 30px rgba(0,0,0,0.6);
    text-align: center;
}

h2{
    margin-bottom: 20px;
    color: #38bdf8;
}

input{
    width: 100%;
    padding: 12px;
    margin-top: 15px;
    border-radius: 8px;
    border: none;
    background: #1f2937;
    color: white;
    outline: none;
}

input::placeholder{
    color: #94a3b8;
}

button{
    width: 100%;
    padding: 12px;
    margin-top: 15px;
    border-radius: 8px;
    border: none;
    background: #3b82f6;
    color: white;
    font-weight: bold;
    cursor: pointer;
    transition: 0.3s;
}

button:hover{
    background: #2563eb;
    transform: scale(1.03);
}

.history-btn{
    background: #22c55e;
}

.history-btn:hover{
    background: #16a34a;
}

.result{
    margin-top: 25px;
    padding: 15px;
    border-radius: 10px;
    font-size: 18px;
}

.phishing{
    background: rgba(239,68,68,0.2);
    color: #ef4444;
}

.legitimate{
    background: rgba(34,197,94,0.2);
    color: #22c55e;
}

.url-text{
    font-size: 12px;
    color: #94a3b8;
    margin-top: 5px;
    word-break: break-all;
}

</style>
</head>

<body>

<div class="box">
    <h2>🔍 Phishing Detection</h2>

    <form method="post">
        <input type="text" name="url" placeholder="Enter website URL..." required>
        <button type="submit">Check Website</button>
    </form>

    <a href="/history">
        <button class="history-btn">View History</button>
    </a>

    {% if result %}
    <div class="result {{ css_class }}">
        <strong>{{ result }}</strong>
        <div class="url-text">{{ url }}</div>
    </div>
    {% endif %}
</div>

</body>
</html>
"""

# ==================================================
# Home Page
# ==================================================
@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    css_class = ""
    url = ""

    if request.method == "POST":

        url = normalize_url(request.form["url"].strip())

        # 🔥 CHECK CACHE FIRST
        cached = get_cached_result(url)

        if cached:
            prediction, hybrid_prob = cached
            print("⚡ CACHE HIT (WEB):", url)
        else:
            print("🧠 RUN MODEL (WEB):", url)

            features = extract_features(url)
            features = np.array(features).reshape(1, -1)
            features = scaler.transform(features)

            xgb_prob = xgb_model.predict_proba(features)[:,1][0]
            ann_prob = ann_model.predict(features, verbose=0).ravel()[0]

            hybrid_prob = 0.5 * xgb_prob + 0.5 * ann_prob

            prediction = "phishing" if hybrid_prob >= THRESHOLD else "legitimate"

            save_result(url, xgb_prob, ann_prob, hybrid_prob, prediction)

        if prediction == "phishing":
            result = "🚨 PHISHING WEBSITE"
            css_class = "phishing"
        else:
            result = "✅ LEGITIMATE WEBSITE"
            css_class = "legitimate"

    return render_template_string(
        HTML_PAGE,
        result=result,
        css_class=css_class,
        url=url
    )

# ==================================================
# Browser Extension API
# ==================================================
@app.route("/api/check", methods=["POST"])
def api_check():

    data = request.json
    url = normalize_url(data.get("url"))

    # 🔥 1. CHECK DATABASE
    cached = get_cached_result(url)

    if cached:
        prediction, score = cached

        print("⚡ CACHE HIT:", url)

        return jsonify({
            "url": url,
            "prediction": prediction,
            "score": float(score),
            "cached": True
        })

    # 🔥 2. RUN MODEL
    print("🧠 RUNNING MODEL:", url)

    features = extract_features(url)
    features = np.array(features).reshape(1, -1)
    features = scaler.transform(features)

    xgb_prob = xgb_model.predict_proba(features)[:,1][0]
    ann_prob = ann_model.predict(features, verbose=0).ravel()[0]

    hybrid_prob = 0.5 * xgb_prob + 0.5 * ann_prob

    prediction = "phishing" if hybrid_prob >= THRESHOLD else "legitimate"

    # 🔥 3. SAVE RESULT
    save_result(url, xgb_prob, ann_prob, hybrid_prob, prediction)

    return jsonify({
        "url": url,
        "prediction": prediction,
        "score": float(hybrid_prob),
        "cached": False
    })

# ==================================================
# History Page
# ==================================================
@app.route("/history")
def history():

    conn = sqlite3.connect("phishing_results.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM results ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()

    return render_template_string("""
<html>
<head>
<title>Detection History</title>
<style>
body{font-family:Arial;padding:40px;background:#f4f6f9;}
table{border-collapse:collapse;width:100%;background:white;}
th,td{padding:12px;border:1px solid #ddd;text-align:center;}
th{background:#007bff;color:white;}
tr:nth-child(even){background:#f2f2f2;}
</style>
</head>

<body>

<h2>Phishing Detection History</h2>

<table>
<tr>
<th>ID</th>
<th>URL</th>
<th>XGB</th>
<th>ANN</th>
<th>Hybrid</th>
<th>Prediction</th>
<th>Time</th>
</tr>

{% for row in rows %}
<tr>
<td>{{row[0]}}</td>
<td>{{row[1]}}</td>
<td>{{"%.3f"|format(row[2])}}</td>
<td>{{"%.3f"|format(row[3])}}</td>
<td>{{"%.3f"|format(row[4])}}</td>
<td>{{row[5]}}</td>
<td>{{row[6]}}</td>
</tr>
{% endfor %}

</table>

</body>
</html>
""", rows=rows)

# ==================================================
# Run Server
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)