# make sure to pip install gspread, gspread_formatting, oauth2client, and PyOpenSSL
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import get_effective_format
from RatingAlgorithm import findEloPoint
import re, datetime, time, copy

'''
# Determine if a cell value at specified row & column is bolded
# Precondition: number for row & col must be in between 1~26
'''
def isBolded(sheet: gspread.worksheet.Worksheet, row: int, col: int) -> bool:
    a1Label = str(chr(ord('@')+col)) + str(row)
    cell_format = get_effective_format(sheet, a1Label)
    return cell_format.textFormat.bold

'''
# Update & return the date based on the match frequency
# Precondition: the date must be in format of MM/DD/YY, and match frequency should be in 
the unit of day (ig. if the match is held every week, the match frequency is 7)
'''
def update_date(inputDate: str, matchFrequency: int) -> str:
    # Convert the input string to a datetime object
    date_format = "%m/%d/%y"  # Adjust the format to 'DD/MM/YY'
    inputDate_obj = datetime.datetime.strptime(inputDate, date_format)
    # Add the specified number of days to the date
    new_date_obj = inputDate_obj + datetime.timedelta(days=matchFrequency)
    # Convert the datetime object back to a string
    new_date_str = new_date_obj.strftime(date_format)
    return new_date_str

'''
# Search for a target element inside a nested list & return its row & col index as a tuple 
# Precondition: the nested list is a list of lists
'''
def search_nested_list(nested_list: list, target) -> tuple:
    row_index, col_index = 0, 0
    for sublist in nested_list:
        for item in sublist:
            if item == target:
                return (row_index, col_index)
            col_index += 1
        # At the every end of each inner loop
        col_index = 0
        row_index += 1
    # If no item is found
    return (-1, -1)

'''
# Read data from a sheet onto a collection (list of lists)
# Precondition: the sheet should have columns of "Player", "Initial Rating"
# Post-condition: final product should be in format [ [player1, rating1, rating2, ..., 
ratingN], [player2, rating1, rating2, ..., ratingN], ...]
'''
def read_sheet_onto_coll(inputSheet: gspread.worksheet.Worksheet, A1Range: str) -> list:
    # Update the product list
    productList = list()
    helperList = list()
    range_data = inputSheet.range(A1Range)
    curRow = int(A1Range[1])
    for cell_data in range_data:
        data = cell_data.value
        # Whenever there's a rating, compute it based on the Elo Rating Algorithm
        if (re.search('[0-9]', data)):
            # the rating here is '1,300.00', so try to convert that into clean numbers
            data = float(data.replace(",", ""))
        # If we need to move on to the next row, add & reset the nested list
        if (cell_data.row != curRow):
            productList.append(helperList)
            helperList = list()
        helperList.append(data)
        curRow = cell_data.row
    return productList

