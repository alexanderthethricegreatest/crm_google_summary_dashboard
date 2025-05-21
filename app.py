from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
SHEET_NAME = "Prospects2"

FIELDS = [
    "Name", "Phone", "Email", "Address", "City", "State", "Zip", "Country",
    "Last Contacted", "Next Step", "Status", "Notes"
]

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gsheet_creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

def load_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_data(df):
    sheet = get_sheet()
    sheet.clear()
    sheet.update([df.columns.tolist()] + df.values.tolist())

@app.route("/", methods=["GET", "POST"])
def index():
    df = load_data()

    if request.method == "POST":
        new_entry = {field: request.form.get(field.lower().replace(" ", "_"), "") for field in FIELDS}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        return redirect(url_for("index"))

    query = request.args.get("q", "").lower()
    if query:
        df = df[df.apply(lambda row: query in str(row.values).lower(), axis=1)]

    return render_template("index.html", data=df.to_dict(orient="records"), columns=FIELDS)

@app.route("/dashboard")
def dashboard():
    df = load_data()
    total_leads = len(df)
    closed_leads = df["Status"].str.lower().eq("closed").sum()
    open_leads = total_leads - closed_leads

    pie_data = {
        "labels": ["Closed", "Open"],
        "values": [int(closed_leads), int(open_leads)]
    }

    return render_template("dashboard.html", total=total_leads, closed=closed_leads, pie_data=pie_data)

@app.route("/delete/<int:index>")
def delete(index):
    df = load_data()
    df = df.drop(index).reset_index(drop=True)
    save_data(df)
    return redirect(url_for("index"))
