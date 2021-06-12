import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from pandas as pd

import requests

from time import localtime, strftime
from pymongo import MongoClient
import re
from src import myconfig
import datetime
import pdb

"""셀레니움과 뷰티풀숩을 통해 유튜브와
디시인사이드 넷플릭스 갤러리를 크롤링하고
csv 파일로 저장함"""

df = pd.DataFrame({'제목': [],
                   '글쓴이': [],
                   '날짜' : [],
                   '조회 수' : [],
                   '추천 수' : []})

def crawl_dcinside(logger, page=50):
    for num in range(1, page):
        params = {'id': 'netflix', 'page' : f'{num}'}
        headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'}
        resp = requests.get(dc_url, params=params, headers=headers)
        soup = BeautifulSoup(resp.content, 'html.parser')
        contents = soup.find('tbody').find_all('tr')
        page_size = len(contents)

        for i in contents:
            line = []

            # 제목 추출
            title_tag = i.find('a')
            title = title_tag.text
            line.append(title)

            # 글쓴이 추출
            writer_tag = i.find('td', class_='gall_writer ub-writer').find('span', class_='nickname')

            if writer_tag is not None:
                writer = writer_tag.text
                line.append(writer)
            else:
                line.append("없음")


            # 날짜 추출
            date_tag = i.find('td', class_='gall_date')
            date_dict = date_tag.attrs

            if len(date_dict) == 2:
                line.append(date_dict['title'])

            else:
                line.append(date_tag.text)
                pass

            # 조회 수 추출
            views_tag = i.find('td', class_='gall_count')
            views = views_tag.text
            line.append(views)

            # 추천 수 추출
            recommend_tag = i.find('td', class_='gall_recommend')
            recommend = recommend_tag.text
            line.append(recommend)

            df = df.append(pd.Series(line, index=df.columns), ignore_index=True)
    
    return df

def crawl_youtube(logger, country='Korea', pagedown=5):
    delay=3
    browser = Chrome()
    browser.implicitly_wait(delay)

    start_url  = \
            ('https://www.youtube.com/c/Netflix%d' % country) + \
            '/videos?view=0&sort=p&flow=grid'
    browser.get(start_url)

    body = browser.find_element_by_tag_name('body')

    num_of_pagedowns = pagedown

    while num_of_pagedowns:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
        num_of_pagedowns -= 1

    page = browser.page_source
    soup = BeautifulSoup(page,'lxml')

    all_title = soup.find_all('a','yt-simple-endpoint style-scope ytd-grid-video-renderer')
    title = [soup.find_all('a','yt-simple-endpoint style-scope ytd-grid-video-renderer')[n].string for n in range(0,len(all_title))]

    #조회수, 올린지 얼마나 되었는지(업로드 시점)
    c = soup.find_all('span','style-scope ytd-grid-video-renderer')
    view_num = [soup.find_all('span','style-scope ytd-grid-video-renderer')[n].string for n in range(0,len(c))]

    youtube_video_list = []

    #조회수의 index
    x = 0

    #업로드 시점의 index
    y = 1

    for i in range(0,len(all_title)):
        roww = []
        roww.append(title[i])

        roww.append(view_num[x])
        x += 2

        roww.append(view_num[y])
        y += 2

        youtube_video_list.append(roww)

    netflix_youtube = pd.DataFrame(youtube_video_list)
    netflix_youtube.columns = ["title", "view", "date"]
    return netflix_youtube
