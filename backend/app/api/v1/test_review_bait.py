"""Temporary file to verify Claude Code Review action posts comments. Delete after verification."""

import os
import sqlite3


def unsafe_query(user_input):
    """SQL injection vulnerability - should trigger review comment."""
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")
    return cursor.fetchall()


def hardcoded_secret():
    """Hardcoded credentials - should trigger review comment."""
    api_key = "sk-ant-api03-FAKE-KEY-FOR-TESTING-ONLY"
    password = "admin123"
    return api_key, password


def unreachable_code():
    """Dead code after return - should trigger review comment."""
    return True
    print("this never runs")
    x = 1 + 2


def no_error_handling():
    """Missing error handling - should trigger review comment."""
    data = open("/etc/passwd").read()
    result = int(data)
    return result / 0
