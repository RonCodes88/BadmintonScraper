# make sure to pip install gspread, gspread_formatting, oauth2client, and PyOpenSSL
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import get_effective_format
from RatingAlgorithm import findEloRating
import time

# Determine if a cell value at specified A1 Label is bolded
def isBolded(sheet: gspread.worksheet.Worksheet, a1Label: str) -> bool:
    cell_format = get_effective_format(sheet, a1Label)
    return cell_format.textFormat.bold

# Read data from a sheet onto a dictionary
# def read_sheet_onto_dict(workbook: gspread.spreadsheet.Spreadsheet, title: str):

# Write a given dictionary (or multiple) onto a new sheet
# So far, this can only deal with first week's ratings
def write_dict_onto_sheet(workbook: gspread.spreadsheet.Spreadsheet, title: str, *inputDicts: dict):
    # Create a sheet (+1 are extra rows & columns for headers)
    try:
        productSheet = workbook.add_worksheet(title=title, rows=len(inputDicts[0])+1,
                                              cols=len(inputDicts[0])+1)
    # If the sheet already exists
    except:
        productSheet = workbook.worksheet(title)
    # Create headers & fill their cells with cyan
    productSheet.update([['Player', 'Initial Rating', '4/20']])
    productSheet.format('A1:C1', {"backgroundColor": {"red": 0, "green": 1, "blue": 1}})
    # Instead of looping through dictionary to update sheet (as it'll make too many api calls)
    # Turn inputDict into a list of lists, then update the sheet with 1 api call only
    inputNestedList = []
    for (player, initialRating), newRating in zip(inputDicts[0].items(), inputDicts[1].values()):
        inputNestedList.append([player, initialRating, newRating])
    productSheet.update(inputNestedList, f'A2:C{len(inputDicts[0])+1}')

# scopes represent the endpoints to access the google sheets and drive APIs
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# retrieve credentials from secret keys json and authorize the file
credentials = ServiceAccountCredentials.from_json_keyfile_name('secret key.json', scopes)
file = gspread.authorize(credentials)
workbook = file.open('Copy of Ratings for badminton')

# Example to open the first sheet (specified index 0) in the workbook
# sheet = workbook.get_worksheet(0)

# Get access to the sheet from current singles & doubles
singleSheet = workbook.worksheet("Current Singles")
doubleSheet = workbook.worksheet("Current Doubles")

# Player names and ratings are in columns F and G respectively
names_range_single = singleSheet.range("F3:F47")
ratings_range_single = singleSheet.range("G3:G47")
names_range_double = doubleSheet.range("F3:F21")
ratings_range_double = doubleSheet.range("G3:G21")

# Put all player names and their ratings into a dictionary
singleTable = dict()
doubleTable = dict()
for name_cell, rating_cell in zip(names_range_single, ratings_range_single):
    name = name_cell.value
    rating = rating_cell.value # the rating here is '1,300.00', so try to convert that into numbers
    rating = float(rating.replace(",", ""))
    singleTable.update({name: rating})
for name_cell, rating_cell in zip(names_range_double, ratings_range_double):
    name = name_cell.value
    rating = rating_cell.value # the rating here is '1,300.00', so try to convert that into numbers
    rating = float(rating.replace(",", ""))
    doubleTable.update({name: rating})

# Now open worksheets with all the match results
matchSheet = workbook.worksheet("Doubles week of 4/20")

# Update ratings in the dictionary based on the match result
# abbr used: lP = left player, rP = right player
singleTable_updated = singleTable.copy()
doubleTable_updated = doubleTable.copy()

# Cell values that are needed for the update
lPTable = matchSheet.range("E2:E13")
rPTable = matchSheet.range("F2:F13")
# A1 labels that are needed for the update
leftA1Labels = list()
rightA1Labels = list()
for num in range(2, 14):
    leftA1Labels.append("E" + str(num))
    rightA1Labels.append("F" + str(num))

for lPCell, rPCell, lA1, rA1 in zip(lPTable, rPTable, leftA1Labels, rightA1Labels):
    lP = lPCell.value
    rP = rPCell.value
    lStatus = isBolded(matchSheet, lA1)
    rStatus = isBolded(matchSheet, rA1)
    lPRating = 0
    rPRating = 0
    # Case1: double players: displayed as "player1+player2" in cell
    if (lP.find("+") >= 0):
        # split the double players into [player1, player2]
        lPs = lP.split("+")
        rPs = rP.split("+")
        for leftP, rightP in zip(lPs, rPs):
            lPRating += doubleTable[leftP]
            rPRating += doubleTable[rightP]
        # update new ratings of left & right players into the dictionary
        for leftP, rightP in zip(lPs, rPs):
            doubleTable_updated[leftP] += findEloRating(lPRating, rPRating, 32, lStatus) / 2
            doubleTable_updated[rightP] += findEloRating(rPRating, lPRating, 32, rStatus) / 2
    # Case2: single player: displayed as "player1" in cell
    else:
        lPRating = singleTable[lP]
        rPRating = singleTable[rP]
        # update new ratings of left & right players into the dictionary
        singleTable_updated[lP] += findEloRating(lPRating, rPRating, 32, lStatus)
        singleTable_updated[rP] += findEloRating(rPRating, lPRating, 32, rStatus)

# Pause the program to avoid making excessive api calls
time.sleep(10)

# Example to update a cell to "" at row 49, column 2
# sheet.update_cell(49, 2, "example update")

# Write dictionaries above into sheets
write_dict_onto_sheet(workbook, "Product (single)", singleTable, singleTable_updated)
write_dict_onto_sheet(workbook, "Product (double)", doubleTable, doubleTable_updated)