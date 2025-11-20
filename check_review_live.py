import re
import joblib

# Load saved model and vectorizer
model = joblib.load("custom_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

def clean_text(s):
    s = s.lower()
    s = re.sub(r'https?://\S+|www\.\S+', ' ', s)
    s = re.sub(r'<.*?>', ' ', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

print("\n🤖 FAKE REVIEW DETECTOR READY")
print("----------------------------------")

while True:
    text = input("\nEnter a review (or 'exit' to stop): ")

    if text.lower() == "exit":
        print("\n👋 Exiting Fake Review Detector...")
        break

    clean = clean_text(text)
    X = vectorizer.transform([clean])
    prediction = model.predict(X)[0]

    if prediction == 1:
        print("🚨 This review is likely *FAKE*! ")
    else:
        print("✅ This review seems *REAL*. ")
