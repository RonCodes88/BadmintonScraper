from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

driver = webdriver.Chrome()

driver.get('https://www.tournamentsoftware.com/tournament/13bfd913-52bf-4986-84f1-08ece4b947ba/matches/20240527')


# Bypass the accept page
try:
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-accept-basic"))
    )
    accept_button.click()
except Exception as e:
    print(f"Error: {e}")

html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')

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



driver.quit()

