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
chat_history = [] # チャット履歴を追加
status = "default"  # グローバル変数としてstatusを定義
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
    global status  # グローバル変数として宣言
    
    if isinstance(event, dict):
        reply_token = event.get('replyToken')
        message_text = event.get('message', {}).get('text')
    else:
        reply_token = event.reply_token
        message_text = event.message.text

    if reply_token == "00000000000000000000000000000000":
        print("no reply")
        return
    
    if(status == "default"):
        if(message_text == "タスクを追加"):
            status = "add_task"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message_text == "タスク完了"):
            status = "remove_task"
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message_text == "タスクリストを表示"):
            tasks = Clib.get_tasks()
            if tasks:
                task_list = "\n".join([task['summary'] for task in tasks])
                response_text = f"タスクリスト:\n{task_list}"
            else:
                response_text = "タスクリストは空です。"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=response_text)
            )
        elif(message_text == "空き時間を算出"):
            events = Clib.get_today_events()
            if events:
                free_times = []  # 空き時間を格納するリスト
                total_free_minutes = 0  # 合計空き時間（分）
                now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))  # JSTタイムゾーン
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + datetime.timedelta(days=1)

                # 予定を開始時間でソート
                events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

                # 最初の空き時間を計算
                last_end_time = today_start

                for event in events:
                    start_time = datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00'))
                    
                    # タイムゾーンを日本時間に変換
                    start_time = start_time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                    end_time = end_time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))

                    # 空き時間がある場合
                    if last_end_time < start_time:
                        free_times.append(f"{last_end_time.strftime('%H:%M')} - {start_time.strftime('%H:%M')}")
                        # 空き時間の分数を計算
                        free_minutes = (start_time - last_end_time).total_seconds() / 60
                        total_free_minutes += free_minutes

                    # 最後の予定の終了時間を更新
                    last_end_time = max(last_end_time, end_time)

                # 最後の予定の後の空き時間を追加
                if last_end_time < today_end:
                    free_times.append(f"{last_end_time.strftime('%H:%M')} - {today_end.strftime('%H:%M')}")
                    free_minutes = (today_end - last_end_time).total_seconds() / 60
                    total_free_minutes += free_minutes

                if free_times:
                    hours = int(total_free_minutes // 60)
                    minutes = int(total_free_minutes % 60)
                    response_text = "空き時間:\n" + "\n".join(free_times) + f"\n\n合計空き時間: {hours}時間{minutes}分"
                else:
                    response_text = "空き時間はありません。"
            else:
                response_text = "今日の予定はありません。"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=response_text)
            )
        elif(message_text == "スケジュール"):
            events = Clib.get_today_events()
            if events:
                schedule_items = []
                for event in events:
                    start_time = datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00'))
                    
                    # タイムゾーンを日本時間に変換
                    start_time = start_time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                    end_time = end_time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                    
                    schedule_items.append(f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}: {event['summary']}")
                
                schedule_list = "\n".join(schedule_items)
                response_text = f"今日のスケジュール:\n{schedule_list}"
            else:
                response_text = "今日のスケジュールはありません。"
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=response_text)
            )
        else:
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="だまれ")
            )
    elif(status == "add_task"):
        Clib.add_task(message_text)
        # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="タスクを追加しました")
        )
        status = "default"
    elif(status == "remove_task"):
        Clib.delete_task(message_text)
        # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="タスクを完了しました")
        )
        status = "default"

if __name__ == "__main__":
  app.run(host="localhost", port=8000)
