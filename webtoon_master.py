import os
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from konlpy.tag import Kkma
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# driver를 실행한다.
def drive():
    os.chdir('C:\\Users\\user\\Downloads\\chromedriver_win32') # 크롬드라이버.exe가 있는 폴더
    driver = webdriver.Chrome('./chromedriver') # driver 객체 불러옴
    driver.implicitly_wait(3) # 3초 후에 작동하도록
    return driver

# 지정한 네이버 웹툰의 댓글을 크롤링한다. (댓글 목록 return)
# id_num : 네이버 웹툰 번호 (웹툰별 고유 번호)
# cnt : 회차 개수 (최종 회차 번호)
def comment_crawler(id_num, cnt):
    comments = []
    proceed = -1 #진행 상태 표시 위함, 처음에 0보다 작아야 0%가 표시 됨
    
    driver = drive() #driver만 먼저 열어 놓음. for문 돌면서 url만 바꿔줄 것임
    print('진행중...')
    for i in range(1,cnt):
        percentage = int((i/cnt)*100)
        if percentage%10==0 and percentage>proceed: # 진행상황 표시
            proceed = percentage
            print(proceed, '% 완료')
        url = 'https://comic.naver.com/comment/comment.nhn?titleId={0}&no={1}#'.format(id_num, str(i))
        # best 댓글 15개만 읽고 있음 (전체 댓글을 읽을 수 있는 방법 고민)
        # url 예 : https://comic.naver.com/comment/comment?titleId=790713&no=43
        time.sleep(1.5)
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser') # BeautifulSoup 생성
        comments += list(map(lambda x: x.text, soup.select('.u_cbox_contents'))) # u_cbox_contents 영역에 있는 댓글을 comments에 더함

    driver.close()
    print('crawling finished')
    return comments

# 이모지를 제거하기 위한 패턴
# BMP (Basic Multilingual Plane, 기본 다국어 평면) characters 이외
# 참고 : https://studyprogram.tistory.com/1
only_BMP_pattern = re.compile("["u"\U00010000-\U0010FFFF""]+", flags=re.UNICODE) 

# 지정한 파일의 댓글을 형태소로 나누고 형태소별 개수가 담긴 딕셔너리를 만든다.
def count_word(inputfile):
    os.chdir('D:\python\webtoon_comments') # 작업 디렉토리
    fhand = open(inputfile, 'rt', encoding='UTF8') # 읽을 파일 열기
    question_file = open('D:\python\webtoon_comments\question.txt', 'a', encoding='utf-8') # 의미없는 형태소 저장할 파일 열기, apapend 모드
    counts={} # 형태소별 개수를 저장할 딕셔너리

    for line in fhand :
        line = only_BMP_pattern.sub(r'', line) # 이모지 제거
        if len(line) > 1 :
            try :
                result = Kkma().pos(line) # 꼬꼬마를 이용해 텍스트를 형태소 단위로 나눈다
                for word, tag in result :
                    # 의미없는 형태소는 원문을 포함해서 따로 저장
                    if (word == '아' and tag == 'VV') or (word == '어' and tag == 'VV') or (word == 'ㄱ' and tag == 'NNG') or (word == 'ㄷ' and tag == 'NNG') or (word == 'ㅇ' and tag == 'NNG') or (word == '베' and tag == 'NNG'):
                        question_file.write(tag + ' ' + word + '\n') # 의미없는 형태소와 태그 저장
                        question_file.write(line + '\n') # 원문 댓글 저장
                        question_file.write(str(result) + '\n\n') # 댓글 분석 결과를 string으로 변환하여 저장
                        continue

                    # tag 설명 : https://docs.google.com/spreadsheets/d/1OGAjUvalBuX-oZvZ_-9tEfYD2gQe7hTGsgUpiiBSXI8/edit#gid=0
                    if tag in ['NNG', 'NNP']: # 일반명사, 고유명사 (의존명사 'NNB'는 넣지 않음)
                        counts[tag + ' ' + word] = counts.get(tag + ' ' + word, 0) + 1
                    elif tag in ['VV', 'VA']: # 동사, 형용사 (읽기 좋게 뒤에 '다'를 붙여서 저장)
                        counts[tag + ' ' + word + '다'] = counts.get(tag + ' ' + word + '다', 0) + 1
            except:
                print("ERROR " + line) # 이모지가 있는 경우 오류 발생

    question_file.close()

    return counts

