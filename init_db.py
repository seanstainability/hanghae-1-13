import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient

client = MongoClient('13.125.123.139', 27017, username="seanstainability", password="spnm24365!")
db = client.horror


# DB에 저장할 영화들의 url 가져오기
def get_movies():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get('https://movie.naver.com/movie/sdb/rank/rmovie.nhn?sel=pnt&date=20210607&tg=4', headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    movies = soup.select('#old_content > table > tbody > tr > td.title > div')
    print(movies)

    urls = []
    for movie in movies:
        a = movie.select_one('a')
        if a is not None:
            base_url = 'https://movie.naver.com/'
            url = base_url + a['href']
            urls.append(url)

    return urls


# 출처 url로부터 영화 제목, 영화 이미지를 가져와서 db에 저장
def insert_movie(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url, headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    try:
        name = soup.select_one('#content > div.article > div.mv_info_area > div.mv_info > h3 > a').text
        img_url = soup.select_one('#content > div.article > div.mv_info_area > div.poster > a > img')['src']
        rate = soup.select_one('#content > div.article > div.section_group.section_group_frst > div > div > div.score_area > div.netizen_score > div > div > em').text
        time = soup.select_one('#content > div.article > div.mv_info_area > div.mv_info > dl > dd > p > span:nth-child(3)').text
        desc_list = soup.select('#content > div.article > div.mv_info_area > div.mv_info > dl > dd > p > span:nth-child(1) > a')

        desc = ''
        for genre in desc_list:
            desc += genre.text + ' '

        doc = {
            'name': name,
            'img': img_url,
            'url': url,
            'like': 0,
            'rate': rate,
            'time': time,
            'desc': desc,
        }

        db.movie.insert_one(doc)
        print('완료!', name)
    except:
        pass


# 기존 horror 콜렉션을 삭제하고, 출처 url들을 가져온 후, 크롤링하여 DB에 저장합니다.
def insert_all():
    db.movie.drop()  # horror 콜렉션을 모두 지워줍니다.
    urls = get_movies()
    for url in urls:
        insert_movie(url)


### 실행하기
insert_all()