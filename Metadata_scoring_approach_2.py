# -*- coding: utf-8 -*-
"""
Metadata Scoring Approach 2
----------------------------
This is currently a first pass of the checks - still a work in progress.

User needs to put in username, password, and csv_file_path of records that need to be scored. Additionally, the granule data format
csv needs to be in the same directory as this script. The csv witht he records listed needs to have a column called 'Concept_id' 
and a column called 'Revision_id'. Chrome webdriver also needs to be in the same directory as this script.

"""
def metadata_scoring2(user_name, pass_word, csv_file_path):
    
    import json
    import urllib.request
    from urllib.request import urlopen
    import pandas as pd
    
    import re
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup
    
    # import csv file with test records that need to be scored
    #csv_file_path = 'C:/Users/Jenny/Desktop/Metadata_scoring/Test_records_3.csv'
    df = pd.read_csv(csv_file_path)
    data_format_csv = 'GranuleDataFormat.csv'
    df_csv = pd.read_csv(data_format_csv)
    
    # change Concept id and Revision id columns to lists
    Concept_ids = df['Concept_id'].dropna().tolist()
    Revision_ids = df['Revision_id'].dropna().tolist()
    Data_Formats = df_csv['Keyword Version: 9.1.5'].dropna().tolist()
    
    # get url with metadata information for each record in the list
    base_url = 'https://cmr.earthdata.nasa.gov/search/concepts/'
    info_urls = []
    automatic_score = []
    manual_score = []
    
    for cID in range(len(Concept_ids)):
        info_urls.append(base_url + Concept_ids[cID] + '/' + str(Revision_ids[cID]) + '.umm-json')
    
    # AUTOMATIC CHECKS: Perform checks to see what's included in metadata and score appropriately
    for url in info_urls:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        
        # records start with a score of 0
        score = 0
        
        # DATA DISCOVERY CHECKS
        # Check to see if access constraints field is populated
        if 'AccessConstraints' in data:
            score+=1
        else:
            score+=0
            
        # Check whether entry title and short name are identical
        if data['EntryTitle'] != data['ShortName']:
            score+=1
        else:
            score+=0
            
        # check to see if science keywords are provided
        if data['ScienceKeywords'][0]['Category'] == 'Not provided':
            score+=0
        elif data['ScienceKeywords'][0]['Topic'] == 'Not provided':
            score+=0
        elif data['ScienceKeywords'][0]['Term'] == 'Not provided':
            score+=0
        else:
            score+=1
        
        # Check to see if DOI field exists - what if doi = Not provided, what if doi exists but not populated
        if 'DOI' in data:
            score+=1
        else:
            score+=0
            
        # DATA ACCESSIBILITY CHECKS
        # unsure if these lists are complete
        subtypes1 = ['WEB MAP SERVICE (WMS)', 'WEB COVERAGE SERVICE (WCS)', 'OPENDAP DATA', 'GIOVANNI', 'THREDDS DATA', 'WORLDVIEW']
        subtypes2 = ['WEB MAP SERVICE (WMS)', 'WEB COVERAGE SERVICE (WCS)', 'OPENDAP DATA']
        # check to see if at least one link has the type 'GET DATA'
        if 'RelatedUrls' in data:
            related_urls = data['RelatedUrls']
            for url in related_urls:
                if url['Type']=='GET DATA':
                    score+=1 # if there's more than one 'GET DATA' link it will add more than one to the score
                else:
                    score+=0
                # This is actually a data usability check
                if url['Type']=='VIEW RELATED INFORMATION':
                    score+=1 # if there's more than one 'VIEW RELATED INFO' link it will add more than one to the score
                else:
                    score+=0
                if 'Subtype' in url:
                    if url['Subtype'] in subtypes1:
                        score+=1 # if there's more than one subtype match, it will add more than one to the score
                    else:
                        score+=0
                    if url['Subtype'] in subtypes2:
                        score+=1 #if there's more than one subtype match, it will add more than one to the score
                    else:
                        score+=0
        
        # DATA USABILITY CHECKS  
        # check to see if version field is populated
        if 'Version' in data:
            score+=1
        else:
            score+=0
        
        # check to see if quality field is populated    
        if 'Quality' in data:
            score+=1
        else:
            score+=0
        
        #Check to see if collection progress field meets criteria - should any other things be included?
        if data['CollectionProgress'] == 'PLANNED':
            score+=1
        elif data['CollectionProgress'] == 'IN WORK':
            score+=1
        elif data['CollectionProgress'] == 'ACTIVE':
            score+=1
        elif data['CollectionProgress'] == 'COMPLETE':
            score+=1
        else:
            score+=0
            
        # Check to see if data format info is provided and whether it matches the accepted formats
        if 'ArchiveAndDistributionInformation' in data:
            score+=1
            data_format = data['ArchiveAndDistributionInformation']['FileDistributionInformation'][0]['Format']
            if data_format in Data_Formats:
                score += 1
            else: 
                score+=0
        else:
            score+=0
        
        # check to see if spatial information is provided
        if 'SpatialExtent' in data:
            score+=1
        else:
            score+=0
        
        # check to see if temporal information is provided
        if 'TemporalExtents' in data:
            score+=1
        else:
            score+=0
    
        automatic_score.append(score)
        print('Score:', score)
    
    # Dashboard Manual Checks
           
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
    #tables = soup.findChildren('td', text=re.compile('C1703403055-PODAAC'))
    for cID in Concept_ids:
        tables = soup.findChildren('td', text=re.compile(cID))
        for rID in Revision_ids:
            revision_id = str(rID)
            
    # appends record specific 'value' to url to get to metadata elements page (i.e. colors) and also specifies the granule specific 'value'
            baseURL = 'https://cmr-dashboard.earthdata.nasa.gov/records/'
            for i in tables:
                if (i.parent.find_all('td')[1].contents[0]) == revision_id:
                    collectionURL = baseURL + i.parent.find_all('td')[-1].contents[0]['value'] + "?"
        
                    driver.get(collectionURL)
                    
                    soup2 = BeautifulSoup(driver.page_source, 'html.parser')
                    score = 0
                    # ECHO 10
                    if(soup2.findChildren('p', text = re.compile('FORMAT : echo10'))):
                        # check to see if restriction comment is red/yellow
                        echo10_restriction = soup2.findChildren('p', text = re.compile('RestrictionComment'))
                        flag_color = str(echo10_restriction[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # Check to see if abstract is red/yellow
                        echo10_abstract = soup2.findChildren('p', text = re.compile('Description'))
                        flag_color = str(echo10_abstract[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if category science keyword is red/yellow
                        echo10_category = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / CategoryKeyword'))
                        flag_color = str(echo10_category[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if topic science keyword is red/yellow
                        echo10_topic = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / TopicKeyword'))
                        flag_color = str(echo10_topic[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1   
                        # check to see if term keyword is red/yellow
                        echo10_term = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / TermKeyword'))
                        flag_color = str(echo10_term[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1  
                        # check to see if variable 1 keyword is red/yellow
                        echo10_var1 = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / VariableLevel 1Keyword / Value'))
                        flag_color = str(echo10_var1[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1   
                        # check to see if variable 2 keyword is red/yellow
                        echo10_var2 = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / VariableLevel 2Keyword / Value'))
                        flag_color = str(echo10_var2[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 3 keyword is red/yellow
                        echo10_var3 = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / VariableLevel 3Keyword / Value'))
                        flag_color = str(echo10_var3[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if detailed variable keyword is red/yellow
                        echo10_devar = soup2.findChildren('p', text = re.compile('ScienceKeywords / ScienceKeyword / DetailedVariableKeyword'))
                        flag_color = str(echo10_devar[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if collection progress is red/yellow
                        echo10_progress = soup2.findChildren('p', text = re.compile('CollectionState'))
                        flag_color = str(echo10_progress[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if spatial info is red/yellow
                        echo10_west = soup2.findChildren('p', text = re.compile('Spatial / HorizontalSpatialDomain / Geometry / BoundingRectangle / WestBoundingCoordinate'))
                        flag_color = str(echo10_west[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        echo10_north = soup2.findChildren('p', text = re.compile('Spatial / HorizontalSpatialDomain / Geometry / BoundingRectangle / NorthBoundingCoordinate'))
                        flag_color = str(echo10_north[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        echo10_east = soup2.findChildren('p', text = re.compile('Spatial / HorizontalSpatialDomain / Geometry / BoundingRectangle / EastBoundingCoordinate'))
                        flag_color = str(echo10_east[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        echo10_south = soup2.findChildren('p', text = re.compile('Spatial / HorizontalSpatialDomain / Geometry / BoundingRectangle / SouthBoundingCoordinate'))
                        flag_color = str(echo10_south[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if temporal information is red/yellow
                        echo10_temporal = soup2.findChildren('p', text = re.compile('Temporal / RangeDateTime / BeginningDateTime'))
                        flag_color = str(echo10_temporal[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                    # DIF 10
                    elif(soup2.findChildren('p', text = re.compile('FORMAT : dif10'))):
                        # check to see if access constraints are red/yellow
                        dif10_restriction = soup2.findChildren('p', text = re.compile('Access_Constraints'))
                        flag_color = str(dif10_restriction[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if abstract is red/yellow
                        dif10_abstract = soup2.findChildren('p', text = re.compile('Summary / Abstract'))
                        flag_color = str(dif10_abstract[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if category science keyword is red/yellow
                        dif10_category = soup2.findChildren('p', text = re.compile('Science_Keywords / Category'))
                        flag_color = str(dif10_category[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if topic science keyword is red/yellow
                        dif10_topic = soup2.findChildren('p', text = re.compile('Science_Keywords / Topic'))
                        flag_color = str(dif10_topic[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if term science keyword is red/yellow
                        dif10_term = soup2.findChildren('p', text = re.compile('Science_Keywords / Term'))
                        flag_color = str(dif10_term[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 1 keyword is red/yellow
                        dif10_var1 = soup2.findChildren('p', text = re.compile('Science_Keywords / Variable_Level_ 1'))
                        flag_color = str(dif10_var1[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 2 keyword is red/yellow
                        dif10_var2 = soup2.findChildren('p', text = re.compile('Science_Keywords / Variable_Level_ 2'))
                        flag_color = str(dif10_var2[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 3 keyword is red/yellow
                        dif10_var3 = soup2.findChildren('p', text = re.compile('Science_Keywords / Variable_Level_ 3'))
                        flag_color = str(dif10_var3[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if detailed variable keyword is red/yellow
                        dif10_devar = soup2.findChildren('p', text = re.compile('Science_Keywords / Detailed_Variable'))
                        flag_color = str(dif10_devar[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if collection progress is red/yellow
                        dif10_progress = soup2.findChildren('p', text = re.compile('Dataset_Progress'))
                        flag_color = str(dif10_progress[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                         # check to see if spatial info is red/yellow
                        dif10_west = soup2.findChildren('p', text = re.compile('Spatial_Coverage / Geometry / Bounding_Rectangle / Westernmost_Longitude'))
                        flag_color = str(dif10_west[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        dif10_north = soup2.findChildren('p', text = re.compile('Spatial_Coverage / Geometry / Bounding_Rectangle / Northernmost_Latitude'))
                        flag_color = str(dif10_north[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        dif10_east = soup2.findChildren('p', text = re.compile('Spatial_Coverage / Geometry / Bounding_Rectangle / Easternmost_Longitude'))
                        flag_color = str(dif10_east[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        dif10_south = soup2.findChildren('p', text = re.compile('Spatial_Coverage / Geometry / Bounding_Rectangle / Southernmost_Latitude'))
                        flag_color = str(dif10_south[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        #check to see if temporal info is red/yellow
                        dif10_temporal = soup2.findChildren('p', text = re.compile('Temporal_Coverage / Range_DateTime / Beginning_Date_Time'))
                        flag_color = str(dif10_temporal[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                    # UMM-JSON
                    elif(soup2.findChildren('p', text = re.compile('FORMAT : umm_json'))):
                        # not sure if there's an acess constraints field in umm
                        # check to see if abstract is red/yellow
                        umm_abstract = soup2.findChildren('p', text = re.compile('Abstract'))
                        flag_color = str(umm_abstract[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if category science keyword is red/yellow
                        umm_category = soup2.findChildren('p', text = re.compile('ScienceKeywords / Category'))
                        flag_color = str(umm_category[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if topic science keyword is red/yellow
                        umm_topic = soup2.findChildren('p', text = re.compile('ScienceKeywords / Topic'))
                        flag_color = str(umm_topic[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if term science keyword is red/yellow
                        umm_term = soup2.findChildren('p', text = re.compile('ScienceKeywords / Term'))
                        flag_color = str(umm_term[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 1 keyowrd is red/yellow
                        umm_var1 = soup2.findChildren('p', text = re.compile('ScienceKeywords / VariableLevel 1'))
                        flag_color = str(umm_var1[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 2 keyword is red/yellow
                        umm_var2 = soup2.findChildren('p', text = re.compile('ScienceKeywords / VariableLevel 2'))
                        flag_color = str(umm_var2[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if variable 3 keyword is red/yellow
                        umm_var3 = soup2.findChildren('p', text = re.compile('ScienceKeywords / VariableLevel 3'))
                        flag_color = str(umm_var3[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if detailed variable keyword is red/yellow
                        umm_devar = soup2.findChildren('p', text = re.compile('ScienceKeywords / DetailedVariable'))
                        flag_color = str(umm_devar[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if collection progress is red/yellow
                        umm_progress = soup2.findChildren('p', text = re.compile('CollectionProgress'))
                        flag_color = str(umm_progress[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if spatial info is red/yellow
                        umm_west = soup2.findChildren('p', text = re.compile('SpatialExtent / HorizontalSpatialDomain / Geometry / BoundingRectangles / WestBoundingCoordinate'))
                        flag_color = str(umm_west[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        umm_north = soup2.findChildren('p', text = re.compile('SpatialExtent / HorizontalSpatialDomain / Geometry / BoundingRectangles / NorthBoundingCoordinate'))
                        flag_color = str(umm_north[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        umm_east = soup2.findChildren('p', text = re.compile('SpatialExtent / HorizontalSpatialDomain / Geometry / BoundingRectangles / EastBoundingCoordinate'))
                        flag_color = str(umm_east[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        umm_south = soup2.findChildren('p', text = re.compile('SpatialExtent / HorizontalSpatialDomain / Geometry / BoundingRectangles / SouthBoundingCoordinate'))
                        flag_color = str(umm_south[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                        # check to see if temporal info is red/yellow
                        umm_temporal = soup2.findChildren('p', text = re.compile('TemporalExtents / RangeDateTimes / BeginningDateTime'))
                        flag_color = str(umm_temporal[0].parent)
                        if 'red' in flag_color:
                            score += 0
                        elif 'yellow' in flag_color:
                            score += 0
                        else:
                            score+=1
                    print(score)
                    manual_score.append(score)
     
    # adding automatic score and manual score together               
    total_score = [x + y for x, y in zip(automatic_score, manual_score)]
    print('Total_scores:', total_score)
