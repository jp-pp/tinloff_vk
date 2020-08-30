from datetime import date, time, datetime, timedelta
import psycopg2


def select_date_data(conn, cur, date_first, date_second):
    # Найти записи по датам

    def display_object(d):
        # Вывод объекто с данными в консоль

        cur.execute("select person, quality, response_duration, project_id, server_id from call_records where date=(%s)", (d,))

        rows = cur.fetchall()
        print({'quantity': len(rows)})
        for r in rows:
            dataObj = {}
            dataObj['person_or_AM'] = r[0]
            dataObj['quality'] = r[1]
            dataObj['response_duration'] = r[2]
            cur.execute("select name from project where id=(%s)", (r[3],))
            project = cur.fetchone()
            dataObj['project_id'] = project[0]
            cur.execute("select name from server where id=(%s)", (r[4],))
            server = cur.fetchone()
            dataObj['server_id'] = server[0]
            print(dataObj)


    if date_second is None or date_first == date_second:
        # Если указана только одна дата

        display_object(date_first)

    else:
        # Если указан промежуток дат
        df = date.fromisoformat(date_first)
        ds = date.fromisoformat(date_second)

        if df > ds:
            df, ds = ds, df

        date_array = []

        while df <= ds:
            date_array.append(df.isoformat())
            df+=timedelta(days=1)

        for d in date_array:
            display_object(d)

    cur.close()
    conn.close()