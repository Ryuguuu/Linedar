from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

class CalendarLib:
    def __init__(self, service_account_file, scopes):
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_file, 
            scopes=scopes
        )
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
        self.calendar_id = 'ryugupri@gmail.com'

    def get_today_events(self):
        try:
            now = datetime.datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + datetime.timedelta(days=1)

            events_result = self.calendar_service.events().list(
                calendarId=self.calendar_id,
                timeMin=today_start.isoformat() + 'Z',
                timeMax=today_end.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])
        except Exception as e:
            print(f"予定取得エラー: {str(e)}")
            return []

    def get_tasks(self):
        try:
            events_result = self.calendar_service.events().list(
                calendarId=self.calendar_id,
                q='#task',  # タスクを識別するためのタグ
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"タスク取得エラー: {str(e)}")
            return []

    def add_task(self, title):
        try:
            d_today = str(datetime.date.today())
            event = {
                'summary': title,
                'start': {
                    'dateTime': f"{d_today}T23:58:00+09:00",
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': f"{d_today}T23:59:00+09:00",
                    'timeZone': 'Asia/Tokyo',
                },
            }
            self.calendar_service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return True
        except Exception as e:
            print(f"タスク追加エラー: {str(e)}")
            return False

    def delete_task(self, title):
        try:
            events_result = self.calendar_service.events().list(
                calendarId=self.calendar_id,
                q=f"{title} #task"
            ).execute()
            
            for event in events_result.get('items', []):
                self.calendar_service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event['id']
                ).execute()
                return True
            return False
        except Exception as e:
            print(f"タスク削除エラー: {str(e)}")
            return False