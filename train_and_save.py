import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

# ==========================
# Load Dataset
# ==========================
df = pd.read_csv("Phishing_Legitimate_full.csv")

X = df.drop("CLASS_LABEL", axis=1).values
y = df["CLASS_LABEL"].values

# ==========================
# Scaling
# ==========================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==========================
# XGBoost Model
# ==========================
xgb_model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.75,
    colsample_bytree=0.75,
    eval_metric="logloss",
    random_state=42
)

xgb_model.fit(X_scaled, y)

# ==========================
# ANN Model
# ==========================
ann_model = Sequential([
    Dense(64, activation="relu", input_shape=(X_scaled.shape[1],)),
    Dropout(0.4),
    Dense(32, activation="relu"),
    Dropout(0.2),
    Dense(1, activation="sigmoid")
])

ann_model.compile(
    optimizer="adam",
    loss="binary_crossentropy"
)

ann_model.fit(
    X_scaled,
    y,
    epochs=10,
    batch_size=64,
    verbose=0
)

# ==========================
# Save Models (CORRECT WAY)
# ==========================
joblib.dump(xgb_model, "xgb_model.pkl")
joblib.dump(scaler, "scaler.pkl")

# 🔥 IMPORTANT FIX HERE
ann_model.save("ann_model.keras")

print("✅ Models saved successfully")
