# coding: utf-8

import sys
import time
import datetime
import json
import requests

# argvs = sys.argv
# argc = len(argvs)

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
    start = datetime.datetime.strptime(r['start'], '%Y-%m-%dT%H:%M:%S')
    end = datetime.datetime.strptime(r['end'], '%Y-%m-%dT%H:%M:%S')
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

def create_notification(r, r_n):
    text = "サーモンランオープン！\n"
    text = text + create_info_text(r)
    embeds = create_embeds(r)
    text = text + "\n"
    text = text + "次回スケジュール\n"
    text = text +create_info_text(r_n)
    send_discord_notification(text, embeds)
    print(datetime.datetime.now())

def main():
    try:
        prev_collect_minute = 5
        result = collectData("coop/schedule")
        r0 = result[0]
        r1 = result[1]
        r2 = result[2]
        salmon_start_now = datetime.datetime.strptime(r0['start'], '%Y-%m-%dT%H:%M:%S')
        salmon_start_next = datetime.datetime.strptime(r1['start'], '%Y-%m-%dT%H:%M:%S')

        now = datetime.datetime.now()
        if now > salmon_start_now:
            create_notification(r0, r1)

        while True:
            now = datetime.datetime.now()
            if now >= salmon_start_next:
                create_notification(r1, r2)
                result = collectData("coop/schedule")
                r1 = result[1]
                r2 = result[2]
                salmon_start_next = datetime.datetime.strptime(r1['start'], '%Y-%m-%dT%H:%M:%S')
            else:
                if now.minute != prev_collect_minute and now.minute % 10 == 5:
                    result = collectData("coop/schedule")
                    r1 = result[1]
                    r2 = result[2]
                    salmon_start_next = datetime.datetime.strptime(r1['start'], '%Y-%m-%dT%H:%M:%S')
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