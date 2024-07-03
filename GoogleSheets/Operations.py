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
    Testing_doubles = workbook.worksheet('Testing Doubles')
    # currentSinglesSheet = workbook.worksheet("Current Singles")
    # currentDoublesSheet = workbook.worksheet("Current Doubles")
    singles = Testing_singles.get_all_values()
    doubles = Testing_doubles.get_all_values()
    headers_singles = singles.pop(1)
    headers_doubles = doubles.pop(1)
    singles.pop(0)
    doubles.pop(0)
    df_singles = pd.DataFrame(singles, columns=headers_singles)
    df_doubles = pd.DataFrame(doubles, columns=headers_doubles)
    return Testing_singles, Testing_doubles, df_singles, df_doubles


def clean_and_convert_to_float(cell):
    if isinstance(cell, str) and ',' in cell:
        # Remove commas and convert to float
        return float(cell.replace(',', ''))
    return cell


'''For testing purposes'''
# match_data = [
        # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240321"},
        # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240228"},
        # {"winner": ["Jasper Liu"], "loser": ["Ronald Li"], "result": "2-1", "date": "20240625"},
        # {"winner": ["Jasper Liu", "Ronald Li"], "loser": ["Ronald Li", "Jasper Liu"], "result": "2-1", "date": "20240617"},
    # ]

def determine_rating_date(match_date, df):
    """Determines the correct rating to get based on the match date."""
    match_date = datetime.strptime(match_date, "%Y%m%d")
    date_columns = df.columns[6:]
    days_until_saturday = (5 - match_date.weekday()) % 7
    new_rating_date = match_date + timedelta(days=days_until_saturday)
    if all(col == '' for col in date_columns):
        return new_rating_date.strftime("%m/%d/%Y"), None
    else:     
        if match_date < datetime.strptime(df.columns[6], "%m/%d/%Y"):
            return new_rating_date.strftime("%m/%d/%Y"), None
        elif match_date > datetime.strptime(df.columns[-1], "%m/%d/%Y"):
            return new_rating_date.strftime("%m/%d/%Y"), None
        else:
            for i in range(len(date_columns) - 1):
                if datetime.strptime(date_columns[i], "%m/%d/%Y") <= match_date <= datetime.strptime(date_columns[i + 1], "%m/%d/%Y"):
                    return new_rating_date.strftime("%m/%d/%Y"), date_columns[i]

def get_player_rating(player, new_rating_date, df):  
    default_rating = 1300
    new_rating_date_dt = datetime.strptime(new_rating_date, "%m/%d/%Y")
    if player in df['Player'].values:
        if new_rating_date_dt < datetime.strptime(df.columns[6], "%m/%d/%Y"): 
            return df.loc[df['Player'] == player, 'Initial Rating'].values[0]
        elif new_rating_date_dt > datetime.strptime(df.columns[-1], "%m/%d/%Y"):
            return df.loc[df['Player'] == player, 'Latest Rating'].values[0]
        else: 
            date_columns = df.columns[7:]
            for i in range(len(date_columns) - 1):
                earliest_date = datetime.strptime(date_columns[i], "%m/%d/%Y")
                latest_date = datetime.strptime(date_columns[i + 1], "%m/%d/%Y")
                if earliest_date < new_rating_date_dt < latest_date:
                    value = df.loc[df['Player'] == player, date_columns[i]].values[0]
                    if pd.notna(value) and value != '':
                        return value
                    # If value is NaN, go backwards to find the previous non-NaN value
                    for j in range(i, -1, -1):
                        prev_value = df.loc[df['Player'] == player, date_columns[j]].values[0]
                        if pd.notna(prev_value) and value != '':
                            return prev_value
    return default_rating



