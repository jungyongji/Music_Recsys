import re
import bs4
import json
import time
import random
import numpy as np
import pandas as pd

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from user_agent import generate_user_agent
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException, TimeoutException



## Chromedriver options   
options = Options()
user = generate_user_agent(device_type='desktop')
options.add_argument(f'user-agent={user}')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('headless')        # 창 x
options.add_argument('--blink-settings=imagesEnabled=false')        # 이미지 x
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_experimental_option("excludeSwitches", ['load-extension, enable-automation', 'enable-logging'])
options.add_experimental_option('useAutomationExtension', False)


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


## Metadata and genre information load
def json_to_tsv(json_file, tsv_file):
    with open(json_file, encoding="UTF-8") as f:
        js = json.load(f)
        if isinstance(js, list):
            df = pd.DataFrame.from_records(js)
            df['song_gn_gnr_basket'] = df['song_gn_gnr_basket'].apply(lambda x : ','.join(x))
            df['song_gn_dtl_gnr_basket'] = df['song_gn_dtl_gnr_basket'].apply(lambda x : ','.join(x))
            df['artist_name_basket'] = df['artist_name_basket'].apply(lambda x : ','.join(x))
            df['artist_id_basket'] = df['artist_id_basket'].apply(lambda x : str(x)[1:-1])
        if isinstance(js, dict):
            df = pd.DataFrame.from_dict([js])
            df = df.transpose()
            df.reset_index(inplace = True)
            df.columns = ['genre_id', 'genre']
        df.to_csv(tsv_file, sep = '\t', index = None, encoding = 'utf-8')
    return df




## Preprocssing the genre of the song and the special symbol of html
def preprocessing(meta, genre : pd.DataFrame):
    
    #### genre filtering ####
    genre.columns = ['song_gn_gnr_basket', 'genre']
    '''
    GN1100	일렉트로니카
    GN1600	클래식
    GN1700	재즈
    GN1800	뉴에이지
    GN1900	J-POP
    GN2400	국악
    GN2600	일렉트로니카
    GN2700	EDM
    GN2800	뮤직테라피
    '''
    instrumental_music = ['GN1100', 'GN1600', 'GN1700', 'GN1800', 'GN1900', 'GN2400', 'GN2600', 'GN2700', 'GN2800']
    # Main genre
    main_genre = genre[genre['song_gn_gnr_basket'].str.contains('^.*00$', regex=True)]
    # Omitting the genre of instrumental music 
    ss_lyric_genre = main_genre[~main_genre['song_gn_gnr_basket'].isin(instrumental_music)]
    # Remove instrumental music among song with single and multi genre in metadata
    meta = meta[ np.vectorize(lambda x : bool(set(x.split(',')) & set(ss_lyric_genre['song_gn_gnr_basket']) ))(meta['song_gn_gnr_basket'])]
    meta.reset_index(drop = True, inplace = True)
    
    
    
    #### html special symbol filtering ####
    song_index = meta[meta['song_name'].str.contains("^.*(&#).*", regex= True, na = False)].index       #6015
    album_index = meta[meta['album_name'].str.contains("^.*(&#).*", regex= True, na = False)].index     #3320
    artist_index = meta[meta['artist_name_basket'].str.contains("^.*(&#).*", regex= True, na = False)].index        #327

    meta.loc[song_index, 'song_name'] \
    = meta.loc[song_index, 'song_name']\
    .apply(lambda x : bs4.BeautifulSoup(x, 'html.parser'))\
    .apply(lambda x : ','.join(x))

    meta.loc[album_index, 'album_name']\
    = meta.loc[album_index, 'album_name']\
    .apply(lambda x : bs4.BeautifulSoup(x, 'html.parser'))\
    .apply(lambda x : ','.join(x))

    meta.loc[artist_index, 'artist_name_basket']\
    = meta.loc[artist_index, 'artist_name_basket']\
    .apply(lambda x : bs4.BeautifulSoup(x, 'html.parser'))\
    .apply(lambda x : ','.join(x))

    meta = meta[~meta['song_name'].str.contains("inst", flags = re.I, na = False)]
    meta = meta[~meta['song_name'].str.contains("(대사)(\)|\s)", regex = True, na = False)]

    meta.to_csv('metadata_filtered.tsv', sep = '\t', index = None, encoding = 'utf-8')
    return meta




