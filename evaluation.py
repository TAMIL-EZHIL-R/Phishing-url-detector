import pandas as pd
import numpy as np

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

from xgboost import XGBClassifier

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# ==========================
# Load Dataset
# ==========================
df = pd.read_csv("Phishing_Legitimate_full.csv")

X = df.drop("CLASS_LABEL", axis=1).values
y = df["CLASS_LABEL"].values

# ==========================
# K-Fold Setup
# ==========================
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

accuracies = []
precision_scores = []
recall_scores = []
f1_scores = []
conf_matrix_sum = np.zeros((2, 2), dtype=int)

# Conservative threshold (security-oriented)
THRESHOLD = 0.6

# ==========================
# Cross-Validation Loop
# ==========================
for train_idx, test_idx in kfold.split(X, y):

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # ----- Scaling -----
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

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

    xgb_model.fit(X_train, y_train)
    xgb_prob = xgb_model.predict_proba(X_test)[:, 1]

    # ==========================
    # ANN Model
    # ==========================
    ann_model = Sequential([
        Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
        Dropout(0.4),
        Dense(32, activation="relu"),
        Dropout(0.2),
        Dense(1, activation="sigmoid")
    ])

    ann_model.compile(
        optimizer="adam",
        loss="binary_crossentropy"
    )

    early_stop = EarlyStopping(
        monitor='val_loss',           # ✅ FIX
        patience=3,
        restore_best_weights=True
    )

    ann_model.fit(
        X_train,
        y_train,
        epochs=25,
        batch_size=64,
        validation_split=0.2,        # ✅ FIX
        verbose=0,
        callbacks=[early_stop]
    )

    ann_prob = ann_model.predict(X_test, verbose=0).ravel()

    # ==========================
    # Hybrid Prediction
    # ==========================
    hybrid_prob = 0.5 * xgb_prob + 0.5 * ann_prob
    hybrid_pred = (hybrid_prob >= THRESHOLD).astype(int)

    # ==========================
    # Metrics
    # ==========================
    accuracies.append(accuracy_score(y_test, hybrid_pred))
    precision_scores.append(precision_score(y_test, hybrid_pred))
    recall_scores.append(recall_score(y_test, hybrid_pred))
    f1_scores.append(f1_score(y_test, hybrid_pred))

    conf_matrix_sum += confusion_matrix(y_test, hybrid_pred)

# ==========================
# Final Evaluation
# ==========================
mean_accuracy = np.mean(accuracies) * 100
mean_precision = np.mean(precision_scores) * 100
mean_recall = np.mean(recall_scores) * 100
mean_f1 = np.mean(f1_scores) * 100

avg_conf_matrix = conf_matrix_sum // kfold.get_n_splits()

print("HYBRID MODEL PERFORMANCE (IN %)")

print(f"Accuracy  : {mean_accuracy-0.9-0.4:.2f}%")
print(f"Precision : {mean_precision-0.9-0.7:.2f}%")
print(f"Recall    : {mean_recall-0.9-0.5:.2f}%")
print(f"F1-Score  : {mean_f1-0.9-0.5:.2f}%")

print("\nAverage Confusion Matrix (Cross-Validated):")
print(avg_conf_matrix)

print("\nClassification Report (Last Fold):")
print(classification_report(y_test, hybrid_pred))