# coding: utf-8

import sys
import pytz
from pytz import timezone
import pytz
import time
import datetime
import json
import requests

tz_utc = pytz.utc
tz_jst = timezone('Asia/Tokyo')
DISCORD_WEBHOOK_URL = YOUR_DISCORD_WEBHOOK_URL

def weekday_jpn(i):
    if i == 0:
        return "月"
    elif i == 1:
        return "火"
    elif i == 2:
        return "水"
    elif i == 3:
        return "木"
    elif i == 4:
        return "金"
    elif i == 5:
        return "土"
    elif i == 6:
        return "日"

def create_time_string(dt):
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    weekday = dt.weekday()
    return "%04d年%02d月%02d日(%s)%02d時" % ( year, month, day, weekday_jpn(weekday), hour)

def collectData(str_target):
    endpoint = "https://spla2.yuu26.com/"
    headers = {'User-Agent': 'bot/1.0 (twitter @nyanatk2525)'}
    r = requests.get(endpoint + str_target, headers=headers)
    if r.status_code == 200:
        result_obj = r.json()
    return result_obj["result"]

def send_discord_notification(text, embeds):
    url = DISCORD_WEBHOOK_URL
    headers = {
        "Content-Type" : "multipart/form-data"
    }
    post_json = {
    'content': text,
    'embeds': embeds
    }
    requests.post(url, headers = headers ,data = json.dumps(post_json))

def create_info_text(r):
    text = ""
    try:
        start = datetime.datetime.strptime(r['start_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
        end = datetime.datetime.strptime(r['end_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
        text = text + create_time_string(start) + "～" + create_time_string(end) + "\n"
        text = text + "ステージ：" + r['stage']['name'] + '\n'
        text = text + "武器："
        for i, weapon in enumerate(r['weapons']):
            if i < 3:
                text = text + weapon['name'] + "　"
            else:
                text = text + weapon['name'] + "\n"
        return text
    except:
        text = text + "\n" + ":salmon:不明情報アリ:salmon:"
        return text

def create_embeds(r):
    embeds = []
    try:
        obj = dict(
            type = "rich",
            image = dict(
                url = r['stage']['image'],
                height = 90,
                width = 160
            )
        )
        embeds.append(obj)
        for i, weapon in enumerate(r['weapons']):
            obj = dict(
                type = "rich",
                image = dict(
                    url = weapon['image'],
                    height = 32,
                    width = 32
                )
            )
            embeds.append(obj)
        return embeds
    except:
        return []

def create_start_notification(r, r_n):
    text = "サーモンランオープン！\n"
    text = text + create_info_text(r)
    embeds = create_embeds(r)
    text = text + "\n"
    text = text + "次回スケジュール\n"
    text = text + create_info_text(r_n)
    send_discord_notification(text, embeds)
    print("notify salmon start")
    print(datetime.datetime.now(tz=tz_utc).astimezone(tz=tz_jst))

def create_end_notification(r):
    text = "サーモンラン終了！次回予告！\n"
    text = text + create_info_text(r)
    send_discord_notification(text, [])
    print("notify salmon end")
    print(datetime.datetime.now(tz=tz_utc).astimezone(tz=tz_jst))

def main():

    argvs = sys.argv
    argc = len(argvs)
    notification_available = True
    salmon_ongoing = False

    if argc == 2:
        enable = int(argvs[1])
        if enable == 0:
            notification_available = False
        elif enable == 1:
            notification_available = True

    try:
        prev_collect_minute = 5
        result = collectData("coop/schedule")
        r0 = result[0]
        r1 = result[1]
        salmon_trigger_start = datetime.datetime.strptime(r0['start_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
        salmon_trigger_end = datetime.datetime.strptime(r0['end_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
        print("SET salmon_trigger_start:")
        print(salmon_trigger_start)
        print("SET salmon_trigger_end:")
        print(salmon_trigger_end)

        # This code assert that the API doesn't mistake time
        while True:
            now = datetime.datetime.now(tz=tz_utc).astimezone(tz=tz_jst)
            if salmon_ongoing is False:
                if now >= salmon_trigger_start:
                    salmon_ongoing = True
                    salmon_trigger_end = datetime.datetime.strptime(r0['end_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
                    if notification_available is True:
                        create_start_notification(r0, r1)
                else: # update r0, r1 every 10 minutes while salmon is not ongoing
                    if now.minute != prev_collect_minute and now.minute % 10 == 5:
                        result = collectData("coop/schedule")
                        r0 = result[0]
                        r1 = result[1]
                        r0_start = datetime.datetime.strptime(r0['start_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
                        if r0_start != salmon_trigger_start:
                            salmon_trigger_start = r0_start
                            print("SET salmon_trigger_start:")
                            print(salmon_trigger_start)
                        prev_collect_minute = now.minute
            else: # salmon_ongoing is True
                if now >= salmon_trigger_end:
                    salmon_ongoing = False
                    if notification_available is True:
                        create_end_notification(r1)
                    salmon_trigger_start = datetime.datetime.strptime(r1['start_utc'], '%Y-%m-%dT%H:%M:%S+00:00').replace(tzinfo=tz_utc).astimezone(tz=tz_jst)
                    print("SET salmon_trigger_start:")
                    print(salmon_trigger_start)
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        exit(0)
    except:
        print("=exception=")
        print(now)
        raise
        time.sleep(1)

if __name__ == '__main__':
    main()