def insert_player_alphabetically(player, new_rating, df):
    """Creates a new row and inserts it into the DataFrame maintaining alphabetical order."""
    # Create a DataFrame for the new row
    new_row = pd.DataFrame({'Player Ordered': [player], 'Latest Rating Ordered': [new_rating], 'Player Alphabetical': [player], 'Latest Rating': [new_rating], 'Player': [player], 'Initial Rating': 1300.00})
    if not df['Player'].any():
        df = df.reset_index(drop=True)
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        #Finds alphabetically correct insertion point for winner player name
        insert_index = df['Player'].searchsorted(player)
        # Split the DataFrame into upper and lower parts
        upper_part = df.iloc[:insert_index].reset_index(drop=True)
        lower_part = df.iloc[insert_index:].reset_index(drop=True)
        # Concatenate the parts with the new row
        df = pd.concat([upper_part, new_row, lower_part]).reset_index(drop=True)
    
    return df
    
    
    
def update_player_rating(player, new_rating, new_rating_date, date, elo_point, df):
    """Updates the player's rating in provided dataframe.""" 
    # Convert new_rating_date from string to datetime
    new_rating_date_dt = datetime.strptime(new_rating_date, "%m/%d/%Y")
    if len(df.columns) == 6:
        df.insert(loc=6, column=new_rating_date, value=None)
    else:
        # Convert the target column date from string to datetime for comparison
        first_column_date_dt = datetime.strptime(df.columns[6], "%m/%d/%Y")
        last_column_date_dt = datetime.strptime(df.columns[-1], "%m/%d/%Y")
    
        #Insert new column at the start of the dates
        if new_rating_date_dt < first_column_date_dt:
            if new_rating_date not in df.columns:
                df.insert(loc=6, column=new_rating_date, value=None)  # Use the string version of date for column name
        #Insert new column at the end of the dates
        elif new_rating_date_dt > last_column_date_dt:
            if new_rating_date not in df.columns:
                df.insert(loc=len(df.columns), column=new_rating_date, value=None)  # Use the string version of date for column name
            df.loc[df['Player Ordered'] == player, 'Latest Rating Ordered'] = new_rating
        #Insert new column in between the dates
        elif new_rating_date not in df.columns:
            df.insert(loc=df.columns.get_loc(date) + 1, column=new_rating_date, value=None)
    
    # Update the player's rating in the new or existing column
    df.loc[df['Player'] == player, new_rating_date] = new_rating

    '''This part not working as intended, need to fix it'''
    #Retroactively updates player's all historical ratings and latest rating if necessary 
    if new_rating_date in df.columns:
        row_index = df[df['Player'] == player].index[0]
        column_index = df.columns.get_loc(new_rating_date)
        df.iloc[row_index, column_index + 1:] = df.iloc[row_index, column_index + 1:].apply(
            lambda x: float(str(x).replace(',', '')) if str(x).replace(',', '').strip() not in ['', 'None'] else None
        )
        df.iloc[row_index, column_index + 1:] += elo_point
        last_valid_col_index = df.iloc[row_index].last_valid_index()
        latest_rating = df.iloc[row_index, df.columns.get_loc(last_valid_col_index)]
        df.loc[df['Player Ordered'] == player, 'Latest Rating Ordered'] = latest_rating
        df.loc[df['Player'] == player, 'Latest Rating'] = latest_rating


def sort_by_latest_rating(df):
    """Splits the dataframe into two parts, orders the first part by rating and concatenates the two parts back together."""
    df['Latest Rating Ordered'] = df['Latest Rating Ordered'].apply(lambda x: float(str(x).replace(',', '')))
    df_ordered_rating = df[['Player Ordered', 'Latest Rating Ordered']].sort_values(by='Latest Rating Ordered', ascending=False)
    df_alphabetical = df[[col for col in df.columns if col not in df_ordered_rating.columns]]
    df_ordered_rating.reset_index(drop=True, inplace=True)
    df_alphabetical.reset_index(drop=True, inplace=True)
    df = pd.concat([df_ordered_rating, df_alphabetical], axis=1)
    return df


def update_ratings_singles(singles_match_data, df_singles):
    """Loop through all players from singles data and update their ratings"""
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

