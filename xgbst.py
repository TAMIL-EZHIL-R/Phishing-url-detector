import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt

# Convert data to DMatrix (XGBoost optimized format)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# XGBoost parameters (tuned for phishing detection)
params = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "max_depth": 6,
    "eta": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "seed": 42
}

# Train model
xgb_model = xgb.train(
    params,
    dtrain,
    num_boost_round=300
)

# Predictions
y_pred_prob = xgb_model.predict(dtest)
y_pred = (y_pred_prob > 0.5).astype(int)

# Evaluation
acc = accuracy_score(y_test, y_pred)
print("\nXGBoost Accuracy:", acc)

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# Feature importance plot
xgb.plot_importance(xgb_model, max_num_features=15)
plt.title("Top 15 Feature Importances (XGBoost)")
plt.show()
