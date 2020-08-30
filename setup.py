from tinkoff_voicekit_client import ClientTTS, ClientSTT
from datetime import date, time, datetime, timedelta
import re
import os
import psycopg2
from selectdata import select_date_data

API_KEY = ""
SECRET_KEY = ""

client = ClientSTT(API_KEY, SECRET_KEY)

audio_config = {
    "encoding": "LINEAR16",
    "sample_rate_hertz": 8000,
    "num_channels": 1
}

auto_answering = [
    'автоответчик',
    'вас приветствует',
    'вас приветствует автоответчик',
    'оставьте сообщение'
    'нажмите цифру',
    'после сигнала',
    'вы позвонили в компанию',
    'вас приветствует компания'
]

positive = [
    'здравствуйте говорите',
    'говорите'
    'слушаю',
    'ало говорите',
    'ало слушаю',
    'алло говорите',
    'алло слушаю',
    'я вас слушаю',
    'да слушаю',
    'да могу говорить',
    'да могу уделить время',
    'да могу',
    'мне интересно',
    'да интересно',
    'да заинтересован',
    'являюсь',
    'да являюсь',
    'да удобно'
]

negative = [
    'нет не могу',
    'нет мне не интересно',
    'не интересно',
    'не заинтересован',
    'я занят',
    'не могу говоорить',
    'нет',
    'досвидания',
    'на роботе'
]

check_answer = {'auto_answering':auto_answering,'positive':positive,'negative':negative}

DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "xxx"
DB_HOST = "localhost"
DB_PORT = "5432"