## Extracdtion name of album and song from metadata
def queue_pop_columns_from_df(dataframe, album_col, song_col, artist_col):
    for album, song, artist, index in zip(dataframe[album_col], dataframe[song_col], dataframe[artist_col], dataframe.index):
        if index % 200 == 0 :
            driver.delete_all_cookies()
            user = generate_user_agent(device_type='desktop')
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user})
        yield [index, album, song, artist]



def lyrics_from_song_total(keyword, song):
    results = {}
    url = f'https://www.melon.com/index.htm'
    driver.get(url)

    search_box = WebDriverWait(driver, 1+random.random()).until(lambda driver: driver.find_element(By.CLASS_NAME, "ui-autocomplete-input"))
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)

    song = song + " 좋아요"
    try:
        song_elements = WebDriverWait(driver, 1+random.random()).until(lambda driver: driver.find_elements(By.CLASS_NAME, "btn_icon.like"))
        song_list = [x.get_attribute("title") for x in song_elements]
        index = [song_list.index(x) for x in song_list if set(song).issubset(x)][0]     ##IndexError
        song_id = driver.find_elements(By.CLASS_NAME, "btn_icon.like")[index].get_attribute("data-song-no")     ##IndexError

        url = f'https://www.melon.com/song/detail.htm?songId={song_id}'
        driver.get(url)
        time.sleep(0.5+random.random())
        
        driver.find_element(By.CLASS_NAME, "button_icons.etc.arrow_d").click()      ## NoSuchElementException
        time.sleep(random.random())
        lyric = driver.find_element(By.CLASS_NAME, "lyric.on").text     ## NoSuchElementException
        time.sleep(0.5+random.random())

    except (NoSuchElementException, ElementNotInteractableException,ElementNotInteractableException):
        lyric = "-"
        print("NoSuchElementException", end = "  ")
        time.sleep(1+random.random())

    except (TimeoutException, IndexError):
        song_id = "-"
        lyric = "-"
        print("Timeout or Index Exception", end = "    ")
        time.sleep(1+random.random())

    lyric = re.sub("[\n]+", " ", lyric)

    results['lyric'] = lyric
    results['song_id'] = song_id
    print("Complete!", end = "  ")
    
    return results



def extract_lyricNsongId(album_song : list) -> pd.DataFrame:
    index, album, song, artist = album_song
    keyword = ', '.join(filter(None, [song, album, artist]))

    print(f'Index = {index}, Song = {song},     Album = {album},    Artist = {artist}       ', end = '')
    results = lyrics_from_song_total(keyword, song)
    lyric = results['lyric'][:5]
    song_id = results['song_id']
    print(f'Lyric = {lyric},     ID = {song_id}')

    return results




if __name__ == '__main__':
    start_index = 0
    end_index = start_index + 10000
    genre = json_to_tsv("genre_gn_all.json", "genre_gn_all.tsv")
    meta = json_to_tsv("song_meta.json", "song_meta.tsv")
    meta = preprocessing(meta, genre)
    
    ## 파이썬의 Na 값은 파일로 저장할때랑, 불러올때 다르게 반환된다.
    ## 가장 마지막에 Na값을 바꾸는게 맞음
    ## nan NaN은 숫자 무한대와 같으므로, float형이다
    meta = pd.read_csv("metadata_filtered.tsv", sep = '\t')

    meta.replace(float("NaN"), None, inplace = True)
    meta.replace("N/A", None, inplace = True)
    meta.fillna('', inplace = True)
    meta.replace("\`","\'", regex= True, inplace = True)
    print(len(meta))

    meta = meta.iloc[start_index:end_index,:]
    
    start = time.time()
    try:
        album_song_df = pd.DataFrame(map(extract_lyricNsongId, queue_pop_columns_from_df(meta, "album_name", "song_name","artist_name_basket")), index = meta.index)
        album_song_df.reset_index(inplace = True)
    finally:
        print(album_song_df)
    print(f"time : {(time.time()-start)/3600}hour")


    album_song_df = album_song_df.iloc[:,1:]

    meta.reset_index(inplace = True)    
    meta_with_album_song_df = pd.concat([meta, album_song_df], axis=1)
    print(meta_with_album_song_df)
    meta_with_album_song_df.to_csv(f'meta_lyric_{start_index}to{end_index}.tsv', index = None, sep = '\t', encoding = 'utf-8')
    
    now = datetime.now()
    print(now)