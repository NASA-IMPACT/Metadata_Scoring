# -*- coding: utf-8 -*-
'''
Metadata Scoring Script
------------------------
This metadata scoring approach is based on integrating the existing metrics used in the CMR dashboard record reviews.
The ARC team currently uses a hierarchy of colors and corresponding recommendations to produce quality assessments of
metadata. Thus, this script produces a score based on the colors that fields are given.

This script takes in a csv with column headings 'Concept_id' and 'Revision_id' and outputs a score for the collection 
and granule. The records in the csv will need to be reviewed in the CMR dashboard prior to running this script.
It prints these scores to the screen and also writes them to a new csv called 'Record_scores.csv'. 

The score is based on the following method: -1 for red fields, -0.5 for yellow fields, and -0.25 for blue fields. 
Gray fields do not have any effect on the score. 

Requirements for user
----------------------
The function requires the user to input his or her Earthdata login credentials in order to access the dashboard. It also 
requires the user to specify the file path for the csv with records that need to be scored. Reminder - these records 
should already be reviewed and the column headings should be 'Concept_id' and 'Revision_id'. The script uses selenium 
webdriver to access the dashboard, so chromedriver will need to be in the same directory as the script. If chromedriver 
is not already installed, it will need to be downloaded.

As mentioned above, these variables will need to be defined by the user in order to call the function/run the script:
user_name
pass_word
csv_file_path 

'''

