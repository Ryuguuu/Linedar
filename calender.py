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
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message == "空き時間を算出"):
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
            )
        elif(message == "スケジュール"):
            # 自動応答のメッセージを返す（受け取ったJSON形式のデータをそのまま表示する）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="タスクの名前を入力してください")
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
