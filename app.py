from flask import Flask, render_template, request, redirect
import mysql.connector
import requests

app = Flask(__name__)

# --- Connect to MySQL database ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="736251",
    database="MoodJournal"
)
cursor = db.cursor(dictionary=True)

# --- Hugging Face API ---
HF_API_KEY = "your_huggingface_api_key"
HF_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

def analyze_sentiment(text):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text}
    response = requests.post(HF_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()[0][0]
        label = result['label']
        score = round(result['score'] * 100, 2)
        return f"{label} ({score}%)"
    else:
        return "could not analyze"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form["entry"]
        mood = analyze_sentiment(text)

        cursor.execute(
            "INSERT INTO entries (mood, text, created_at) VALUES (%s, %s, NOW())",
            (mood, text)
        )
        db.commit()
        return redirect("/")

    cursor.execute("SELECT * FROM entries ORDER BY created_at DESC")
    entries = cursor.fetchall()
    return render_template("index.html", entries=entries)


# --- Update entry ---
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    text = request.form["entry"]
    mood = analyze_sentiment(text)

    cursor.execute(
        "UPDATE entries SET text=%s, mood=%s WHERE id=%s",
        (text, mood, id)
    )
    db.commit()
    return redirect("/")


# --- Delete entry ---
@app.route("/delete/<int:id>")
def delete(id):
    cursor.execute("DELETE FROM entries WHERE id=%s", (id,))
    db.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)


@app.route("/success")
def success():
    return "Payment successful! Thank you."

import stripe

stripe.api_key = "your_stripe_secret_key"

@app.route("/checkout", methods=["POST"])
def checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Mood Journal Premium"},
                "unit_amount": 500,  # in cents ($5.00)
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:5000/success",
        cancel_url="http://localhost:5000/cancel",
    )
    return redirect(session.url, code=303)


@app.route("/cancel")
def cancel():
    return "Payment canceled."