# call function to score metadata - must pass in username and password for the CMR dashboard as well as the file path for the records that need to be scored
def metadata_scoring(user_name, pass_word, csv_file_path):
    
    import re
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup
    import pandas as pd
    import csv
    
    # opening dashboard in Chrome
    driver = webdriver.Chrome()
    driver.get('https://cmr-dashboard.earthdata.nasa.gov/home')
    
    # clicking on the login button
    button_element = driver.find_element_by_css_selector('body > div.wrapper > header > div > div.col-6.header-tools > a.eui-btn--blue')
    button_element.click()
    
    # find username and password elements within html
    username = driver.find_element_by_id("username")
    password = driver.find_element_by_id("password")
    
    # typing in username and password
    username.send_keys(user_name)
    password.send_keys(pass_word)
    
    # clicking login and driver waits to load home page - uses xpath of title
    driver.find_element_by_css_selector('#login > p.button-with-notes > input').click()
    WebDriverWait(driver,5).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[3]/div[1]/div[1]/h3')))
    
    # load html of home page                                    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # reads in csv and puts concept ids and revision ids in 2 separate lists, creates an empty list for collection and granule scores
    df = pd.read_csv(csv_file_path)
    Concept_ids = df['Concept_id'].dropna().tolist()
    Revision_ids = df['Revision_id'].dropna().tolist()
    Collection_score = []
    Granule_score = []
    
    # load html tables specific to concept id and revision id 
    for cID in Concept_ids:
        tables = soup.findChildren('td', text=re.compile(cID))
        for rID in Revision_ids:
            revision_id = str(rID)
            
            # appends record specific 'value' to url to get to metadata elements page (i.e. colors) and also specifies the granule specific 'value'
            baseURL = 'https://cmr-dashboard.earthdata.nasa.gov/records/'
            for i in tables:
                if (i.parent.find_all('td')[1].contents[0]) == revision_id:
                    collectionURL = baseURL + i.parent.find_all('td')[-1].contents[0]['value'] + "?"
                    granule_value = int(i.parent.find_all('td')[-1].contents[0]['value']) + 1
            
        #collectionURL = baseURL + tables.parent.find_all('td')[-1].contents[0]['value'] + "?"
        driver.get(collectionURL)
        
        # list of all fields reviewed                                              
        all_bubbles = driver.find_elements_by_class_name("single_bubble_container")
        
        # list of all green fields
        green_bubbles = driver.find_elements_by_class_name("bubble.flag_green.no_script.bubbletooltip")
        green_bubbles_script = driver.find_elements_by_class_name("bubble.flag_green.script.bubbletooltip")
        all_green_bubbles = green_bubbles + green_bubbles_script
        
        # list of all yellow fields
        yellow_bubbles = driver.find_elements_by_class_name("bubble.flag_yellow.no_script.bubbletooltip")
        yellow_bubbles_script = driver.find_elements_by_class_name("bubble.flag_yellow.script.bubbletooltip")
        all_yellow_bubbles = yellow_bubbles + yellow_bubbles_script
        
        # list of all blue fields
        blue_bubbles = driver.find_elements_by_class_name("bubble.flag_blue.no_script.bubbletooltip")
        blue_bubbles_script = driver.find_elements_by_class_name("bubble.flag_blue.script.bubbletooltip")
        all_blue_bubbles = blue_bubbles + blue_bubbles_script
        
        # list of all red fields
        red_bubbles = driver.find_elements_by_class_name("bubble.flag_red.no_script.bubbletooltip")
        red_bubbles_script = driver.find_elements_by_class_name("bubble.flag_red.script.bubbletooltip")
        all_red_bubbles = red_bubbles + red_bubbles_script
        
        # list of all gray fields
        gray_bubbles = driver.find_elements_by_class_name("bubble.flag_gray.no_script.bubbletooltip")
        gray_bubbles_script = driver.find_elements_by_class_name("bubble.flag_gray.script.bubbletooltip")
        all_gray_bubbles = gray_bubbles + gray_bubbles_script
        
        # total number of fields that aren't gray (gray fields should not impact score in any way)
        total_bubbles = len(all_bubbles) - len(all_gray_bubbles)
        
        # Calculate score - subtract 1 for red, 0.5 for yellow, and 0.25 for blue 
        raw_score = total_bubbles - ((len(all_red_bubbles)*1) + (len(all_yellow_bubbles)*.5) + (len(all_blue_bubbles)*0.25))
        collection_score = (raw_score / total_bubbles) * 100
        
        # append collection score to a list
        print("Collection Score:", collection_score)
        Collection_score.append(collection_score)
        
        
        # Expanding to granules (may be a more efficient way of doing this) - get granule url
        granuleURL = baseURL + str(granule_value) + "?"
        driver.get(granuleURL)
        
        # list of all fields reviewed                                              
        all_bubbles2 = driver.find_elements_by_class_name("single_bubble_container")
        
        # list of all green fields
        green_bubbles2 = driver.find_elements_by_class_name("bubble.flag_green.no_script.bubbletooltip")
        green_bubbles_script2 = driver.find_elements_by_class_name("bubble.flag_green.script.bubbletooltip")
        all_green_bubbles2 = green_bubbles2 + green_bubbles_script2
        
        # list of all yellow fields
        yellow_bubbles2 = driver.find_elements_by_class_name("bubble.flag_yellow.no_script.bubbletooltip")
        yellow_bubbles_script2 = driver.find_elements_by_class_name("bubble.flag_yellow.script.bubbletooltip")
        all_yellow_bubbles2 = yellow_bubbles2 + yellow_bubbles_script2
        
        # list of all blue fields
        blue_bubbles2 = driver.find_elements_by_class_name("bubble.flag_blue.no_script.bubbletooltip")
        blue_bubbles_script2 = driver.find_elements_by_class_name("bubble.flag_blue.script.bubbletooltip")
        all_blue_bubbles2 = blue_bubbles2 + blue_bubbles_script2
        
        # list of all red fields
        red_bubbles2 = driver.find_elements_by_class_name("bubble.flag_red.no_script.bubbletooltip")
        red_bubbles_script2 = driver.find_elements_by_class_name("bubble.flag_red.script.bubbletooltip")
        all_red_bubbles2 = red_bubbles2 + red_bubbles_script2
        
        # list of all gray fields
        gray_bubbles2 = driver.find_elements_by_class_name("bubble.flag_gray.no_script.bubbletooltip")
        gray_bubbles_script2 = driver.find_elements_by_class_name("bubble.flag_gray.script.bubbletooltip")
        all_gray_bubbles2 = gray_bubbles2 + gray_bubbles_script2
        
        # total number of fields that aren't gray (gray fields should not impact score in any way)
        total_bubbles2 = len(all_bubbles2) - len(all_gray_bubbles2)
        
        # Calculate score - subtract 1 for red, 0.5 for yellow, and 0.25 for blue 
        raw_score2 = total_bubbles2 - ((len(all_red_bubbles2)*1) + (len(all_yellow_bubbles2)*.5) + (len(all_blue_bubbles2)*0.25))
        granule_score = (raw_score2 / total_bubbles2) * 100
        
        # append granule score to a list
        print("Granule Score:", granule_score)
        Granule_score.append(granule_score)
    
    # write dataframe with the following columns: concept ids, revision ids, collection score, granule score
    df1 = pd.DataFrame()
    df1['Concept_id'] = Concept_ids
    df1['Revision_id'] =  Revision_ids
    df1['Collection_Score'] = Collection_score
    df1['Granule_score'] = Granule_score
    
    # Convert dataframe to csv
    df1.to_csv('Record_scores.csv', index = False)
