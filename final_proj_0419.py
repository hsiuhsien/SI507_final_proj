#################################
##### Name: Christina (HsiuHsien) Chen
##### Uniqname: hsiu
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import sqlite3

# Cache variables
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

# Database variables
DBNAME = 'yelpcafe.sqlite'
conn = sqlite3.connect(DBNAME)
cur = conn.cursor()

# API variables
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'

# Cafe Instance
class Cafe:
    def __init__(self, id, yelpid, name, rating, numberofreviews, state, city, fulladdress, zipcode, phonenumber, yelpurl):
        self.id = id
        self.yelpid = yelpid
        self.name = name
        self.rating = rating
        self.numberofreviews = numberofreviews
        self.state = state
        self.city = city
        self.fulladdress = fulladdress
        self.zipcode = zipcode
        self.phonenumber = phonenumber
        self.yelpurl = yelpurl

# Category Instance
class Category:
    def __init__(self, id, title, alias):
        self.id = id
        self.title = title
        self.alias = alias

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache): # called whenever the cache is changed
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

# Load the cache, save in global variable
CACHE_DICT = load_cache()

# Create Database
def create_db_table():
    conn = sqlite3.connect("yelpcafe.sqlite")
    cur = conn.cursor()

    drop_cafe = 'DROP TABLE IF EXISTS "Cafe"'
    drop_category = 'DROP TABLE IF EXISTS "Category"'
    drop_cafe_category = 'DROP TABLE IF EXISTS "Cafe_Category"'

    create_cafe = '''
        CREATE TABLE IF NOT EXISTS "Cafe" (
            "Id"                INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "YelpId"            TEXT NOT NULL,
            "Name"              TEXT NOT NULL,
            "Rating"            REAL,
            "NumberOfReviews"   INTEGER,
            "State"             TEXT,
            "City"              TEXT,
            "FullAddress"       TEXT,
            "ZipCode"           INTEGER,
            "PhoneNumber"       TEXT,
            "YelpURL"           TEXT
        );
    '''
    create_category = '''
        CREATE TABLE IF NOT EXISTS "Category" (
            "Id"                INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Title"             TEXT NOT NULL,
            "Alias"             TEXT NOT NULL
        );
    '''
    create_cafe_category = '''
        CREATE TABLE IF NOT EXISTS "Cafe_Category" (
            "CafeId"            INTEGER NOT NULL,
            "CategoryId"        INTEGER NOT NULL,
            FOREIGN KEY(CafeId) REFERENCES Cafe(Id)
            FOREIGN KEY(CategoryId) REFERENCES Category(Id)
        );
    '''

    cur.execute(drop_cafe)
    cur.execute(drop_category)
    cur.execute(drop_cafe_category)

    cur.execute(create_cafe)
    cur.execute(create_category)
    cur.execute(create_cafe_category)

    conn.commit()

# Insert data to given table
def insertDataToDB(table, data):
    if table == 'cafe':
        insert = 'INSERT INTO Cafe VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'category':
        insert = 'INSERT INTO Category VALUES (NULL, ?, ?)'
    elif table == 'cafe_category':
        insert = 'INSERT INTO Cafe_Category VALUES (?, ?)'
  
    cur.execute(insert, data)
    conn.commit()
    lastInsertedId= cur.lastrowid
    return lastInsertedId

# Gets Category with given Alias
def getCategoryByAlias(alias):
    query = f''' 
            SELECT Id, Title, Alias 
            FROM Category 
            WHERE Alias = "{0}"
            '''
    result = cur.execute(query).fetchone()
    if result != None:
        return Category(result[0], result[1], result[2])
    return result

# Gets Cafe with given Yelp ID
def getCafeByYelpId(yelpid):
    query = f''' 
        SELECT Id, YelpId, Name, Rating, NumberOfReviews, State, City, FullAddress, ZipCode, PhoneNumber, YelpURL   
        FROM Cafe 
        WHERE YelpId = "{yelpid}"
        '''
    result = cur.execute(query).fetchone()
    if result != None:
        return Cafe(result[0], result[1], result[2], result[3], result[4], result[5],
            result[6], result[7], result[8], result[9], result[10])
    return result 

# Adds {Cafe, Category} relationship to database by looping through each category
def insertCafeCategories(cafeId, categories):
    for c in categories:
        values = [cafeId, c]
        insertDataToDB('cafe_category', values)

# Gets a list of IDs associated with given categories
def getCategoryIds(categories):
    ids = []
    for c in categories:
        category = getCategoryByAlias(c['alias'])
        if category == None:
            category_values = [c['title'], c['alias']]
            id = insertDataToDB('category', category_values)
        else:
            id = category.id
        ids.append(id)
    return ids

# Adds data to database tables
def insertCafes(cafes):
    cafeList = []
    for c in cafes:
        cafe = getCafeByYelpId(c['id'])
        if cafe == None:
            # Only need to do inserts if Cafe hasn't been added to database before
            yelpid = c['id']
            name = c['name']
            rating = c['rating']
            reviewcount = c['review_count']
            state = c['location']['state']
            city = c['location']['city']
            address = ', '.join(c['location']['display_address'])
            zipcode = c['location']['zip_code']
            phone = c['display_phone']
            url = c['url']
            cafe_values = [yelpid, name, rating, reviewcount, state, city, address, zipcode, phone, url]
            categories = getCategoryIds(c['categories'])
            cafeId = insertDataToDB('cafe', cafe_values)
            insertCafeCategories(cafeId, categories)
            cafe = Cafe(cafeId, yelpid, name, rating, reviewcount, state, city, address, zipcode, phone, url)
        cafeList.append(cafe)
    return cafeList

# Sends request to Yelp Fusion API, Business Endpoint
def request(url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(API_HOST, SEARCH_PATH)
    headers = {
        'Authorization': secrets.API_KEY,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()

# Searches for coffee shops at given location
# Process results and store each item in the database
# Returns top 10 result to be stored in the cache
def searchByLocation(location):
    url_params = {
        'categories': 'coffee',
        'location': location.replace(' ', '+'),
        'limit': 50,
        'sort_by': 'rating'
    }
    results = request(url_params)
    cafes = insertCafes(results.get('businesses'))
    return cafes[:10]

# Checks cache to see if give location has been processed before
def make_request_using_cache(location):
    if location in CACHE_DICT.keys():
        return CACHE_DICT[location]
    else:
        data = searchByLocation(location)
        CACHE_DICT[location] = data
        save_cache(CACHE_DICT)
        return data

def main():
    while True:
        # Gets user input of location
        location = input('Enter a city, state (e.g. San Francisco, CA or Ann Arbor, MI) or "exit" \n: ')

        if location.lower() == "exit":
            exit()
        else:
            top10 = make_request_using_cache(location.lower())
            for item in top10:
                print('{0} ({1})'.format(item.name, item.rating))

                
if __name__ == '__main__':
    main()