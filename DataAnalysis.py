import sys
from PyQt5.QtWidgets import *
import Kiwoom
import matplotlib.pyplot as plt
import math
import pandas as pd
import Crawling
from sklearn import  linear_model #선형회귀
from sklearn.metrics import mean_squared_error#MSE:평균제곱오차
from sklearn.metrics import r2_score#결정계수

# 시장구분 –> 0:장내, 3:ELW, 4:뮤추얼펀드, 5:신주인수권,
# 6:리츠, 8:ETF, 9:하이일드펀드, 10:코스닥, 30:제3시장
MARKET_KOSPI   = 0


class DataAnalysis:
    def __init__(self):
        self.kiwoom = Kiwoom.Kiwoom()
        self.kiwoom.comm_connect()
    def fundamental_analysis(self, df):
        print("각 칼럼의 최댓값 :\n" , df.max())
        print("각 칼럼의 최솟값 :\n",  df.min())
        print("각 칼럼의 평균값 :\n", df.mean())
        print("각 칼럼의 표준편차 :\n",df.std() )


    # 함수 인자로 조회할 종목코드와 시작날짜를 넘겨준다.
    def get_opt10081(self, code, start):
        #dataframe 객체로 만드는 가장 쉬운 방법인 딕셔너리를 사용
        # 날짜와 종가, 거래량만 가져온다.
        self.kiwoom.ohlcv = {'date': [], 'close': [], 'volume': []}

        # opt10081(일봉) TR 요청
        #open API의 SetInputValue함수로 설정값 입력
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        # CommRqData 함수 -> 사용자 구분 명, trcode, 0:조회2:연속, 4자리 화면번호
        # opt10081을 통해 일봉 데이터를 요청
        self.kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

        # date 값을 index로 설정
        df = pd.DataFrame(self.kiwoom.ohlcv, columns=['close', 'volume'],
                       index=self.kiwoom.ohlcv['date'])
        return df

    #KOSPI 200 불러오기
    def get_opt50037(self, code, start):
        self.kiwoom.ohlcv = {'date': [], 'close': [], 'volume': []}
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("기준일자", start)
        self.kiwoom.comm_rq_data("opt50037_req", "opt50037", 0, "0101")
        df = pd.DataFrame(self.kiwoom.ohlcv, columns=['close', 'volume'],
                       index=self.kiwoom.ohlcv['date'])
        print(df)
        return df

    def merge_dataframe(self, df1, df2):
        temp={"df1_close" :df1['close'], "df1_volume" : df1['volume'],
                "df2_close" :df2['close'], "df2_volume" : df2['volume'] }
        result= pd.DataFrame(temp, columns=["df1_close","df1_volume","df2_close","df2_volume"], index=df1.index)
        return result

    def linearegression(self, x_var, y_var):
        #훈련 데이터와 테스트 데이터를 9:1 비율로 나눈다.
        x_var_train=x_var[:540]
        x_var_test = x_var[540:]
        y_var_train = y_var[:540]
        y_var_test = y_var[540:]

        #모델 생성
        model = linear_model.LinearRegression()
        model.fit(x_var_train,y_var_train)
        print("---------------------------------------")
        print("model.coef, model.intercept -> ",model.coef_, model.intercept_)
        print("---------------------------------------")

        # 모델 평가
        # 예측값 설정 - 회귀모델이 잘만들어졌는지 테스트
        y_train_pred = model.predict(x_var_train)
        y_test_pred = model.predict(x_var_test)

        plt.scatter(y_train_pred, y_train_pred - y_var_train, c='blue', marker='o', label='Training data')
        plt.scatter(y_test_pred, y_test_pred - y_var_test, c='lightgreen', marker='s', label='Test data')

        plt.hlines(y=0, xmin=40000, xmax=70000, lw=2, color='red')
        plt.xlabel('Predicted Values')
        plt.ylabel('Residuals')
        plt.show()

        # 적합도 검사
        # 평균제곱근오차(RMSE: Root Mean Squared Error)
        print('RMSE train:%.1f, test:%.1f' % (math.sqrt(mean_squared_error(y_var_train, y_train_pred)),
            math.sqrt(mean_squared_error(y_var_test, y_test_pred))))
        # 결정계수
        print('R^2 train:%.1f, test:%.1f' % ( r2_score(y_var_train, y_train_pred),
            r2_score(y_var_test, y_test_pred)))


        #만약 키움증권의 주가가 50,000원이고 거래량이 10,000이라면 GS의 주가는?
        gs_pred = 50000 * model.coef_[0] + 10000*model.coef_[1] +model.intercept_
        print("모델에 따른 GS의 주가는 ?  : " , gs_pred)

    def read_CSVfile(self, filename):
            fopen = open(filename)
            line = fopen.readline()
            code = []
            name = []
            market = []
            while line :
                line = fopen.readline()
                code_list= line.split('\t')
                if code_list[0] != '' :
                    if self.kiwoom.get_master_code_name(code_list[0]) !='' :
                        code.append(code_list[0])
                        name.append(code_list[1])
                        market.append(code_list[2][:5])
            #dataframe으로 만들기
            code_list = {'code' : code , 'name' : name, 'market': market}
            df_code_list = pd.DataFrame(code_list)
            df_code_list.info()
    def get_basic_finance(self,code):
        BasicFinanceOfCode = Crawling.get_basic_finance(code)
        print(BasicFinanceOfCode)


if __name__ == "__main__":
    # Kiwoom 클래스는 QAxWidget 클래스를 상속받았기 때문에 Kiwoom의 인스턴스를 생성하기 위해서는 먼저 QApplication 클래스의 인스턴스를 생성
    #QApplication 클래스에 대한 인스터스를 생성하고 app 변수를 통해 바인딩한다.
    app = QApplication(sys.argv)
    dataAnalysis = DataAnalysis()



    #유가증권 시장에 상장된 종목코드를 뽑아온다.
    #code_list = dataAnalysis.kiwoom.get_code_list_by_market(MARKET_KOSPI)
    #print(code_list)
    #키움증권 2017년 10월 13일까지 조회
    kiwoom_df= dataAnalysis.get_opt10081("078930","20171013")
    print(kiwoom_df)
    # GS 2017년 3월 21일 부터 조회
    #gs_df = dataAnalysis.get_opt10081("078930","20171013")

    # 자료형을 dataframe의 index에서 datetime으로 바꾸어준다.
    # dateIndex = pd.to_datetime(gs_df.index, format='%Y%m%d')

    #기본적 분석
    #dataAnalysis.fundamental_analysis(kiwoom_df)
    #dataAnalysis.read_CSVfile('C:/Users/user/Desktop/code_list.txt')

    #GS의 기초 재무 비율을 크롤링을 통해서 가져온다.
    dataAnalysis.get_basic_finance("078930")

    # 두 DataFrame 합치기
    # print(dataAnalysis.merge_dataframe(kiwoom_df,gs_df))

