import sys
sys.path.append('C:/Users/admin/Desktop/BadmintonScraper')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
from Scraper.scraper import open_tournament_link, find_all_matches, match_data
from RatingAlgorithm import findEloPoint, winProbability
from datetime import datetime, timedelta

# scopes represent the endpoints to access the google sheets and drive APIs
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# retrieve credentials from secret keys json and authorize the file
credentials = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/admin/Desktop/BadmintonScraper/data/secret_keys.json', scopes)
file = gspread.authorize(credentials)
workbook = file.open('Copy of Ratings for badminton')

# Get access to the sheet with specified title
currentSinglesSheet = workbook.worksheet("Current Singles")
# currentDoublesSheet = workbook.worksheet("Current Doubles")

singles = currentSinglesSheet.get_all_values()
headers = singles.pop(1)
singles.pop(0)
df_singles = pd.DataFrame(singles, columns=headers)

def clean_and_convert_to_float(cell):
    if isinstance(cell, str) and ',' in cell:
        # Remove commas and convert to float
        return float(cell.replace(',', ''))
    return cell  # Return cell as-is if no conversion is needed

# Apply the function element-wise to each cell in the dataframe
df_singles = df_singles.map(clean_and_convert_to_float)


# doublesDf = pd.DataFrame(currentDoublesSheet.get_all_values())



