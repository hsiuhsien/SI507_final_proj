#################################
##### Name: Christina (HsiuHsien) Chen
##### Uniqname: hsiu
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import sqlite3
import plotly.graph_objects as go 

# Cache variables
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

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
        
        for city in cache.keys():
            for index, item in enumerate(cache[city]):
                instance = object.__new__(Cafe)
                for key, value in item.items():
                    setattr(instance, key, value)
                cache[city][index] = instance
        return cache
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache, default=lambda x: x.__dict__)
    cache_file.write(contents_to_write)
    cache_file.close()

# Load the cache, save in global variable
CACHE_DICT = load_cache()

#Create DB file and tables
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
        WHERE Alias = "{alias}"
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
        'Authorization': 'Bearer %s' % secrets.API_KEY,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()

# Searches for coffee shops at given location
def searchByLocation(location):
    url_params = {
        'categories': 'coffee',
        'location': location.replace(' ', '+'),
        'limit': 50,
        'sort_by': 'rating'
    }
    results = request(url_params)
    cafes = insertCafes(results.get('businesses'))
    # return first 10
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

# Format the printed result
def print_format(result):
    
    row = "{i:6} {name:<20} {rating:<8} {numberofreviews:<6}".format

    for i in range(len(result)):
        shortenedName = result[i].name
        if len(result[i].name) > 15:
            shortenedName = result[i].name[:15]+'...'
        print(row(i='['+str(i+1)+']', name=shortenedName, rating=result[i].rating, numberofreviews=result[i].numberofreviews))
        i = i+1

# Format the cafe detail data
def print_detail(shop):
    detail_list = [('Shop Name:', shop.name), ('Rating:', shop.rating), ('Number of Reviews:', shop.numberofreviews), ('Address:', shop.fulladdress), ('Phone Number:', shop.phonenumber), ('Yelp URL:', shop.yelpurl)]

    row = "{Headers:<20} {contect:<15}".format

    for r in detail_list:
        print(row(Headers=r[0], contect=r[1]))

# Creat plotly bar chart for rating
def rating_barplot(result):
    xvals_list = []
    yvals_list = []
    for list in result:
        shop = list.name
        xvals_list.append(shop)
        rating = list.rating
        yvals_list.append(rating)

    xvals = xvals_list
    yvals = yvals_list

    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Comparison of Cafe Rating")
    fig = go.Figure(data=bar_data, layout=basic_layout)

    fig.show()

# Creat plotly bar chart for number of reviews
def numberofreviews_barplot(result):
    xvals_list = []
    yvals_list = []
    for list in result:
        shop = list.name
        xvals_list.append(shop)
        numberofreviews = list.numberofreviews
        yvals_list.append(numberofreviews)

    xvals = xvals_list
    yvals = yvals_list

    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Comparison of Cafe Number of Reviews")
    fig = go.Figure(data=bar_data, layout=basic_layout)

    fig.show()

# List of US states
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

def main():
    while True:
        location = input('Enter a city, state (e.g. San Francisco, CA or Ann Arbor, MI) or "exit" :\n')

        if location.lower() == "exit":
            exit()
        else:
            location_state = location.split(",")[1].replace(" ", "").upper()
            if location_state in states:
                top10 = make_request_using_cache(location.lower())
                headline = ["Number", "Name", "Rating", "Number of Reviews"]
                row = "{number:<6} {name:<20} {rating:<8} {numberofreviews:<6}".format
                print ("--------------------------------------------------------")
                print (f"List of Top 10 Cafe in {location}")
                print ("--------------------------------------------------------")
                print(row(number= headline[0], name=headline[1], rating=headline[2], numberofreviews=headline[3]))
                shop_list = sorted(top10, key=lambda item: item.rating, reverse=True)
                print_format(shop_list)
                print ("--------------------------------------------------------")
                while True:
                    detail = input('Choose the number for detail search or input "barchart" to see the comparison (or "exit"/"back") :\n')
                    if detail.isnumeric() and int(detail) != 0 and int(detail) <= 10: 
                        site_detail = shop_list[int(detail) - 1]
                        site_name = site_detail.name
                        print("--------------------------------------------------------")
                        print("Detail information of " + site_name + " :") 
                        print("--------------------------------------------------------")
                        print_detail(site_detail)
                        print("--------------------------------------------------------")
                    elif detail.lower() == "back": 
                        break 
                    elif detail.lower() == "exit":
                        exit()
                    elif detail.lower() == "barchart":
                        print("--------------------------------------------------------")
                        option = input("Choose the number for comparison type\n1. Rating\n2. Number of Reviews\n:")
                        if int(option) == 1:
                            rating_barplot(shop_list)
                            print("--------------------------------------------------------")
                            continue
                        elif int(option) == 2:
                            numberofreviews_barplot(shop_list)
                            print("--------------------------------------------------------")
                            continue
                    else:
                        print("[Error] Invalid input\n")
            else:
                print("[Error] Invalid input\n")
                continue
            
                
if __name__ == '__main__':
    main()