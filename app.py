import os
import uuid

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "csv-cleaner-development-key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file selected.")
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Only CSV files are allowed.")
        return redirect(url_for("index"))

    unique_name = f"{uuid.uuid4().hex}.csv"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

    file.save(filepath)

    try:
        df = pd.read_csv(filepath)

        analysis = {
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "empty_columns": int(
                df.columns[df.isna().all()].shape[0]
            ),
            "column_data": [],
        }

        for column in df.columns:
            analysis["column_data"].append({
                "name": column,
                "dtype": str(df[column].dtype),
                "missing": int(df[column].isna().sum()),
                "unique": int(df[column].nunique(dropna=True)),
            })

        return render_template(
            "analysis.html",
            analysis=analysis
        )

    except Exception as error:
        if os.path.exists(filepath):
            os.remove(filepath)

        flash(f"Could not read CSV file: {error}")
        return redirect(url_for("index"))


@app.errorhandler(413)
def file_too_large(error):
    flash("File is too large. Maximum size is 50 MB.")
    return redirect(url_for("index"))


if __name__ == "main":
    app.run(debug=True)