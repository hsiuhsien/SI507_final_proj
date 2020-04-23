# SI507_final_proj

Apply for API Key : 
1.  follow the Anthentication instruction here to get your own API KEY
    https://www.yelp.com/developers/documentation/v3/authentication
2.  Create a new python file call "secrets.py" and store your API KEY as below format.
    API_KEY=" your own API KEY "

Interact with the program:
1.  Please import below required Python packages 
    import requests
    import sqlite3
    import plotly.graph_objects as go 

2.  You are able to interact with the prgram in four different steps.
    
    2.1 Follow by "'Enter a city, state (e.g. San Francisco, CA or Ann Arbor, MI) or "exit" :" and input the name of a city in the US, with "City, State" format.
    You will then see the top10 Cafe shown by rating of that city
    
    2.2 Follow by "'Choose the number for detail search or input "barchart" to see the comparison (or "exit"/"back")" and input the number of the Cafe shop to see detail information, including shop name, rating, number of reviews, address, phone number and Yelp URL.

    2.3 input "barchart", and follow by "Choose the number for comparison type 
    1. Rating / 2. Number of Reviews:" to input the number that you would like to see for plotly bar chart.

    2.4 If you enter 1, your browser will pop up the Comparison of Cafe Rating
        If you enter 2, your browser will pop up the Comparison of Cafe Number of Reviews