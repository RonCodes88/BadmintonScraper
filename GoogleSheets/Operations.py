import sys
sys.path.append('C:/Users/admin/Desktop/BadmintonScraper')
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from gspread_dataframe import get_as_dataframe, set_with_dataframe
import pandas as pd
from Scraper.scraper import open_tournament_link, find_all_matches, match_data
from RatingAlgorithm import findEloPoint, winProbability
from datetime import datetime, timedelta

def get_sheet_data_as_dataframe():
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
    Testing_singles = workbook.worksheet('Testing Singles')
    # currentSinglesSheet = workbook.worksheet("Current Singles")
    # currentDoublesSheet = workbook.worksheet("Current Doubles")
    singles = Testing_singles.get_all_values()

    headers = singles.pop(1)
    singles.pop(0)
    df_singles = pd.DataFrame(singles, columns=headers)
    return Testing_singles, df_singles


def clean_and_convert_to_float(cell):
    if isinstance(cell, str) and ',' in cell:
        # Remove commas and convert to float
        return float(cell.replace(',', ''))
    return cell




# doublesDf = pd.DataFrame(currentDoublesSheet.get_all_values())

'''For testing purposes'''
# match_data = [
    #     # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240321"},
    #     # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240228"},
    #     # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240625"},
    #     # {"winner": ["Jasper Liu", "Ronald Li"], "loser": ["Ronald Li", "Jasper Liu"], "result": "2-1", "date": "20240617"},
    # ]

def determine_rating_date(match_date, df_singles):
    """Determines the correct rating to get based on the match date."""
    match_date = datetime.strptime(match_date, "%Y%m%d")
    date_columns = df_singles.columns[7:]
    days_until_saturday = (5 - match_date.weekday()) % 7
    new_rating_date = match_date + timedelta(days=days_until_saturday)
    if all(col == '' for col in date_columns):
        return new_rating_date.strftime("%m/%d/%Y"), None
    else:     
        if match_date < datetime.strptime(df_singles.columns[7], "%m/%d/%Y"):
            return new_rating_date.strftime("%m/%d/%Y"), None
        elif match_date > datetime.strptime(df_singles.columns[-1], "%m/%d/%Y"):
            return new_rating_date.strftime("%m/%d/%Y"), None
        else:
            for i in range(len(date_columns) - 1):
                if datetime.strptime(date_columns[i], "%m/%d/%Y") <= match_date <= datetime.strptime(date_columns[i + 1], "%m/%d/%Y"):
                    return new_rating_date.strftime("%m/%d/%Y"), date_columns[i]

def get_player_rating(player, new_rating_date, df_singles):  
    default_rating = 1300
    new_rating_date_dt = datetime.strptime(new_rating_date, "%m/%d/%Y")
    if player in df_singles['Player'].values:
        # if new_rating_date in df_singles.columns:
        #     return df_singles.loc[df_singles['Player'] == player, new_rating_date].values[0]
        if new_rating_date_dt < datetime.strptime(df_singles.columns[7], "%m/%d/%Y"): 
            return df_singles.loc[df_singles['Player'] == player, 'Initial Rating'].values[0]
        elif new_rating_date_dt > datetime.strptime(df_singles.columns[-1], "%m/%d/%Y"):
            return df_singles.loc[df_singles['Player'] == player, 'Latest Rating'].values[0]
        else: 
            date_columns = df_singles.columns[7:]
            for i in range(len(date_columns) - 1):
                earliest_date = datetime.strptime(date_columns[i], "%m/%d/%Y")
                latest_date = datetime.strptime(date_columns[i + 1], "%m/%d/%Y")
                if earliest_date < new_rating_date_dt < latest_date:
                    value = df_singles.loc[df_singles['Player'] == player, date_columns[i]].values[0]
                    if pd.notna(value) and value != '':
                        return value
                    # If value is NaN, go backwards to find the previous non-NaN value
                    for j in range(i, -1, -1):
                        prev_value = df_singles.loc[df_singles['Player'] == player, date_columns[j]].values[0]
                        if pd.notna(prev_value) and value != '':
                            return prev_value
    return default_rating



def insert_player_alphabetically(player, new_rating, df_singles):
    """Creates a new row and inserts it into the DataFrame maintaining alphabetical order."""
    #Finds alphabetically correct insertion point for winner player name
    insert_index = df_singles['Player'].searchsorted(player)
    # Split the DataFrame into upper and lower parts
    upper_part = df_singles.iloc[:insert_index]
    lower_part = df_singles.iloc[insert_index:]
    # Create a DataFrame for the new rows
    new_row = pd.DataFrame({'Player Ordered': [player], 'Latest Rating Ordered': [new_rating], 'Player Alphabetical': [player], 'Latest Rating': [new_rating], 'Player': [player], 'Initial Rating': 1300})
    # Concatenate the parts with the new row
    df_singles = pd.concat([upper_part, new_row, lower_part]).reset_index(drop=True)
    return df_singles
    
