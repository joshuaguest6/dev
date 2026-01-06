from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pandas as pd

import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from google.auth import default
from google.cloud import storage
import io
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

gsheet = 'Web Scraper Output'
sheet_name = "data2"

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])



def main(request):
    print("Starting main function")
    r = requests.post(
        'https://tjapi.timesjobs.com/search/api/v1/search/jobs/list',
        json={
            'company': "",
            'experience': "",
            'functionAreaId': "",
            'industry': "",
            'jobFunction': "",
            'jobFunctions': [],
            'keyword': "\"python\",\"Data Analyzing\",",
            'location': "",
            'page': "2",
            'size': "10"
        },
        headers=(
            {"User-Agent": "Mozilla/5.0"}
        )
    )

    data = r.json()

    i = 1
    cutoff_date = (datetime.now() - timedelta(days=1)).date()
    new_data = []
    for job in data['jobs']:
        post_date = datetime.strptime(job['postDate'], '%Y-%m-%d').date()
        if post_date >= cutoff_date:
            print(f"""
                {i}: Position: {job['title']} 
                    Skills: {job['skills']}
                    Company: {job['company']} 
                    Post date: {job['postDate']}""")
            i += 1

            new_data.append({
                'title': job['title'],
                'skills': job['skills'],
                'company': job['company'],
                'post date': job['postDate']
            }
            )

    df = pd.DataFrame(new_data)

    ### TO GOOGLE SHEETS ###

    creds, project = default(scopes=scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open(gsheet)
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(
            sheet_name, 
            cols=20, 
            rows=1000
            )

    set_with_dataframe(sheet, df)

    ### SAVE LOGS TO GCS ###
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    client_gcs = storage.Client()
    bucket = client_gcs.bucket("web-scraper-logs-prod")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    blob = bucket.blob(f"scraper_run_{timestamp}.csv")

    blob.upload_from_string(csv_data, content_type="text/csv")
    print(f"Scraped {len(df)} rows and uploaded to GCS")

    message = Mail(
        from_email="joshuaguest6@gmail.com",
        to_emails="joshyguest@gmail.com",
        subject="Successful Run",
        plain_text_content=f"{len(df)} records were uploaded to {sheet_name} tab in {gsheet} google sheet at {timestamp}"
    )
    
    response = sg.send(message)
    print(response.status_code)

    print("Main function finished!")

    return "Scraper run completed successfully", 200

if __name__ == "__main__":
    print("Running locally")
    main(None)