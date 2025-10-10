from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
from text_cleaner import preprocess_text
from textblob import TextBlob

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------- NEWS FETCH FUNCTION --------------------
API_KEY = "Your API key"  # 🔹 replace with your NewsAPI key

def fetch_news(query=None, language='en', page_size=5):
    # If query exists → search everything, else show top headlines
    if query:
        url = f'https://newsapi.org/v2/everything?q={query}&language={language}&pageSize={page_size}&apiKey={API_KEY}'
    else:
        url = f'https://newsapi.org/v2/top-headlines?country=in&pageSize={page_size}&apiKey={API_KEY}'

    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get('articles', [])
        results = []
        for article in articles:
            news_item = {
                "title": article.get('title'),
                "source": article.get('source', {}).get('name'),
                "publishedAt": article.get('publishedAt'),
                "url": article.get('url'),
                "description": article.get('description'),
                "image": article.get('urlToImage')
            }
            results.append(news_item)
        return results
    else:
        print(f"Error fetching news: {response.status_code}")
        return []

# -------------------- USER AUTH --------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect("/login")
        except:
            return "⚠️ Username already exists!"
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/dashboard")
        else:
            return "❌ Invalid username or password!"
    return render_template("login.html")

from textblob import TextBlob
from text_cleaner import preprocess_text

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect("/login")

    query = None
    corrected_query = None
    news_items = []

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        page_size = int(request.form.get("page_size", 5))

        #  Auto-correct using TextBlob
        blob = TextBlob(query)
        corrected_query = str(blob.correct()).strip()

        print(f"Original: {query} → Corrected: {corrected_query}")

        #  If correction is weird, fallback to original
        if not corrected_query or corrected_query.lower() == "i":
            corrected_query = query

        #  Use the corrected query for fetching news
        news_items = fetch_news(corrected_query, page_size=page_size)

    else:
        corrected_query = "latest"
        news_items = fetch_news(corrected_query, page_size=5)

    #  Clean descriptions
    for news in news_items:
        desc = news.get("description")
        news["clean_description"] = preprocess_text(desc) if desc else "No description available."

    return render_template(
        "dashboard.html",
        news=news_items,
        user=session["username"],
        query=query,
        corrected_query=corrected_query
    )


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)