'''
# Update the collection once based on a Single/Double match
# Precondition: (1) the input list should be a product from the read_sheet_onto_coll method,
(2) mode only accepts inputs "Double" or "Single" (3) cells in matchSheet is in the format 
like the ones in 'Singles week of 4/20'
# Please try to make the code work without relying too much on the precondition (3)
'''
def update_coll_once(inputList: list, matchSheet: gspread.worksheet.Worksheet, mode: str) -> list:
    # Make a deepcopy so any changes to the new nested list won't reflect to the original one
    inputList_updated = copy.deepcopy(inputList)
    # add all players' original rating to their nested inner list
    for innerList in inputList_updated:
            innerList.append(innerList[len(innerList)-1])
    # abbr used: lP = left player, rP = right player
    # Cell values that are needed for the update
    lPTable = matchSheet.range("E2:E13")
    rPTable = matchSheet.range("F2:F13")
    # Loop through each match player cell
    for lPCell, rPCell in zip(lPTable, rPTable):
        lP, rP = lPCell.value, rPCell.value
        lStatus = isBolded(matchSheet, lPCell.row, lPCell.col)
        rStatus = isBolded(matchSheet, rPCell.row, rPCell.col)
        # Case1: double players: displayed as "playerA+playerB" in cell
        if (lP.find("+") >= 0 and mode == "Double"):
            # split the double players into [playerA, playerB]
            lPs = lP.split("+")
            rPs = rP.split("+")
            # convert [playerA, playerB] into [ratingA, ratingB]
            lPRs = list()
            rPRs = list()
            for leftP, rightP in zip(lPs, rPs):
                lPRow = search_nested_list(inputList, leftP)[0]
                rPRow = search_nested_list(inputList, rightP)[0]
                lPRating = inputList[lPRow][len(inputList[0])-1]
                rPRating = inputList[rPRow][len(inputList[0])-1]
                lPRs.append(lPRating)
                rPRs.append(rPRating)
            # Locate the match player's winning/losing point after a match
            lEloPoint = findEloPoint(sum(lPRs), sum(rPRs), 32, lStatus) / 2
            rEloPoint = findEloPoint(sum(rPRs), sum(lPRs), 32, rStatus) / 2
            # Update match players' original rating with a new post-match rating
            for lPRating, rPRating in zip(lPRs, rPRs):
                lPR_Row = search_nested_list(inputList, lPRating)[0]
                rPR_Row = search_nested_list(inputList, rPRating)[0]
                lPRating_removed = inputList_updated[lPR_Row].pop(len(inputList[0])-1)
                rPRating_removed = inputList_updated[rPR_Row].pop(len(inputList[0])-1)
                inputList_updated[lPR_Row].append(lPRating_removed + lEloPoint)
                inputList_updated[rPR_Row].append(rPRating_removed + rEloPoint)
        # Case2: single player: displayed as "playerA" in cell
        elif (lP.find("+") < 0 and mode == "Single"):
            # Locate the row of the match player
            lPRow = search_nested_list(inputList, lP)[0]
            rPRow = search_nested_list(inputList, rP)[0]
            # Locate the match player's pre-match rating & winning/losing point after a match
            lPRating = inputList[lPRow][len(inputList[0]) - 1]
            rPRating = inputList[rPRow][len(inputList[0]) - 1]
            lEloPoint = findEloPoint(lPRating, rPRating, 32, lStatus)
            rEloPoint = findEloPoint(rPRating, lPRating, 32, rStatus)
            # Update match players' original rating with a new post-match rating
            lPRating_removed = inputList_updated[lPRow].pop(len(inputList_updated[0])-1)
            rPRating_removed = inputList_updated[rPRow].pop(len(inputList_updated[0])-1)
            inputList_updated[lPRow].append(lPRating_removed + lEloPoint)
            inputList_updated[rPRow].append(rPRating_removed + rEloPoint)
    return inputList_updated

'''
# Write a given collection (a list of lists) onto a sheet
# Precondition: input list should be a product from the read_sheet_onto_call method,
date must be in format MM/DD/YY
'''
def write_coll_onto_sheet(inputList: list, workbook: gspread.spreadsheet.Spreadsheet,
                          startDate: str, matchFrequency: int, title="Product"):
    # Create a new sheet (+1 are extra rows for headers)
    try:
        productSheet = workbook.add_worksheet(title=title, rows=len(inputList)+1,
                                              cols=len(inputList[0])+1)
    # If the sheet already exists, then get access to that sheet
    except:
        productSheet = workbook.worksheet(title)
    # Create headers & fill their cells with cyan
    headers = ['Player', 'Initial Rating']
    for i in range(1, len(inputList[0])-1):
        headers.append(startDate)
        startDate = update_date(startDate, matchFrequency)
    end_col = chr(ord('@') + len(headers)) # the end column of the product sheet
    productSheet.update([headers])
    productSheet.format(f'A1:{end_col}1', {"backgroundColor": {"red": 0, "green": 1, "blue": 1}})
    # Update the sheet with 1 api call only
    productSheet.update(inputList, f'A2:{end_col}{len(inputList) + 1}')

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
singleSheet = workbook.worksheet("Current Singles")
doubleSheet = workbook.worksheet("Current Doubles")
# Store the player & initial rating onto a list of lists
singleTable = read_sheet_onto_coll(singleSheet, 'F3:L47')
doubleTable = read_sheet_onto_coll(doubleSheet, 'F3:G21')
# Update the data collection based on the tournament (multiple matches)
# The code here is somehow not working, especially for the double week's tables
'''matchDate = "04/20/24"
matchSheet = workbook.worksheet(f"Doubles week of {matchDate}")
numOfMatches = 5
for i in range(1, numOfMatches):
    singleTable = update_coll_once(singleTable, matchSheet, "Single")
    matchDate = update_date(matchDate, 7)
    matchSheet = workbook.worksheet(f"Doubles week of {matchDate}")
    # Pause the program to avoid making excessive api calls
    time.sleep(100)
doubleTable_updated = update_coll_once(doubleTable, matchSheet, "Double")
'''
# Write collections above into sheets
write_coll_onto_sheet(singleTable, workbook, "04/20/24", 7)
'write_coll_onto_sheet(doubleTable_updated, workbook, "04/20/24", 7)'