# 딕셔너리를 형태소 개수로 정렬해서 파일에 저장한다.
# dict : (형태소, 개수)가 담긴 딕셔너리
# outputfile : 결과를 저장할 파일명
def sort_and_write_dict(dict, outputfile):
    os.chdir('D:\python\webtoon_comments') # 작업 디렉토리
    file = open(outputfile, 'w', encoding='utf-8') # 결과를 저장할 파일 오픈
    list=[]
    for k,v in dict.items():
        list.append((v,k)) # (형태소, 개수)를 (개수, 형태소)로 바꿔 목록에 추가
    list = sorted(list, reverse=True) # 개수가 큰 순으로 정렬
    for v,k in list[:10]: # 확인을 위해 개수가 큰 순서로 10개를 화면에 출력
        print(k,v)
    for v,k in list:
        file.write(k + ' ' + str(v) + '\n') # '형태소 개수' 형태로 파일에 저장
    file.close()

# 형태소별 개수가 담긴 파일을 입력받아 워드클라우드를 만든다.
def create_wordcloud(inputfile, outputfile):
    os.chdir('D:\python\webtoon_comments')
    fhand = open(inputfile, 'rt', encoding='UTF8')
    tags = {} # 워드클라우드 생성을 위한 딕셔너리
    for line in fhand :
        values = line.split() # 각 라인은 '형태소태그 형태소 형태소개수'
        tags[values[1]] = int(values[2]) # 딕셔너리의 키는 형태소, 딕셔너리의 값은 형태소의 개수

    # 워드클라우드 만들기
    wordcloud = WordCloud(font_path='D:\python\JALNAN.TTF', background_color='white', max_words=50, width=1600, height=500)
    cloud = wordcloud.generate_from_frequencies(dict(tags))

    plt.figure()
    plt.imshow(cloud)
    plt.axis('off')
    plt.savefig(outputfile, bbox_inches='tight') # 파일로 저장

webtoons = [
    (525053, 47, '연재_베도_윈드브레이커'),
    (739130, 62, '연재_베도_대학원탈출일지'),
    (726786, 82, '연재_베도_여우자매'),
    (788273,17,'베도_그들이사는세상'),
    (734597,197, '베도_자작보드게임동아리'),
    (770601,36,'베도_악마법소녀'),
    (761392,17,'베도_계약인싸'),
    (786401,52,'베도_그냥선생님'),
    (784133, 40, '베도_카르엘'),
    (751809,28,'베도_39`C'),
    (694914,34,'베도_비너스'),
    (511287,36,'베도_연애혁명'),
    (700559,12,'베도_어글리후드'),
    (792936,21,'베도_내담당일진')
]

for webtoon in webtoons:
    id_num = webtoon[0]
    cnt = webtoon[1]
    toon_name = webtoon[2]

    comments = comment_crawler(id_num, cnt)

    #수집된 댓글 수
    #print(len(comments))

    #추출한 댓글 저장 위해 현재 working directory 변경, 저장할 폴더 위치로 지정하면 된다.
    os.chdir('D:\python\webtoon_comments')
    file = open(toon_name + '_comments.txt', 'w', encoding='utf-8')
    for cmt in comments:
        file.write(cmt+'\n')
    file.close()

    input = toon_name + '_comments.txt'
    output = toon_name + '_result.txt'
    wordcloudoutput = toon_name + '_wordcloud.png'
    counts = count_word(input)
    sort_and_write_dict(counts, output)
    create_wordcloud(output, wordcloudoutput)
