from functools import wraps
from flask import request, jsonify
from collections import defaultdict, deque
import time

# Simple in-memory rate limiter
_buckets = defaultdict(deque)


def rate_limit(key_func, limit=5, window=60):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = key_func() if callable(key_func) else str(key_func)
            now = time.time()
            bucket = _buckets[key]
            while bucket and bucket[0] < now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                if request.is_json or request.path.startswith("/api"):
                    return jsonify({"error": "Too many requests"}), 429
                from flask import flash, redirect, url_for
                flash("Too many attempts. Please try again later.", "danger")
                return redirect(url_for("auth.login"))
            bucket.append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator
