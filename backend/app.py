
from flask import Flask, jsonify
import os
import psycopg2

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "projectdb"),
        user=os.getenv("DB_USER", "admin"),
        password=os.environ["DB_PASSWORD"]
    )

@app.route("/")
def home():
    return jsonify({
        "message": "Kubernetes Multi-Tier Application - Version 3",
        "status": "Backend is running"
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/ready")
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ready"}), 200

    except Exception:
        return jsonify({"status": "not_ready"}), 503

        
@app.route("/data")
def get_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL
            )
        """)

        conn.commit()

        cur.execute("SELECT id, message FROM test_data ORDER BY id")
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify([
            {"id": row[0], "message": row[1]}
            for row in rows
        ])

    except Exception as error:
        return jsonify({"error": str(error)}), 503

@app.route("/add/<message>")
def add_data(message):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS test_data (id SERIAL PRIMARY KEY, message TEXT NOT NULL)"
        )

        cur.execute(
            "INSERT INTO test_data (message) VALUES (%s) RETURNING id",
            (message,)
        )

        new_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "id": new_id,
            "message": message,
            "status": "saved"
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
