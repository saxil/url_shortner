from flask import Flask, render_template, request, redirect, url_for
import hashlib
import sqlite3
import sys

app = Flask(__name__)

DATABASE_FILE = "url_shortener.db"

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            short_url TEXT PRIMARY KEY,
            original_url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def shorten_url(original_url):
    create_database()
    hash_object = hashlib.md5(original_url.encode())
    short_url = hash_object.hexdigest()[:8]

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO urls (short_url, original_url) VALUES (?, ?)", (short_url, original_url))
        conn.commit()
        return short_url
    except sqlite3.IntegrityError:
        cursor.execute("SELECT short_url FROM urls WHERE original_url = ?", (original_url,))
        existing_short_url = cursor.fetchone()[0]
        return existing_short_url
    finally:
        conn.close()

def unshorten_url(short_url):
    create_database()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT original_url FROM urls WHERE short_url = ?", (short_url,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form["original_url"]
        shortened_url = shorten_url(original_url)
        if shortened_url:
            shortened_link = request.host_url + shortened_url
            return render_template("index.html", shortened_link=shortened_link)
        else:
            return render_template("index.html", error="Error shortening URL.")
    return render_template("index.html")

@app.route("/<short_url>")
def redirect_url(short_url):
    original_url = unshorten_url(short_url)
    if original_url:
        return redirect(original_url)
    else:
        return render_template("404.html"), 404

@app.route("/unshorten", methods=["POST"])
def unshorten():
    short_url = request.form["short_url"]
    original_url = unshorten_url(short_url)
    if original_url:
        return render_template("index.html", unshortened_link=original_url)
    else:
        return render_template("index.html", error="Shortened URL not found.")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def cli_main():
    while True:
        print("\nURL Shortener/Unshortener CLI")
        print("1. Shorten URL")
        print("2. Unshorten URL")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            original_url = input("Enter the original URL: ")
            shortened_url = shorten_url(original_url)
            if shortened_url:
                print(f"Shortened URL: {shortened_url}")
            else:
                print("Error shortening URL.")

        elif choice == "2":
            short_url = input("Enter the shortened URL: ")
            original_url = unshorten_url(short_url)
            if original_url:
                print(f"Original URL: {original_url}")
            else:
                print("Shortened URL not found.")

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_main()
    else:
        app.run(debug=True)