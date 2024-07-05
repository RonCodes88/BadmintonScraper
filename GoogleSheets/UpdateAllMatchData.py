import pandas as pd
import gspread
# import sys
# sys.path.append('C:/Users/admin/Desktop/BadmintonScraper')
# from oauth2client.service_account import ServiceAccountCredentials
# from Scraper.scraper import open_tournament_link, find_all_matches, match_data
from ReadAndWrite import list_to_string
   
#Converts match data (singles or doubles based on parameter) into a list for pandas dataframe
def convert_to_string(match_data: list) -> list:
    helperList = []
    helperList2 = []
    #match data is either singles or doubles
    for match in match_data:
        helperList2.append(list_to_string(match["winner"]))
        helperList2.append(list_to_string(match["loser"]))
        helperList2.append(list_to_string(match["result"]))
        helperList2.append(match["date"])
        # Add & clear the nested [winner, loser, date] into the outer list
        helperList.append(helperList2)
        helperList2 = []
    return helperList

#Writes match data onto the singles and doubles sheets ensuring the date is in ascending order
def write_match_data_onto_sheet(singles_match_data: list, doubles_match_data: list, workbook: gspread.spreadsheet.Spreadsheet):
    singlesProductSheet = workbook.worksheet("Testing Product (Singles)")
    doublesProductSheet = workbook.worksheet("Testing Product (Doubles)")
    
    #Converts match data into a list for pandas dataframe
    singles_helperList = convert_to_string(singles_match_data)
    doubles_helperList = convert_to_string(doubles_match_data)
    
    singlesProduct = singlesProductSheet.get_all_values()
    doublesProduct = doublesProductSheet.get_all_values()

    #Retrieves the column names for singles and doubles
    singlesColumns = singlesProduct.pop(0)
    doublesColumns = doublesProduct.pop(0)

    #Puts current Testing Product data into dataframes
    df_singlesProduct = pd.DataFrame(singlesProduct, columns=singlesColumns)
    df_doublesProduct = pd.DataFrame(doublesProduct, columns=doublesColumns)

    #Create the dataframes for the new singles and doubles data
    df_singlesNew = pd.DataFrame(singles_helperList, columns=singlesColumns)
    df_doublesNew = pd.DataFrame(doubles_helperList, columns=doublesColumns)

    #Combines the existing Testing Product data with the new data
    df_combinedSingles = pd.concat([df_singlesProduct, df_singlesNew], ignore_index=True)
    df_combinedDoubles = pd.concat([df_doublesProduct, df_doublesNew], ignore_index=True)

    #Converts the date column to datetime objects to sort
    df_combinedSingles['date'] = pd.to_datetime(df_combinedSingles['date'], format='%Y%m%d')
    df_combinedDoubles['date'] = pd.to_datetime(df_combinedDoubles['date'], format='%Y%m%d')

    #Sorts the data by date in ascending order ensuring stable sort (without changing the order of equal dates)
    df_singlesProduct = df_combinedSingles.sort_values(by='date', ascending=True, kind='stable')
    df_doublesProduct = df_combinedDoubles.sort_values(by='date', ascending=True, kind='stable')

    #Converts the date column back to string format for Google Sheets
    df_singlesProduct['date'] = df_singlesProduct['date'].dt.strftime('%Y%m%d')
    df_doublesProduct['date'] = df_doublesProduct['date'].dt.strftime('%Y%m%d')

    print(df_singlesProduct)
    print(df_doublesProduct)

    #Updates the Google Sheets with the new data
    singlesProductSheet.update([df_singlesProduct.columns.values.tolist()] + df_singlesProduct.values.tolist(), 'A1')
    doublesProductSheet.update([df_doublesProduct.columns.values.tolist()] + df_doublesProduct.values.tolist(), 'A1')
    
   
    



