import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

# STEP 1: Load custom dataset
df = pd.read_csv("DataBase/custom_reviews_200.csv")   # <-- FIXED PATH

# STEP 2: Clean text
def clean_text(s):
    s = s.lower()
    s = re.sub(r'https?://\S+|www\.\S+', ' ', s)
    s = re.sub(r'<.*?>', ' ', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

df["clean_text"] = df["text"].apply(clean_text)

# STEP 3: Split data
X_train, X_test, y_train, y_test = train_test_split(
    df["clean_text"], df["label"],
    test_size=0.2, random_state=42, stratify=df["label"]
)

# STEP 4: TF-IDF Vectorization
vectorizer = TfidfVectorizer(max_features=1000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# STEP 5: Train Logistic Regression model
model = LogisticRegression(max_iter=3000, random_state=42)
model.fit(X_train_tfidf, y_train)

# STEP 6: Evaluate model
y_pred = model.predict(X_test_tfidf)

print("✅ Model Trained Successfully!")
print(f"Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# STEP 7: Save model + vectorizer
joblib.dump(model, "custom_model.pkl")
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")

print("\n💾 Model and Vectorizer Saved Successfully!")
