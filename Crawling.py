import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
'''
매출액: salseAccount ,영업이익: operationProfit, 순이익: netIncome, 영업이익률: rateOfOperatioinProfit
순이익률: netProfitMargin, ROE:ROE, 부채비율: debtRatio, 당좌비율: quickRatio , 유보율: reserveRatio
EPS: EPS, BPS: BPS , 주당배당금: bookValuePerShare, 시가배당률: DividendRatio,  배당성향: propensityToDividend
'''

#지금 이거 너무 느려서 한번 가져온 데이터는 DB에 저장해야함
#그리고 반드시 크롤링했던 종목인지 사전에 체크하고 안한 것만 이 메소드 사용해야함.
def get_basic_finance(code):
    html = urlopen("http://finance.naver.com/item/main.nhn?code=" + code)
    bsObj = BeautifulSoup(html, "html.parser")

    column_list= ["salseAccount","operationProfit","netIncome","rateOfOperatioinProfit","netProfitMargin",
            "ROE","debtRatio","quickRatio","reserveRatio","EPS","BPS","bookValuePerShare","DividendRatio","propensityToDividend"]
    index = ['14.12', '15.12', '16.12','17.12E','16.06','16.09','16.12' ,'17.03','17.06','17.09E']

    BasicFinance=pd.DataFrame(index = index)

    BasicfinanceTableList = bsObj.find("table", {"class": "tb_type1 tb_num tb_type1_ifrs"}).find("tbody")
    i = 0
    for tr_tag in  BasicfinanceTableList.findAll("tr"):
        list=make_td_list(tr_tag)
        BasicFinance[column_list[i]]=list
        i = i+1

    return BasicFinance

def make_td_list(tr_tag):
    temp_list=[]
    for i in range(0, 10):
        value= tr_tag.findAll("td")[i].get_text().strip()
        if value == "":
            value ="없음"
        temp_list.append(value)
    return temp_list