def update_ratings_doubles(doubles_match_data, df_doubles):
    """Loop through all players from doubles data and update their ratings"""
    for doubles_match in doubles_match_data:
        winner1, winner2 = doubles_match["winner"][0], doubles_match["winner"][1]
        loser1, loser2 = doubles_match["loser"][0], doubles_match["loser"][1]
        
        new_rating_date, date = determine_rating_date(doubles_match['date'], df_doubles)

        winner1_rating = get_player_rating(winner1, new_rating_date, df_doubles)
        winner2_rating = get_player_rating(winner2, new_rating_date, df_doubles)
        loser1_rating = get_player_rating(loser1, new_rating_date, df_doubles)
        loser2_rating = get_player_rating(loser2, new_rating_date, df_doubles)

        winner_team_rating = (float(winner1_rating) + float(winner2_rating)) / 2
        loser_team_rating = (float(loser1_rating) + float(loser2_rating)) / 2

        winner_elo = findEloPoint(winner_team_rating, loser_team_rating, 32, True)
        loser_elo = findEloPoint(loser_team_rating, winner_team_rating, 32, False)
        
        winner1_new_rating = float(winner1_rating) + winner_elo
        winner2_new_rating = float(winner2_rating) + winner_elo
        loser1_new_rating = float(loser1_rating) + loser_elo
        loser2_new_rating = float(loser2_rating) + loser_elo
        
        if winner1 not in df_doubles['Player'].values:  # Implies winner is new
            #Inserts winner player into dataframe in alphabetical order as a new row
            df_doubles = insert_player_alphabetically(winner1, winner1_new_rating, df_doubles)
            update_player_rating(winner1, winner1_new_rating, new_rating_date, date, winner_elo, df_doubles)
        else:
            #Since winner player already exists, update their rating
            update_player_rating(winner1, winner1_new_rating, new_rating_date, date, winner_elo, df_doubles)

        if winner2 not in df_doubles['Player'].values:  # Implies winner is new
            #Inserts winner player into dataframe in alphabetical order as a new row
            df_doubles = insert_player_alphabetically(winner2, winner2_new_rating, df_doubles)
            update_player_rating(winner2, winner2_new_rating, new_rating_date, date, winner_elo, df_doubles)
        else:
            #Since winner player already exists, update their rating
            update_player_rating(winner2, winner2_new_rating, new_rating_date, date, winner_elo, df_doubles)

        if loser1 not in df_doubles['Player'].values:  # Implies loser is new
            #Inserts loser player into dataframe in alphabetical order as a new row
            df_doubles = insert_player_alphabetically(loser1, loser1_new_rating, df_doubles)
            update_player_rating(loser1, loser1_new_rating, new_rating_date, date, loser_elo, df_doubles)
        else:
            #Since loser player already exists, update their rating
            update_player_rating(loser1, loser1_new_rating, new_rating_date, date, loser_elo, df_doubles)

        if loser2 not in df_doubles['Player'].values:  # Implies loser is new
            #Inserts loser player into dataframe in alphabetical order as a new row
            df_doubles = insert_player_alphabetically(loser2, loser2_new_rating, df_doubles)
            update_player_rating(loser2, loser2_new_rating, new_rating_date, date, loser_elo, df_doubles)
        else:
            #Since loser player already exists, update their rating
            update_player_rating(loser2, loser2_new_rating, new_rating_date, date, loser_elo, df_doubles)
        
        #Orders dataframe by latest rating
        df_doubles = sort_by_latest_rating(df_doubles)
    return df_doubles



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
    print(doubles_match_data)
    
    Testing_singles, Testing_doubles, df_singles, df_doubles = get_sheet_data_as_dataframe()
    # Apply the function element-wise to each cell in the dataframe
    df_singles = df_singles.map(clean_and_convert_to_float)
    df_doubles = df_doubles.map(clean_and_convert_to_float)
    df_singles = update_ratings_singles(singles_match_data, df_singles)
    df_doubles = update_ratings_doubles(doubles_match_data, df_doubles)
    print(df_singles)
    print(df_doubles)
    df_singles_to_sheet = [df_singles.columns.values.tolist()] + df_singles.where(pd.notnull(df_singles), '').values.tolist()
    df_doubles_to_sheet = [df_doubles.columns.values.tolist()] + df_doubles.where(pd.notnull(df_doubles), '').values.tolist()
    Testing_singles.update(df_singles_to_sheet, 'A2')
    Testing_doubles.update(df_doubles_to_sheet, 'A2')
    print("Success!")
        
   