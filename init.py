from flask import Flask, render_template, request, redirect, flash
import os

app = Flask(__name__)

FLASK_ENV = os.getenv('FLASK_ENV', None)

cwd = app.instance_path.replace('instance','')[:-1]

print(f"current working directory: {cwd}")
print(f"flask environment: {FLASK_ENV}")
print(f"current working directory: {cwd}")
app.config.from_object("config.ProductionConfig")

app.config["PDF_UPLOADS"] = f"{cwd}/static/uploads"
app.config["ALLOWED_FILE_EXT"] = ["PDF", "TXT"]
app.config["MAX_FILESIZE"] = 5 * 1024 * 1024#bytes (~5MB)
