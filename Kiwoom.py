import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

# TR(Transaction) -> 서버로부터 데이터를 주고받는 행위
# 키움증권 api 메소드를 사용하기 위해 dynamicCall를 사용해야한다.

class Kiwoom(QAxWidget):
    def __init__(self):
        # 부모 클래스의 __init__를 호출한다
        super().__init__()
        # QAxWidget 클래스에 ProgID 값을 던져 키움증권 클래스를 사용한다.
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        #로그인 시도
        self.OnEventConnect.connect(self.event_connect)
        #'OnReceiveTrData' 이벤트가 발생하면 receive_tr_data() 함수 호출
        self.OnReceiveTrData.connect(self.receive_tr_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        # PyQt를 사용하여 GUI 형태로 만들지 않았기 때문에 명시적으로 이벤트 루프를 만들어주어야 한다.
        # PyQt의 QEventLoop 클래스의 인스턴스를 생성 후 exec() 메소드 실행
        # 이벤트 루프로 인해 로그인할 때는 정상적으로 수행될 때까지 파이썬 코드는 실행되지 않고 대기
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def event_connect(self, err_code):
        if err_code == 0:
            # OnEventConnect 이벤트 처리로 로그인 성공 시 "connected" 출력
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()


    def get_code_list_by_market(self, market):
        #시장 구분에 따른 종목코드를 반환한다.  인자값이 시장구분.  반환값은 리스트로~
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        #반환된 종목코드들은 ;로 구분되기 때문에 ;로 나누어준다.
        code_list = code_list.split(';')
        return code_list[:-1]

    # 인자로 종목 코드 값을 받으면 해당하는 종목 명이 출력
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    #이것도 뭐에 쓰는지 확인
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

     # TR 입력 값을 설정할 때 사용 예로) opt10081TR을 이용한 일봉 차트 데이터 연속 조회
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    # CommRqData 함수 호출 및 QEventLoop 클래스의 인스턴스를 생성 후 이벤트 루프를 만들어준다.
    #  주식일봉조회(OPT10081) , [OPT50037 : 코스피200지수요청]
    # rqname은 TR을 구분하기 위한 용도, trcode는 실제 TR을 요청할 때 사용, next은 단순 or 연속 조회, screen_no은 화면값으로 주로 기본값인 "0101"을 사용
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        # 이벤트 루프 덕분에 TR요청시 키움증권 서버가 'OnReceiveTrData' 이벤트를 보낼 때까지 대기
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    # TR 요청에 대한 이벤트 발생 후 실제로 데이터를 가져오려면 CommGetData 메서드를 사용해야함
    def comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        # 문자열 양쪽에 공백이 있어 공백 제거
        return ret.strip()

    # 수신 받은 데이터의 반복 개수를 반환한다
    def get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    #여러 종류의 TR을 요청해도 모두 receive_tr_data 안에서 처리해야 한다. rqname 값을 통해서 TR을 구별한다.
    def receive_tr_data(self, screen_no, rqname, trcode, record_name, next , unused1, unused2, unused3, unused4):

        # 키움증권 서버는 OnReceiveTrData 이벤트가 발생할 때 PrevNext라는 인자 값을 통해서 연속조회가 필요한 경우 PrevNext 값을 2로 리턴
        # 2이면 TR을 또 요청해서 남아있는 데이터를 받아야한다.
        if next == '2':
            self.remained_data = True
            print(self.remained_data)
        else:
            self.remained_data = False
            print(self.remained_data)

        #TR 유형이 "opt10081_req" 일 때 _opt10081()을 호출한다.
        # 이제 여기에 원하는 TR 요청을 하면 된다.
        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        if rqname == 'opt50037_req':
            self._opt50037(rqname, trcode)
        try:
            # 이상 없이 수행했다면 이벤트 루프를 종료 시킨다.
            self.tr_event_loop.exit()
        except AttributeError:
            pass
    def _opt50037(self,rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)
        print(data_cnt)
        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "일자")
            close = self.comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")
            self.ohlcv['date'].append(date)
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))



    def _opt10081(self, rqname, trcode):
        #먼저 요청에 대한 반환 데이터의 개수를 가져온다.
        data_cnt = self.get_repeat_cnt(trcode, rqname)

        #일봉 데이터는 거래일 단위로 '종목코드', '현재가', '거래량', '거래대금', '일자', '시가', '고가', '저가', '수정주가구분',
        # '수정비율', '대업종구분', '소업종구분', '종목정보', '수정주가이벤트', '전일종가'를 한 번에 제공
        #이 중에서 날짜와 종가, 거래량만 가져온다.
        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "일자")
            close = self.comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")
            print(close)
            #  open = self.comm_get_data(trcode, "", rqname, i, "시가")
            #  high = self.comm_get_data(trcode, "", rqname, i, "고가")
            #  low = self.comm_get_data(trcode, "", rqname, i, "저가")

            self.ohlcv['date'].append(date)
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
            #  self.ohlcv['open'].append(int(open))
            #  self.ohlcv['high'].append(int(high))
            #  self.ohlcv['low'].append(int(low))