singles_match_data = [{"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20230621"},
                      {"winner": ["Jasper Liu"], "loser": ["NotExistLoser"], "result": "2-1", "date": "20230621"},
                      {"winner": ["NotExistWinner"], "loser": ["Ronald Li"], "result": "2-1", "date": "20230621"},
                      {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20230621"},
                      ]
# doubles_match_data = []

"""Useful later"""
# for match in match_data:
#     if len(match['winner']) == 1 and len(match['loser']) == 1:
#         singles_match_data.append(match)
#     elif len(match['winner']) == 2 and len(match['loser']) == 2:
#         doubles_match_data.append(match)

# def get_player_rating(player, default_rating=1300):
#     """Returns the player's rating if they exist in df_singles, else returns default rating."""
#     if player in df_singles['Player'].values:
#         return df_singles.loc[df_singles['Player'] == player, 'Latest Rating'].values[0]
#     return default_rating

# def determine_rating_date(match_date, df_singles):
#     """Determines the correct rating to get based on the match date."""
#     match_date = datetime.strptime(match_date, "%Y%m%d")
#     date_columns = df_singles.columns[7:]
#     dates = [datetime.strptime(date, "%m/%d") for date in date_columns]
#     dates_2024 = [date.replace(year=2024) for date in dates]

#     for date in dates_2024:
#         start, end = get_week_range(date)
#         if start <= match_date <= end:
#             print(date)


# def get_week_range(date):
#     start = date - timedelta(days=date.weekday())  # Monday of the week
#     end = start + timedelta(days=6)                # Sunday of the week
#     return start, end

# determine_rating_date("20240517", df_singles)

def insert_player_alphabetically(player, new_rating, df_singles):
    """Creates a new row and inserts it into the DataFrame maintaining alphabetical order."""
    #Finds alphabetically correct insertion point for winner player name
    insert_index = df_singles['Player'].searchsorted(player)
    # Split the DataFrame into upper and lower parts
    upper_part = df_singles.iloc[:insert_index]
    lower_part = df_singles.iloc[insert_index:]
    # Create a DataFrame for the new rows
    new_row = pd.DataFrame({'Player Ordered': [player], 'Latest Rating Ordered': [new_rating], 'Player Alphabetical': [player], 'Latest Rating': [new_rating], 'Player': [player], 'Initial Rating': [new_rating], '4/20': [None], '4/27': [None], '5/4': [None], '5/11': [None], '5/18': [None]})
    # Concatenate the parts with the new row
    df_singles = pd.concat([upper_part, new_row, lower_part]).reset_index(drop=True)
    return df_singles

def update_player_rating(player, new_rating):
    """Updates the player's rating in df_singles."""
    df_singles.loc[df_singles['Player'] == player, 'Latest Rating'] = new_rating
    df_singles.loc[df_singles['Player Ordered'] == player, 'Latest Rating Ordered'] = new_rating

def sort_by_latest_rating(df_singles):
    """Splits the dataframe into two parts, orders the first part by rating and concatenates the two parts back together."""
    df_ordered_rating = df_singles[['Player Ordered', 'Latest Rating Ordered']].sort_values(by='Latest Rating Ordered', ascending=False)
    df_alphabetical = df_singles[[col for col in df_singles.columns if col not in df_ordered_rating.columns]]
    df_ordered_rating.reset_index(drop=True, inplace=True)
    df_alphabetical.reset_index(drop=True, inplace=True)
    df_singles = pd.concat([df_ordered_rating, df_alphabetical], axis=1)
    return df_singles

"""Loop thru all players from match data and update the ratings"""
for singles_match in singles_match_data:
    winner, loser = singles_match["winner"][0], singles_match["loser"][0]
    # match_date = singles_match["date"][0]
    winner_rating = get_player_rating(winner)
    loser_rating = get_player_rating(loser)

    winner_new_rating = findEloPoint(winner_rating, loser_rating, 32, True) + winner_rating
    loser_new_rating = findEloPoint(loser_rating, winner_rating, 32, False) + loser_rating

    if winner_rating == 1300:  # Implies winner is new
        #Inserts winner player into dataframe in alphabetical order as a new row
        df_singles = insert_player_alphabetically(winner, winner_new_rating, df_singles)
    else:
        #Since winner player already exists, update their rating
        update_player_rating(winner, winner_new_rating)

    if loser_rating == 1300:  # Implies loser is new
        #Inserts loser player into dataframe in alphabetical order as a new row
        df_singles = insert_player_alphabetically(loser, loser_new_rating, df_singles)
    else:
        #Since loser player already exists, update their rating
        update_player_rating(loser, loser_new_rating)
    #Orders dataframe by latest rating
    df_singles = sort_by_latest_rating(df_singles)
print(df_singles)















# for singles_match in singles_match_data:
#         winner = singles_match["winner"][0]
#         loser = singles_match["loser"][0]
#         if winner not in df_singles['Player'].values and loser not in df_singles['Player'].values:
#             winner_new_rating = findEloPoint(1300, 1300, 32, True) 
#             loser_new_rating = findEloPoint(1300, 1300, 32, False)
#             #Inserts winner player into dataframe in alphabetical order 
#             df_singles = insert_player_alphabetically(winner, winner_new_rating, df_singles)
#             #Inserts loser player into dataframe in alphabetical order
#             df_singles = insert_player_alphabetically(loser, loser_new_rating, df_singles)
#         elif winner in df_singles['Player'].values and loser not in df_singles['Player'].values:
#             winner_new_rating = findEloPoint(df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'].values[0], 1300, 32, True)
#             loser_new_rating = findEloPoint(1300, df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'].values[0], 32, False)
#             #Modify winner player rating
#             df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'] = winner_new_rating
#             df_singles.loc[df_singles['Player Ordered'] == winner, 'Latest Rating Ordered'] = winner_new_rating
#             #Inserts loser player into dataframe in alphabetical order
#             df_singles = insert_player_alphabetically(loser, loser_new_rating, df_singles)
            
#         elif winner not in df_singles['Player'].values and loser in df_singles['Player'].values:
#             winner_new_rating = findEloPoint(1300, df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'].values[0], 32, True)
#             loser_new_rating = findEloPoint(df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'].values[0], 1300, 32, False)
#             #Inserts winner player into dataframe in alphabetical order
#             df_singles = insert_player_alphabetically(winner, winner_new_rating, df_singles)
#             #Modify loser player rating
#             df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'] = loser_new_rating
#             df_singles.loc[df_singles['Player Ordered'] == loser, 'Latest Rating Ordered'] = loser_new_rating
#         #Both players are in the dataframe
#         else:
#             winner_new_rating = findEloPoint(df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'].values[0], df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'].values[0], 32, True)
#             loser_new_rating = findEloPoint(df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'].values[0], df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'].values[0], 32, False)             
#             #Modify winner player rating
#             df_singles.loc[df_singles['Player'] == winner, 'Latest Rating'] = winner_new_rating
#             df_singles.loc[df_singles['Player Ordered'] == winner, 'Latest Rating Ordered'] = winner_new_rating
#             #Modify loser player rating
#             df_singles.loc[df_singles['Player'] == loser, 'Latest Rating'] = loser_new_rating
#             df_singles.loc[df_singles['Player Ordered'] == loser, 'Latest Rating Ordered'] = loser_new_rating

#         #Handles dataframe for ordering by latest rating
#         df_singles = sort_by_latest_rating(df_singles)
# print(df_singles)

# print(sorted_singlesDf)
        





# if __name__ == "__main__":
#     user_input = input("Please enter a list of tournament URLs separated by commas: ")

#     # Split the user input into a list of URLs
#     links = [url.strip() for url in user_input.split(',')]

#     for link in links:
#         soup = open_tournament_link(link)
#         link_date = link.split('/')[-1]
#         find_all_matches(soup, link_date)
        
#     print(match_data)