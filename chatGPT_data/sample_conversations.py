import json

with open('conversations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sample_data = data[:2]

with open('sample_conversations.json', 'w') as f:
    json.dump(sample_data, f, indent=2)