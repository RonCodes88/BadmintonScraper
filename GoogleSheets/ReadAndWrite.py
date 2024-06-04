import gspread 
from oauth2client.service_account import ServiceAccountCredentials

#make sure to pip install gspread, oauth2client, and PyOpenSSL


#scopes represent the endpoints to access the google sheets and drive APIs 
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

#retrieve credentials from secret keys json and authorize the file
credentials = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/admin/Desktop/BadmintonScraper/data/secret_keys.json', scopes)

file = gspread.authorize(credentials)
workbook = file.open('Copy of Ratings for badminton')
#opens the first sheet (index 0) in the workbook, can change 0 to the index of the sheet you want to open
sheet = workbook.get_worksheet(0)

#Player names and ratings are in columns F and G respectively
names_range = sheet.range("F3:F47")
ratings_range = sheet.range("G3:G47")

#Prints all player names and their ratings
for name_cell, rating_cell in zip(names_range, ratings_range):
    name = name_cell.value
    rating = rating_cell.value
    print(f"Player: {name}\n Rating: {rating}")

#Example to update a cell to "" at row 48, column 2
sheet.update_cell(48, 2, "")
