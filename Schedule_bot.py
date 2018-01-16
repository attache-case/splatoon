# coding: utf-8

import sys
from pytz import timezone
import time
import datetime
import json
import requests

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
    url = 'https://discordapp.com/api/webhooks/401828481421279243/h7CEWxoRr34PZYUPHWOYW_gpdxhIHeqKBYtyz6GkmomwXKMeGKpduXj4YtO2XxTQBal9'
    headers = {
        "Content-Type" : "multipart/form-data"
    }
    post_json = {
    'content': text,
    'embeds': embeds
    }
    requests.post(url, headers = headers ,data = json.dumps(post_json))

def create_info_text(r):
    start = datetime.datetime.strptime(r['start'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))
    end = datetime.datetime.strptime(r['end'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))
    text = ""
    text = text + create_time_string(start) + "～" + create_time_string(end) + "\n"
    text = text + "ステージ：" + r['stage']['name'] + '\n'
    text = text + "武器："
    for i, weapon in enumerate(r['weapons']):
        if i < 3:
            text = text + weapon['name'] + "　"
        else:
            text = text + weapon['name'] + "\n"
    return text

def create_embeds(r):
    embeds = []
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

def create_start_notification(r, r_n):
    text = "サーモンランオープン！\n"
    text = text + create_info_text(r)
    embeds = create_embeds(r)
    text = text + "\n"
    text = text + "次回スケジュール\n"
    text = text +create_info_text(r_n)
    send_discord_notification(text, embeds)
    print("notify salmon start")
    print(datetime.datetime.now(timezone('Asia/Tokyo')))

def create_end_notification(r):
    text = "サーモンラン終了！次回予告！\n"
    text = text + create_info_text(r)
    send_discord_notification(text, [])
    print("notify salmon end")
    print(datetime.datetime.now(timezone('Asia/Tokyo')))

def main():

    argvs = sys.argv
    argc = len(argvs)
    notification_available = True
    current_salmon_ended = False

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
        salmon_start_now = datetime.datetime.strptime(r0['start'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))

        while True:
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            if now >= salmon_start_now:
                current_salmon_ended = False
                if notification_available is True:
                    create_start_notification(r0, r1)
                result = collectData("coop/schedule")
                r0 = result[1]
                r1 = result[2]
                salmon_start_now = datetime.datetime.strptime(r1['start'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))
            else:
                if now.minute != prev_collect_minute and now.minute % 10 == 5:
                    result = collectData("coop/schedule")
                    start = datetime.datetime.strptime(r0['start'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))
                    if salmon_start_now == start:
                        r0 = result[0]
                        r1 = result[1]
                        salmon_start_now = datetime.datetime.strptime(r0['start'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone('Asia/Tokyo'))
                        if current_salmon_ended is False:
                            if notification_available is True:
                                create_end_notification(r0)
                            else:
                                notification_available = True
                            current_salmon_ended = True
                    prev_collect_minute = now.minute
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        exit(0)
    except:
        print("=exception=")
        raise
        time.sleep(1)

if __name__ == '__main__':
    main()
