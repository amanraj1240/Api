from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

# ==================== CONFIG =====================
YOUR_API_KEYS = ["ERROR"]     # Access key
CACHE_TIME = 3600             # 1 hour cache
# ================================================

cache = {}

def clean_text(value):
    if isinstance(value, str):
        return value.replace("@Gaurav_Cyber", "").strip()
    if isinstance(value, list):
        return [clean_text(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_text(v) for k, v in value.items()}
    return value


def remove_credit_fields(obj):
    if isinstance(obj, dict):
        return {
            k: remove_credit_fields(v)
            for k, v in obj.items()
            if k.lower() not in (
                "credit", "credits", "credit_by",
                "developer", "powered_by"
            )
        }
    if isinstance(obj, list):
        return [remove_credit_fields(i) for i in obj]
    return obj


@app.route("/", methods=["GET"])
def number_api():
    num = request.args.get("num")
    key = request.args.get("key")

    if not num or not key:
        return jsonify({
            "error": "missing parameters",
            "usage": "?num=Number&key=ERROR"
        }), 400

    if key not in YOUR_API_KEYS:
        return jsonify({"error": "invalid key"}), 403

    number = "".join(filter(str.isdigit, num))
    if len(number) < 10:
        return jsonify({"error": "invalid number"}), 400

    # 🔹 Cache check
    if number in cache and time.time() - cache[number]["time"] < CACHE_TIME:
        return jsonify(cache[number]["data"])

    try:
        # 🔥 NEW RAVAN LOOKUP API
        response = requests.get(
            "https://ravan-lookup.vercel.app/api",
            params={
                "key": "Ravan",
                "type": "mobile",
                "term": number
            },
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({"error": "upstream failed"}), 502

        data = response.json()

        data = clean_text(data)
        data = remove_credit_fields(data)

        # ✅ DEVELOPER & BRANDING (UPDATED)
        data["developer"] = "@urslash"
        data["powered_by"] = "urslash-number-api"

        cache[number] = {
            "time": time.time(),
            "data": data
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": "request failed",
            "details": str(e)
        }), 500


# 🔥 VERCEL ENTRY POINT (DO NOT CHANGE)
handler = app
