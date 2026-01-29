import requests
import json

# url = "https://www.whoscored.com/statisticsfeed/1/getplayerstatistics?"

# params = {
#     'category': 'summary',
#     'subcategory': 'all',
#     'statsAccumulationType': '0',
#     'isCurrent': 'true',
#     'tournamentOptions': '2,3,4,5,22',
#     'sortBy': 'Rating',
#     'field': 'Overall',
#     'isMinApp': 'true',
#     'numberOfPlayersToPick': '10'
# }
# resp = requests.get(url=url, params=params, headers={'User-Agent': 'Mozilla/5.0'})
# resp.text[:500]
# data = resp.json()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False, 
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context()
    page = context.new_page()

    # Step 1: Visit a real WhoScored page (important)
    page.goto(
        "https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/5471/Stages/12274/PlayerStatistics/England-Premier-League-2012-2013",
        wait_until="domcontentloaded", timeout=60000
    )

    # Step 2: Fetch API JSON inside browser context
    data = page.evaluate("""
        async () => {
            const res = await fetch(
                "https://www.whoscored.com/statisticsfeed/1/getplayerstatistics?" +
                "category=summary&" + 
                "subcategory=all&" + 
                "statsAccumulationType=0&" + 
                "isCurrent=false&" + 
                "playerId=&" + 
                "teamIds=&" + 
                "matchId=&" + 
                "stageId=&" + 
                "tournamentOptions=2,3,4,5,22&" + 
                "sortBy=Rating&" + 
                "sortAscending=&" + 
                "age=&" + 
                "ageComparisonType=&" + 
                "appearances=&" + 
                "appearancesComparisonType=&" + 
                "field=Overall&" + 
                "nationality=&" + 
                "positionOptions=&" + 
                "timeOfTheGameEnd=&" + 
                "timeOfTheGameStart=&" + 
                "isMinApp=true&" + 
                "page=&" + 
                "includeZeroValues=&" + 
                "numberOfPlayersToPick=100&" + 
                "incPens="
            );
            return await res.json();
        }
    """)

    print(data.keys())  # sanity check

    browser.close()

len(data['playerTableStats'])

data['playerTableStats'][20]
seasons = [i['seasonName'] for i in data['playerTableStats']]

print(set(seasons))
data['paging']