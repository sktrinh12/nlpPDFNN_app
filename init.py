from flask import Flask, render_template, request, redirect, flash
import os

app = Flask(__name__)

FLASK_ENV = os.getenv('FLASK_ENV', None)
app.secret_key = os.urandom(14)
cwd = app.instance_path.replace('instance','')[:-1]

print("="*30)
print(f"current working directory: {cwd}")
print(f"flask environment: {FLASK_ENV}")
print(f"current working directory: {cwd}")
print("="*30)

app.config["PDF_UPLOADS"] = f"{cwd}/static/uploads"
app.config["ALLOWED_FILE_EXT"] = ["PDF", "TXT"]
app.config["MAX_FILESIZE"] = 5 * 1024 * 1024#bytes (~5MB)
