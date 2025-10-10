import re
import string
import nltk
import spacy
from textblob import TextBlob
from nltk.corpus import stopwords

# Download stopwords (run only once)
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    # 1. Lowercase
    text = text.lower()

    # 2. Remove URLs and HTML
    text = re.sub(r'http\S+|www\S+|<.*?>', '', text)

    # 3. Remove numbers and punctuation
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))

    # 4. Spell Correction using TextBlob
    text = str(TextBlob(text).correct())

    # 5. Tokenization & Lemmatization using spaCy
    doc = nlp(text)
    tokens = []
    for token in doc:
        if token.lemma_ not in stop_words and not token.is_punct and not token.is_space:
            tokens.append(token.lemma_)

    # 6. Join tokens back into a string
    cleaned_text = ' '.join(tokens)

    return cleaned_text
