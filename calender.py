from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot import LineBotSdkDeprecatedIn30
import json
import os
import subprocess
import warnings
from callib import CalendarLib
import datetime

warnings.filterwarnings("ignore", category=LineBotSdkDeprecatedIn30)

import groq_history
chat_history = [] # チャット履歴を追加
status = "default"
Clib = CalendarLib("./credentials.json", ["https://www.googleapis.com/auth/calendar"])

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("MSG_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel token/secret.")
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.reply_token == "00000000000000000000000000000000":
        print("no reply")
        return
    
    message = event.message.text
    if(status == "default"):
        if(message == "タスクを追加"):
            status = "add_task"
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message == "タスク完了"):
            status = "remove_task"
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message == "タスクリストを表示"):
            tasks = Clib.get_tasks()
            if tasks:
                task_list = "\n".join([task['summary'] for task in tasks])
                response_text = f"タスクリスト:\n{task_list}"
            else:
                response_text = "タスクリストは空です。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )
        elif(message == "空き時間を算出"):
            events = Clib.get_today_events()
            if events:
                free_times = []  # 空き時間を格納するリスト
                now = datetime.datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + datetime.timedelta(days=1)

                # 予定を開始時間でソート
                events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

                # 最初の空き時間を計算
                last_end_time = today_start

                for event in events:
                    start_time = event['start'].get('dateTime', event['start'].get('date'))
                    end_time = event['end'].get('dateTime', event['end'].get('date'))

                    # 空き時間がある場合
                    if last_end_time < start_time:
                        free_times.append(f"{last_end_time.strftime('%H:%M')} - {datetime.datetime.fromisoformat(start_time).strftime('%H:%M')}")

                    # 最後の予定の終了時間を更新
                    last_end_time = max(last_end_time, datetime.datetime.fromisoformat(end_time))

                # 最後の予定の後の空き時間を追加
                if last_end_time < today_end:
                    free_times.append(f"{last_end_time.strftime('%H:%M')} - {today_end.strftime('%H:%M')}")

                if free_times:
                    response_text = "空き時間:\n" + "\n".join(free_times)
                else:
                    response_text = "空き時間はありません。"
            else:
                response_text = "今日の予定はありません。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )
        elif(message == "スケジュール"):
            events = Clib.get_today_events()
            if events:
                schedule_list = "\n".join([f"{event['start'].get('dateTime', event['start'].get('date'))}: {event['summary']}" for event in events])
                response_text = f"今日のスケジュール:\n{schedule_list}"
            else:
                response_text = "今日のスケジュールはありません。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )
        else:
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="だまれ")
            )
    elif(status == "add_task"):
        Clib.add_task(message)
        # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="タスクを追加しました")
        )
        status = "default"
    elif(status == "remove_task"):
        Clib.delete_task(message)
        # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="タスクを追加しました")
        )
        status = "default"

if __name__ == "__main__":
  app.run(host="localhost", port=8000)
