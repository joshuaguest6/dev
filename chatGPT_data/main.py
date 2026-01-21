import json
from datetime import datetime

with open('sample_conversations.json', 'r', encoding='utf-8') as f:
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

        text = " ".join(parts)

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
            
    chats.append({
        'Title': chat.get('title'),
        'Create time': datetime.fromtimestamp(chat['create_time']).isoformat() if chat.get('create_time') else None,
        'Update time': datetime.fromtimestamp(chat['update_time']).isoformat() if chat.get('update_time') else None,
        'Chat link': f"https://chatgpt.com/c/{conversation_id}",
        'My message count': my_message_count,
        'My word count': my_message_word_count,
        'Messages': messages
    })

with open('sample_output.json', 'w') as f:
    json.dump(chats, f, indent=2)