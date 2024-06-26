from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from datetime import datetime

def open_tournament_link(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    options.add_argument('--no-sandbox') # Bypass OS security model
    options.add_argument('--disable-dev-shm-usage') # Overcome limited resource problems
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(link)
    
        # Bypass the accept page
        try:
            accept_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-accept-basic"))
            )
            accept_button.click()
        except TimeoutException as e:
            print(f"Timeout Error: {e}")
        except WebDriverException as e:
            print(f"WebDriver Error: {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")
    
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
    
    except WebDriverException as e:
        print(f"WebDriver Exception encountered: {e}")
        soup = None
    except Exception as e:
        print(f"General Exception encountered: {e}")
        soup = None
    finally:
        driver.quit()
    
    return soup


def find_all_players(soup):
    player_names = []

    player_rows = soup.find_all('div', class_='match__row-title-value')

    for player in player_rows:
        player_name = player.find('span', class_='nav-link__value').text.strip().split(' [')[0]
        player_names.append(player_name)

    #removes duplicated player names
    unique_players = list(set(player_names))

    #sorts players sorted by last name
    sorted_players = sorted(unique_players, key=lambda x: x.split()[-1])

    for player_name in sorted_players:
        print(player_name)

    print(f"Number of players: {len(sorted_players)}")


match_data = []
'''
example: matches = [
    {"winner": ["Alice", "Eve"], "loser": ["Bob", "Frank"], "result": "2-1", "date": "20230621"},
    {"winner": ["Charlie", "Grace"], "loser": ["David", "Helen"], "result": "2-0", "date": "20230622"}
]
'''
#finds all matches (winners, losers, results, and match date) in a tournament and appends them to the match_data list
def find_all_matches(soup, link_date):
    match_group_items = soup.find_all('div', class_='match__body')

    for match_item in match_group_items:
        win_match = match_item.find('div', class_='match__row has-won')
        lose_match_list = match_item.select("div[class='match__row']") #Must use select to find exclusively div tags with class match__row
        match_results = match_item.find_all('ul', class_='points')
        winner = []
        loser = []
        result = []
        if win_match:
            winner_names = win_match.find_all('span', class_='nav-link__value')
            for winner_name in winner_names:
                winner.append(winner_name.text.strip().split(' [')[0])
    
        if lose_match_list:
            lose_match = lose_match_list[0]
            loser_names = lose_match.find_all('span', class_='nav-link__value')
            for loser_name in loser_names:
                loser.append(loser_name.text.strip().split(' [')[0])

        if match_results:
            for match_result in match_results:
                winner_score = match_result.find('li', class_='points__cell points__cell--won')
                loser_score_list = match_result.select("li[class='points__cell']") 
                result.append(f"{winner_score.text.strip()}-{loser_score_list[0].text.strip()}")
        
        match_data.append({"winner": winner, "loser": loser, "result": result, "date": link_date})
        
# user_input = input("Please enter a list of tournament URLs separated by commas: ")

# # Split the user input into a list of URLs
# links = [url.strip() for url in user_input.split(',')]

# for link in links:
#     soup = open_tournament_link(link)
#     link_date = link.split('/')[-1]
#     find_all_matches(soup, link_date)
        
# print(match_data)