def update_player_rating(player, new_rating, new_rating_date, date, elo_point, df_singles):
    """Updates the player's rating in df_singles.""" 
    # Convert new_rating_date from string to datetime once at the beginning
    new_rating_date_dt = datetime.strptime(new_rating_date, "%m/%d/%Y")
    
    # Convert the target column date from string to datetime for comparison
    first_column_date_dt = datetime.strptime(df_singles.columns[7], "%m/%d/%Y")
    last_column_date_dt = datetime.strptime(df_singles.columns[-1], "%m/%d/%Y")
   
    #Insert new column at the start of the dates
    if new_rating_date_dt < first_column_date_dt:
        if new_rating_date not in df_singles.columns:
            df_singles.insert(loc=7, column=new_rating_date, value=None)  # Use the string version of date for column name
    #Insert new column at the end of the dates
    elif new_rating_date_dt > last_column_date_dt:
        if new_rating_date not in df_singles.columns:
            df_singles.insert(loc=len(df_singles.columns), column=new_rating_date, value=None)  # Use the string version of date for column name
        df_singles.loc[df_singles['Player Ordered'] == player, 'Latest Rating Ordered'] = new_rating
    elif new_rating_date not in df_singles.columns:
        df_singles.insert(loc=df_singles.columns.get_loc(date) + 1, column=new_rating_date, value=None)
    
    # Update the player's rating in the new or existing column
    df_singles.loc[df_singles['Player'] == player, new_rating_date] = new_rating

    #retroactively updates player's all historical ratings and latest rating if necessary
    if new_rating_date in df_singles.columns:
        row_index = df_singles[df_singles['Player'] == player].index[0]
        column_index = df_singles.columns.get_loc(new_rating_date)
        df_singles.iloc[row_index, column_index + 1:] = df_singles.iloc[row_index, column_index + 1:].apply(
            lambda x: float(str(x).replace(',', '')) if str(x).replace(',', '').strip() not in ['', 'None'] else None
        )
        df_singles.iloc[row_index, column_index + 1:] += elo_point
        last_valid_col_index = df_singles.iloc[row_index].last_valid_index()
        latest_rating = df_singles.iloc[row_index, df_singles.columns.get_loc(last_valid_col_index)]
        df_singles.loc[df_singles['Player Ordered'] == player, 'Latest Rating Ordered'] = latest_rating
        df_singles.loc[df_singles['Player'] == player, 'Latest Rating'] = latest_rating


def sort_by_latest_rating(df_singles):
    """Splits the dataframe into two parts, orders the first part by rating and concatenates the two parts back together."""
    df_singles['Latest Rating Ordered'] = df_singles['Latest Rating Ordered'].apply(lambda x: float(str(x).replace(',', '')))
    df_ordered_rating = df_singles[['Player Ordered', 'Latest Rating Ordered']].sort_values(by='Latest Rating Ordered', ascending=False)
    df_alphabetical = df_singles[[col for col in df_singles.columns if col not in df_ordered_rating.columns]]
    df_ordered_rating.reset_index(drop=True, inplace=True)
    df_alphabetical.reset_index(drop=True, inplace=True)
    df_singles = pd.concat([df_ordered_rating, df_alphabetical], axis=1)
    return df_singles


"""Loop thru all players from match data and update the ratings"""
def update_ratings_singles(singles_match_data, df_singles):
    for singles_match in singles_match_data:
        winner, loser = singles_match["winner"][0], singles_match["loser"][0]
        
        new_rating_date, date = determine_rating_date(singles_match['date'], df_singles)

        winner_rating = get_player_rating(winner, new_rating_date, df_singles)
        loser_rating = get_player_rating(loser, new_rating_date, df_singles)

        winner_elo = findEloPoint(float(winner_rating), float(loser_rating), 32, True)
        loser_elo = findEloPoint(float(loser_rating), float(winner_rating), 32, False)
        
        winner_new_rating = float(winner_rating) + winner_elo
        loser_new_rating = float(loser_rating) + loser_elo
        
        if winner not in df_singles['Player'].values:  # Implies winner is new
            #Inserts winner player into dataframe in alphabetical order as a new row
            df_singles = insert_player_alphabetically(winner, winner_new_rating, df_singles)
            update_player_rating(winner, winner_new_rating, new_rating_date, date, winner_elo, df_singles)
        else:
            #Since winner player already exists, update their rating
            update_player_rating(winner, winner_new_rating, new_rating_date, date, winner_elo, df_singles)

        if loser not in df_singles['Player'].values:  # Implies loser is new
            #Inserts loser player into dataframe in alphabetical order as a new row
            df_singles = insert_player_alphabetically(loser, loser_new_rating, df_singles)
            update_player_rating(loser, loser_new_rating, new_rating_date, date, loser_elo, df_singles)
        else:
            #Since loser player already exists, update their rating
            update_player_rating(loser, loser_new_rating, new_rating_date, date, loser_elo, df_singles)
        #Orders dataframe by latest rating
        df_singles = sort_by_latest_rating(df_singles)
    return df_singles



if __name__ == "__main__":
    user_input = input("Please enter a list of tournament URLs separated by commas: ")

    # Split the user input into a list of URLs
    links = [url.strip() for url in user_input.split(',')]

    for link in links:
        soup = open_tournament_link(link)
        link_date = link.split('/')[-1]
        find_all_matches(soup, link_date)
        # print(match_data)
    
    singles_match_data = []
    doubles_match_data = []

    for match in match_data:
        if len(match['winner']) == 1 and len(match['loser']) == 1:
            singles_match_data.append(match)
        elif len(match['winner']) == 2 and len(match['loser']) == 2:
            doubles_match_data.append(match)
    
    print(singles_match_data)
    
    Testing_singles, df_singles = get_sheet_data_as_dataframe()
    # Apply the function element-wise to each cell in the dataframe
    df_singles = df_singles.map(clean_and_convert_to_float)
    df_singles = update_ratings_singles(singles_match_data, df_singles)
    df_to_sheet = [df_singles.columns.values.tolist()] + df_singles.where(pd.notnull(df_singles), '').values.tolist()
    Testing_singles.update(df_to_sheet, 'A2')
        
   