class RecognitionRecord:

    def __init__(self):
        self.file = None
        self.path = None
        self.number = None
        self.flag = None
        self.project_id = None
        self.server_id = None

    def __check_subs(self, transcript, check_arr):
        # Проверка подстроки на позитивный, негативный ответы и автоответчик
        count = 0
        for subs in check_arr:
            if subs in transcript:
                count += 1
        if count == 0:
            return False
        else:
            return True

    def __time_del(self, str_time):
        # Приведение времени разговора в объект time
        str_time = re.sub(r'[^0-9.]+', r'', str_time)
        time_format = '00:00:00'
        count=0
        for st in str_time:
            if st != '.':
                count += 1
            else:
                break
        time_format = time_format[count:]
        time_format = time_format[::-1]
        time_format+=str_time
        return time.fromisoformat(time_format)

    def __writing_in_file(self, person, positive_respons, start_time, end_time, transcript):
        # Запись в файл или БД
        global quantity
        path = os.path.dirname(__file__) + '\output\dir\log.txt'
        with open(os.path.abspath(path), 'r' if os.path.exists(os.path.abspath(path)) else 'w', encoding='utf-8') as f:

            dt = datetime(1970, 1, 1) + (datetime.combine(date(1970, 1, 1), self.__time_del(end_time)) - datetime.combine(date(1970, 1, 1), self.__time_del(start_time)))
            timestr = dt.time().isoformat(timespec='microseconds')
            make_a_record = True
            if os.path.getsize(os.path.abspath(path)) != 0:
                # Сравнение записей
                i = 0
                while i != quantity:
                    line = f.readline()
                    line_arr = line.split('|',maxsplit=-1)
                    if len(line_arr) == 9:
                        if line_arr[5] == self.number and line_arr[6] == timestr and line_arr[7] == transcript:
                            make_a_record = False
                            break
                    i+=1

            if make_a_record:

                f.write(str(quantity) + '|' + date.today().isoformat() + '|' + datetime.now().time().isoformat(timespec='microseconds') + '|' + str(int(person)) + '|' + str(int(positive_respons)) + '|' + self.number + '|' + timestr + '|' + transcript + '|\n')

                print('Запись прошла успешно')

            elif not make_a_record:
                print('Запись не прошла успешно. Найдена идентичкая запись.')
            f.close()

    def __writing_errors(self, error):
        path = os.path.dirname(__file__) + '\output\dir\error_log.txt'
        with open(os.path.abspath(path), 'a' if os.path.exists(os.path.abspath(path)) else 'w', encoding='utf-8') as f:
            f.write(date.today().isoformat() + '|' + datetime.now().time().isoformat( timespec='microseconds')  + '|' + str(error) + '|\n')
            f.close()

    def __writing_in_db(self, person, positive_respons, start_time, end_time, transcript):
        # Запись в bd
        dt = datetime(1970, 1, 1) + (datetime.combine(date(1970, 1, 1), self.__time_del(end_time)) - datetime.combine(date(1970, 1, 1), self.__time_del(start_time)))
        timestr = dt.time().isoformat(timespec='microseconds')
        make_a_record = True

        conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()

        cur.execute("select number, response_duration, response_text from call_records")

        rows = cur.fetchall()

        for r in rows:
            # Проверка наличия записей в db
            if r[0] == self.number and r[1] == timestr and r[2] == transcript:
                make_a_record = False
                break

        if make_a_record:
            cur.execute("select id from call_records")
            rows = cur.fetchall()
            if len(rows) != 0:
                id = int(rows[-1][0])
                id+=1
                first_rec = False
            else:
                first_rec = True

            if first_rec:
                cur.execute("insert into call_records (id, date, time, person, quality, number, response_duration, response_text, project_id, server_id) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (1, date.today().isoformat(), datetime.now().time().isoformat(timespec='microseconds'), int(person), int(positive_respons), self.number, timestr, transcript, self.project_id, self.server_id))
            else:
                cur.execute("insert into call_records (id, date, time, person, quality, number, response_duration, response_text, project_id, server_id) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (id, date.today().isoformat(), datetime.now().time().isoformat(timespec='microseconds'), int(person), int(positive_respons), self.number, timestr, transcript, self.project_id, self.server_id))

            print('Запись прошла успешно')
        elif not make_a_record:
            print('Запись не прошла успешно. Найдена идентичкая запись.')

        conn.commit()
        cur.close()
        conn.close()

    def __del_respons(self):
        os.remove(self.path)
        print('Файл записи успешно удален')

    def __check_data(self):
        # Проверка данных
        try:
            response = client.recognize(self.path, audio_config)
            for r in response:
                # Проверка на ответ человека или автоответчика
                answering_machine = False
                for tr in r['alternatives']:
                    transcript = tr['transcript']
                    if transcript != '':
                    # Если в записи есть разговор

                        if self.__check_subs(transcript, check_answer['auto_answering']):
                            answering_machine = True
                        positive_respons = False
                        if not answering_machine:
                            # Человек
                            person = True
                            if self.__check_subs(transcript, check_answer['negative']):
                                # Негативный ответ
                                positive_respons = False
                            elif self.__check_subs(transcript, check_answer['positive']):
                                # Позиитивный ответ
                                positive_respons = True
                        else:
                            person = False
                            # Автоответчик
                        if self.flag == '0':
                            self.__writing_in_file(person, positive_respons, r['start_time'], r['end_time'], transcript)
                        elif self.flag == '1':
                            self.__writing_in_db(person, positive_respons, r['start_time'], r['end_time'], transcript)
                        self.__del_respons()
                    if transcript == '':
                        print('Пустая запись')
        except Exception as e:
            self.__writing_errors(e)
            print('Аудио файл не найден или возникла ошибка')

    def __number_of_records(self):
        # Подсчет количества записей в log-файле
        global quantity
        quantity = 0
        path = os.path.dirname(__file__) + '\output\dir\log.txt'
        with open(os.path.abspath(path), 'r' if os.path.exists(os.path.abspath(path)) else 'w') as f:
            if os.path.getsize(os.path.abspath(path)) != 0:
                for line in f:
                    quantity += 1
        f.close()

    def recognition_file(self, data):
        # Заполняем данные и создаем объект
        for obj in data:
            self.__number_of_records()
            self.file = obj['filename']
            path = obj['path_to_file']
            self.path = os.path.dirname(__file__) + '/' + path + '/' + self.file
            self.number = obj['number']
            self.flag = obj['flag']
            self.project_id = obj['project_id']
            self.server_id = obj['server_id']
            self.__check_data()

if __name__ == '__main__':
    #dataArray = [
     #   {'filename': '1.wav', 'path_to_file': 'audio', 'number': '+79088762304', 'flag': '1', 'project_id': 1, 'server_id': 1},
      #  {'filename': '2.wav', 'path_to_file': 'audio', 'number': '+79034654644', 'flag': '1', 'project_id': 2, 'server_id': 1},
       # {'filename': '3.wav', 'path_to_file': 'audio', 'number': '+79056745304', 'flag': '1', 'project_id': 2, 'server_id': 1},
        #{'filename': '4.wav', 'path_to_file': 'audio', 'number': '+79086872304', 'flag': '1', 'project_id': 1, 'server_id': 1}
    #]
    #rec = RecognitionRecord()
    #rec.recognition_file(dataArray)

    conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()

    # Поиск по одной дате
    select_date_data(conn, cur, date.today().isoformat(), None)
    # Поиск по проомежутку дат
    select_date_data(conn, cur, date.today().isoformat(), (date.today()+timedelta(days=1)).isoformat())
