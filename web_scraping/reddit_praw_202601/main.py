import praw
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from google.auth import default

# google sheet
gsheet = 'Reddit Scrape'
sheet_name = 'data'

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]


# Subreddits to search and keywords to match
search_data = [
    {
        'subreddit': 'Entrepreneur',
        'keywords': ['help', 'struggling', 'confused', 'not converting']
    }
]

# initialise reddit instance
reddit = praw.Reddit(client_id='your_client_id',
                     client_secret='your_client_secret',
                     user_agent='your_user_agent')
for item in search_data:
    # Subreddit to scrape
    subreddit = reddit.subreddit(item['subreddit'])

    print('Display name: ', subreddit.display_name)
    print('Title: ', subreddit.title)
    print('Description: ', subreddit.description)

    # define list to store data
    data = []

    # scraping posts and comments
    for post in subreddit.new(limit=10):

        full_text = post.title + post.selftext

        matched_keywords = [k for k in item['keywords'] if k.lower() in full_text.lower()]

        if not matched_keywords:
            continue

        post_data = {
            'Type': 'Post',
            'Post_id': post.id,
            'Title': post.title,
            'Author': post.author.name if post.author else 'Unknown',
            'Timestamp': post.created_utc,
            'Text': post.selftext,
            'Score': post.score,
            'Total_comments': post.num_comments,
            'Post_URL': post.url,
            'Subreddit': item['subreddit'],
            'Matched_keywords': ', '.join(matched_keywords)
        }

        data.append(post_data)

df = pd.DataFrame(data)

# TO GOOGLE SHEETS

creds, project = default(scope=scope)
client = gspread.authorise(creds)

spreadsheet = client.open(gsheet)

try:
    sheet = spreadsheet.worksheet(sheet_name)
except gsheet.WorksheetNotFound:
    sheet = spreadsheet.add_worksheet(
        sheet_name,
        cols=20,
        rows=1000
    )

set_with_dataframe(sheet, df)