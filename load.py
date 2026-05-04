import pandas as pd

df = pd.read_csv("Phishing_Legitimate_full.csv")

print("Shape:", df.shape)
print("\nColumn names:")
print(df.columns)

print("\nClass distribution:")
print(df["CLASS_LABEL"].value_counts())

print("\nMissing values:")
print(df.isnull().sum().sum())
