import pandas as pd
import gspread
import sys
sys.path.append('C:/Users/admin/Desktop/BadmintonScraper')
from oauth2client.service_account import ServiceAccountCredentials
from Scraper.scraper import open_tournament_link, find_all_matches, match_data
from ReadAndWrite import list_to_string, access_the_workbook
import itertools, copy
from Retroactive import determine_earliest_retroactive_date
   
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
def write_match_data_onto_product_sheet(singles_match_data: list, doubles_match_data: list, workbook: gspread.spreadsheet.Spreadsheet):
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

    # print(df_singlesProduct)
    # print(df_doublesProduct)

    #Updates the Google Sheets with the new data
    singlesProductSheet.update([df_singlesProduct.columns.values.tolist()] + df_singlesProduct.values.tolist(), 'A1')
    doublesProductSheet.update([df_doublesProduct.columns.values.tolist()] + df_doublesProduct.values.tolist(), 'A1')

    return singlesProductSheet, doublesProductSheet
    


def filter_df_starting_from_retroactive_date(singles_match_data, doubles_match_data, singlesProductSheet, doublesProductSheet):
    earliest_singles_date, earliest_doubles_date = determine_earliest_retroactive_date(singles_match_data, doubles_match_data)
    
    singlesUpdatedProduct = singlesProductSheet.get_all_values()
    doublesUpdatedProduct = doublesProductSheet.get_all_values()

    singlesColumns = singlesUpdatedProduct.pop(0)
    doublesColumns = doublesUpdatedProduct.pop(0)

    #Puts updated Testing Product data into dataframes
    df_singlesUpdatedProduct = pd.DataFrame(singlesUpdatedProduct, columns=singlesColumns)
    df_doublesUpdatedProduct = pd.DataFrame(doublesUpdatedProduct, columns=doublesColumns)

    # print(df_singlesUpdatedProduct)
    # print(df_doublesUpdatedProduct)

    df_singlesUpdatedProduct['date'] = pd.to_datetime(df_singlesUpdatedProduct['date'], format='%Y%m%d')
    df_doublesUpdatedProduct['date'] = pd.to_datetime(df_doublesUpdatedProduct['date'], format='%Y%m%d')

    df_singlesFilteredProduct = df_singlesUpdatedProduct[df_singlesUpdatedProduct['date'] >= earliest_singles_date].copy()
    df_doublesFilteredProduct = df_doublesUpdatedProduct[df_doublesUpdatedProduct['date'] >= earliest_doubles_date].copy()

    #Converts the date column back to string format
    df_singlesFilteredProduct['date'] = df_singlesFilteredProduct['date'].dt.strftime('%Y%m%d')
    df_doublesFilteredProduct['date'] = df_doublesFilteredProduct['date'].dt.strftime('%Y%m%d')

    print(df_singlesFilteredProduct)
    print(df_doublesFilteredProduct)

    return df_singlesFilteredProduct, df_doublesFilteredProduct



'''Below is for testing'''
# if __name__ == "__main__":
#     user_input = input("Please enter a list of tournament URLs separated by commas: ")

#     # Split the user input into a list of URLs
#     links = [url.strip() for url in user_input.split(',')]
#     # Access list of URLS from spreadsheet "All Tournament Links"
#     workbook = access_the_workbook("Copy of Ratings for badminton")
#     linkSheet = workbook.worksheet("All Tournament Links")
#     existingLinks = linkSheet.get("A2:A")
#     try: existingLinks.remove([])
#     except: pass
#     existingLinks_1D = list(itertools.chain.from_iterable(existingLinks))
    
#     #Processing links
#     for link in links:
#         if link in existingLinks_1D:
#             print(f"skip processing the existed link:{link}")
#             continue
#         soup = open_tournament_link(link)
#         link_date = link.split('/')[-1]
#         find_all_matches(soup, link_date)
#         # print(match_data)
    
#     # Update the existing URLS list without duplicates
#     helperLinks = copy.deepcopy(links)
#     helperLinks_2D = [[link] for link in links]
    
#     for link in helperLinks:
#         if link not in existingLinks_1D:
#             existingLinks.append([link])
#     # print(existingLinks)
#     linkSheet.update(existingLinks, f"A2:A{len(existingLinks) + 1}")

#     singles_match_data = []
#     doubles_match_data = []

#     for match in match_data:
#         if len(match['winner']) == 1 and len(match['loser']) == 1:
#             singles_match_data.append(match)
#         elif len(match['winner']) == 2 and len(match['loser']) == 2:
#             doubles_match_data.append(match)

#     singlesProductSheet, doublesProductSheet = write_match_data_onto_product_sheet(singles_match_data, doubles_match_data, workbook)
#     #Calls filter function to filter data starting from the earliest retroactive date
#     df_singles_filtered_product, df_doubles_filtered_product = filter_df_starting_from_retroactive_date(singles_match_data, doubles_match_data, singlesProductSheet, doublesProductSheet)

#     print(df_singles_filtered_product)
#     print(df_doubles_filtered_product)
    

