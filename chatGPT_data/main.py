import json
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
from google.auth import default
import pandas as pd


gsheet = 'ChatGPT data'
sheet_name = 'data'

# Scope
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]


with open('conversations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chats = []
for chat in data:
    messages = []
    for node in chat['mapping'].values():
        msg = node.get('message')
        if not msg:
            continue
            
        author = msg.get('author', {})
        role = author.get('role')

        if role not in ['assistant','user']:
            continue

        content = msg.get('content', {})
        parts = content.get('parts')
        if not isinstance(parts, list):
            print(f"Parts is not a list: {parts}")
            print(f"From create_time: {msg.get('create_time')}")
            parts = []

        text = " ".join(parts) if content.get('content_type') == 'text' else ""

        create_time = msg.get('create_time') 
        date = datetime.fromtimestamp(create_time) if create_time else None

        messages.append({
            'Date': date.isoformat() if date else None,
            'Role': role,
            'Text': text
        })

    my_messages = [m['Text'] for m in messages if m['Role'] == 'user']
    my_message_count = len(my_messages)
    my_message_text = " ".join(my_messages)
    my_message_word_count = len(my_message_text.split())

    conversation_id = chat.get('conversation_id') or chat.get('id')

    first_message = messages[0]['Text']
    first_message_preview = first_message[:min(200, len(first_message))]

    create_dt = datetime.fromtimestamp(chat['create_time']) if chat.get('create_time') else None
            
    chats.append({
        'Title': chat.get('title'),
        'Create time': create_dt.isoformat(),
        'My message count': my_message_count,
        'My word count': my_message_word_count,
        'Preview': first_message_preview,
        'Year Month': create_dt.strftime('%Y-%m') if create_dt else None,
        'Update time': datetime.fromtimestamp(chat['update_time']).isoformat() if chat.get('update_time') else None,
        'Chat link': f"https://chatgpt.com/c/{conversation_id}"
    })

with open('output.json', 'w') as f:
    json.dump(chats, f, indent=2)

chats_df = pd.DataFrame(chats)

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
        rows=1000)

set_with_dataframe(sheet, chats_df)