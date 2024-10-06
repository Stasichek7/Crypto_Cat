from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import random
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect('crypto_cat.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''DROP TABLE IF EXISTS user_scores''')  
        conn.execute('''CREATE TABLE IF NOT EXISTS user_scores (
            username TEXT PRIMARY KEY, 
            score INTEGER DEFAULT 0,
            referral_code TEXT
        )''')
        conn.commit()

init_db()

class User(BaseModel):
    username: str

def generate_referral_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def assign_referral_codes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM user_scores WHERE referral_code IS NULL")
        users_without_codes = cursor.fetchall()

        for user in users_without_codes:
            while True:
                referral_code = generate_referral_code()
                cursor.execute("SELECT username FROM user_scores WHERE referral_code = ?", (referral_code,))
                if cursor.fetchone() is None:
                    break  # Код унікальний, можна використовувати

            cursor.execute("UPDATE user_scores SET referral_code = ? WHERE username = ?", 
                           (referral_code, user['username']))

        conn.commit()

@app.post("/tap1")
async def tap1(user: User):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM user_scores WHERE username = ?", (user.username,))
        row = cursor.fetchone()

        if row:
            new_score = row[0] + 1
            cursor.execute("UPDATE user_scores SET score = ? WHERE username = ?", (new_score, user.username))
        else:
            new_score = 1
            cursor.execute("INSERT INTO user_scores (username, score) VALUES (?, ?)", (user.username, new_score))

        conn.commit()

    return {
        "message": f"Added 1 point to {user.username}. Total: {new_score}",
    }

@app.post("/tap2")
async def tap2(user: User):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM user_scores WHERE username = ?", (user.username,))
        row = cursor.fetchone()

        if row:
            new_score = row[0] - 1
            cursor.execute("UPDATE user_scores SET score = ? WHERE username = ?", (new_score, user.username))
        else:
            new_score = -1
            cursor.execute("INSERT INTO user_scores (username, score) VALUES (?, ?)", 
                           (user.username, new_score))

        conn.commit()

    return {
        "message": f"Subtracted 1 point from {user.username}. Total: {new_score}",
    }

@app.get("/score/{username}")
def get_score(username: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score, referral_code FROM user_scores WHERE username = ?", (username,))
        row = cursor.fetchone()

    if row:
        return {
            "score": row['score'],
            "referral_code": row['referral_code']  
        }
    else:
        return {"score": 0, "referral_code": None}

@app.get("/leaderboard")
async def leaderboard() -> List[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, score FROM user_scores ORDER BY score DESC LIMIT 10")
        rows = cursor.fetchall()

    leaderboard = [{"username": row["username"], "score": row["score"]} for row in rows]
    return leaderboard

assign_referral_codes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
