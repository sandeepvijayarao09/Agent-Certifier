"""Deliberately insecure support agent, used to demo Agent Certifier.

Do not copy any of this. Every pattern below is something the analyzers
should flag: a hardcoded credential, prompt injection via string
formatting, executing model output, shell and SQL injection, and unsafe
deserialization. The credential is a fake placeholder.
"""
import os
import pickle
import sqlite3

import requests

PASSWORD = "hunter2-not-real"
ADMIN_TOKEN = "EXAMPLEtokenEXAMPLEtoken0000"


def call_llm(prompt):
    return requests.post("http://llm.internal/v1/complete", json={"prompt": prompt}).json()["text"]


def handle(user_input):
    prompt = f"You are a helpful support bot. Follow this instruction: {user_input}"
    reply = call_llm(prompt)
    exec(reply)
    os.system("echo " + user_input + " >> /tmp/support.log")
    return eval(user_input)


def lookup_customer(name):
    conn = sqlite3.connect("customers.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE name = '" + name + "'")
    return cur.fetchall()


def restore_session(blob):
    return pickle.loads(blob)


while True:
    handle(input("> "))
