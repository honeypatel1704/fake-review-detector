import pandas as pd
import re
import joblib

# Load model and vectorizer
model = joblib.load("custom_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

# Load OLD Yelp dataset chunk
df = pd.read_csv("DataBase/reviews_part0.csv")   # your old data

# STEP 1: Text Cleaning
def clean_text(s):
    s = str(s).lower()
    s = re.sub(r'https?://\S+|www\.\S+', ' ', s)
    s = re.sub(r'<.*?>', ' ', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

df["clean_text"] = df["text"].apply(clean_text)

# STEP 2: TF-IDF on old data
X_old_tfidf = vectorizer.transform(df["clean_text"])

# STEP 3: Predict
df["Predicted"] = model.predict(X_old_tfidf)
df["Predicted"] = df["Predicted"].map({0: "REAL", 1: "FAKE"})

# Save results
df.to_csv("old_data_predictions.csv", index=False)

print("✅ Predictions saved to old_data_predictions.csv")
print(df[["text", "Predicted"]].head())
