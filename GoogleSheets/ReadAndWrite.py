# make sure to pip install gspread, gspread_formatting, oauth2client, and PyOpenSSL
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from Scraper.scraper import open_tournament_link, find_all_matches, match_data

'''
# Convert ["value", "value2", ..., "valueN"] into "value1, value2..., valueN" by default
# Or besides the comma, you can pick other delimiters
'''
def list_to_string(inputList: list, sep=",") -> str:
    productStr = ""
    if (len(inputList) == 0): return "walkaway" # for blank list
    for val in inputList:
        productStr += val + sep
    return productStr[:len(productStr)-len(sep)]

'''
# Write a given collection of match data onto a sheet
# Precondition: collection is a list of { "winner": ["players"], "loser": ["players"], "result": ["#-#"],
"date": YYYYMMDD }
'''
def write_coll_onto_sheet(inputList: list, workbook: gspread.spreadsheet.Spreadsheet, title="Product"):
    # Create a new sheet (+1 are extra rows for headers)
    try:
        productSheet = workbook.add_worksheet(title=title, rows=len(inputList)+1, cols=5)
    # If the sheet already exists, then get access to that sheet
    except:
        productSheet = workbook.worksheet(title)
    # Update header into the sheet
    headers = ['winner', 'loser', 'result', 'date']
    productSheet.update([headers])
    # Convert a list of dictionaries -> a list of lists
    # In order to update the sheet with 1 api call only
    helperList = []
    helperList2 = []
    for innerDict in inputList:
        helperList2.append(list_to_string(innerDict["winner"]))
        helperList2.append(list_to_string(innerDict["loser"]))
        helperList2.append(list_to_string(innerDict["result"]))
        helperList2.append(innerDict["date"])
        # Add & clear the nested [winner, loser, date] into the outer list
        helperList.append(helperList2)
        helperList2 = []
    productSheet.update(helperList, f'A2:D{len(inputList)+1}')

'''
# Read data from a sheet onto a collection
# Pre-condition: input sheet has columns of winner, loser, result, date
# Post-condition: final product is a list of { "winner": ["players"], "loser": ["players"], "result": ["#-#"], 
"date": 'YYYYMMDD' }
'''
def read_sheet_onto_coll(inputSheet: gspread.worksheet.Worksheet) -> list:
    # Modify inputData into the final product
    inputData = inputSheet.get_all_records()
    # For single matches, inputData is a list of { 'winner': 'player', 'loser': 'player', 'result': '#-#',
    # 'date': YYYYMMDD}
    if (inputData[0]['winner'].find(",") < 0):
        for inputDict in inputData:
            inputDict['winner'], inputDict['loser'] = [inputDict['winner']], [inputDict['loser']]
            inputDict['result'] = [inputDict['result']]
            inputDict['date'] = str(inputDict['date'])
    # For double matches, inputData is a list of { 'winner': 'player1,player2', 'loser': 'player1,player2',
    # 'result': '#-#,#-#,#-#', 'date': YYYYMMDD}
    else:
        for inputDict in inputData:
            winners, losers = inputDict['winner'].split(","), inputDict['loser'].split(",")
            inputDict['winner'] = winners
            inputDict['loser'] = losers
            inputDict['result'] = inputDict['result'].split(",")
            inputDict['date'] = str(inputDict['date'])
    return inputData

# scopes represent the endpoints to access the google sheets and drive APIs
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# retrieve credentials from secret keys json and authorize the file
credentials = ServiceAccountCredentials.from_json_keyfile_name('secret key.json', scopes)
file = gspread.authorize(credentials)
workbook = file.open('Copy of Ratings for badminton')

# Retrieving match data from the scraper
singles_match_data = []
doubles_match_data = []
title_single, title_double = "Product (Single)", "Product (Double)"
if __name__ == "__main__":
    user_input = input("Please enter a list of tournament URLs separated by commas: ")
    # Split the user input into a list of URLs
    links = [url.strip() for url in user_input.split(',')]
    for link in links:
        soup = open_tournament_link(link)
        link_date = link.split('/')[-1]
        find_all_matches(soup, link_date)
for match in match_data:
    if len(match['winner']) == 1 and len(match['loser']) == 1:
        singles_match_data.append(match)
    elif len(match['winner']) == 2 and len(match['loser']) == 2:
        doubles_match_data.append(match)

# Writing data into the spreadsheet
write_coll_onto_sheet(singles_match_data, workbook, title=title_single)
write_coll_onto_sheet(doubles_match_data, workbook, title=title_double)

# Reading data from the spreadsheet
matchSheet_single = workbook.worksheet(title_single)
matchSheet_double = workbook.worksheet(title_double)
print(f"single data: {read_sheet_onto_coll(matchSheet_single)}")
print(f"double data: {read_sheet_onto_coll(matchSheet_double)}")

