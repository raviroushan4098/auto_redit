import praw
import re
import time
import requests
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Hugging Face Sentiment model
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
labels = ['negative', 'neutral', 'positive']

# VADER (optional, not used here)
nltk.download('vader_lexicon')
vader = SentimentIntensityAnalyzer()

# Telegram Bot Settings
BOT_TOKEN = "7578392618:AAHFChJlanc1ngso-0UoGdwUbhxqeOH0onw"
CHAT_ID = "-1002627483096"

# Sentiment Analyzer
def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    scores = torch.nn.functional.softmax(logits, dim=1)[0]
    top_class = torch.argmax(scores).item()
    return labels[top_class]

# Relevance Checker
def is_relevant(text):
    text = text.lower()
    return (
        "lpu" in text and
        not re.search(r'linkin\s*park|lp\s+tour|lpu\s+membership', text)
    )

# Telegram Messenger
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

# Reddit API Setup
reddit = praw.Reddit(
    client_id="1FbDSYQTnnwwaz-IMbCUOQ",
    client_secret="c4S3AJFuzktQZGxJglpJ2o_27rsx0g",
    user_agent="LPU_Searcher by u/Different_Case_9578"
)

# Store seen posts (titles)
seen_negative_titles = set()

# Main loop
def run_monitor():
    while True:
        new_negative_posts = []
        for submission in reddit.subreddit("all").search("LPU", sort="new", limit=100):
            title = submission.title
            if is_relevant(title):
                sentiment = get_sentiment(title)
                if sentiment == "negative" and title not in seen_negative_titles:
                    seen_negative_titles.add(title)
                    new_negative_posts.append({
                        "title": title,
                        "url": submission.url,
                        "subreddit": submission.subreddit.display_name,
                        "score": submission.score,
                        "comments": submission.num_comments
                    })

        if new_negative_posts:
            for post in new_negative_posts:
                message = (
                    f"🚨 NEGATIVE POST FOUND\n"
                    f"[{post['title']}]\n"
                    f"r/{post['subreddit']} | 👍 {post['score']} 💬 {post['comments']}\n"
                    f"🔗 {post['url']}"
                )
                send_telegram_message(message)
        else:
            send_telegram_message("✅ All OK, no negative post found.")

        time.sleep(300)  # wait 1 minute

# Run
if __name__ == "__main__":
    run_monitor()
