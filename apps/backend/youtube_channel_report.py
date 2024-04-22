import os
import re
from datetime import timedelta
from datetime import datetime
from datetime import date
from dotenv import load_dotenv
from googleapiclient.discovery import build

minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')
hours_pattern = re.compile(r'(\d+)H')

date_pattern = r'\d{4}-\d{2}-\d{2}'

week = timedelta(weeks=1)
month = timedelta(days=30)
today = date.today()
# todo add a timer functionality to calculate how long it takes for a program to run
# todo: figure out if these global variables are still needed and if not delete them
# next_week = today + week
# next_month = today + month
last_month = today - month
last_week = today - week


class YoutubeChannelReport:
    def __init__(self, api_key, channel_id):
        self.api_key = api_key
        self.channel_id = channel_id
        self.channel_name = ""
        self.each_youtube_video_info = self.get_info_for_all_channel_videos()

    def get_videos_posted_this_week(self):
        self.each_youtube_video_info.sort(key=lambda video: video['date'], reverse=True)

        were_videos_uploaded_this_week = False

        weekly_report = [f"Here are the past week videos uploaded on {self.channel_name} between {last_week} and {today}"]

        for video in self.each_youtube_video_info:
            if video['date_only'] >= last_week:
                weekly_report.append(f"VIDEO TITLE: {video['title']}, uploaded on: "
                                     f"{video['date_only_with_month_names']}" f", VIDEO LINK: {video['url']}")

        if len(weekly_report) > 1:
            were_videos_uploaded_this_week = True
            weekly_report.insert(1, f"{len(weekly_report) - 1} videos were released:")

        if not were_videos_uploaded_this_week:
            weekly_report[0] = f"No youtube videos were uploaded on {self.channel_name} between {last_week} and {today}"

        for video_uploaded in weekly_report:
            print(video_uploaded)

    def get_videos_posted_this_month(self):
        self.each_youtube_video_info.sort(key=lambda video: video['date'], reverse=True)

        were_videos_uploaded_this_month = False

        monthly_report = [f"Here are the past monthly videos uploaded on {self.channel_name} between {last_month} and {today}"]

        for video in self.each_youtube_video_info:
            if video['date_only'] >= last_month:
                monthly_report.append(f"VIDEO TITLE: {video['title']}, uploaded on: "
                                      f"{video['date_only_with_month_names']}"f", VIDEO LINK: {video['url']}")
        if len(monthly_report) > 1:
            were_videos_uploaded_this_month = True
            monthly_report.insert(1, f"{len(monthly_report) - 1} videos were released:")

        if not were_videos_uploaded_this_month:
            monthly_report[0] = f"No youtube videos were uploaded on {self.channel_name} " \
                                f"between {last_month} and {today}"

        for video_uploaded in monthly_report:
            print(video_uploaded)

    def get_top_10_videos_by_views(self):
        self.each_youtube_video_info.sort(key=lambda video: video['views'], reverse=True)

        print(f"These are the top videos on the channel by total view count: {self.channel_name}")

        for rank, video in enumerate(self.each_youtube_video_info[:10], start=1):
            print(f"Number {rank} TOTAL VIEWS: {video['view_string']}, VIDEO TITLE: {video['title']}, "
                  f"uploaded on: {video['date_only_with_month_names']}"
                  f", video link: {video['url']}")

    def find_videos_with_disabled_comments_and_or_likes(self):
        videos_with_no_comments_and_or_likes = []
        videos_with_no_likes_total = 0
        videos_with_no_comments_total = 0

        for video in self.each_youtube_video_info:
            # todo try to figure out a better way to do this
            temp = f"VIDEO TITLE: {video['title']}"

            try:
                total_likes = int(video['total_likes'])
            except ValueError:
                temp += f", has likes that were {video['total_likes']} "
                videos_with_no_likes_total += 1

            try:
                total_comments = int(video['total_comments'])
            except ValueError:
                temp += f", has comments that were {video['total_comments']} "
                videos_with_no_comments_total += 1

            likes_index = temp.find(', has likes that were')
            comments_index = temp.find(', has comments that were')

            if likes_index != -1 or comments_index != -1:
                temp += f", VIDEO LINK: {video['url']}."
                videos_with_no_comments_and_or_likes.append(temp)

        if len(videos_with_no_comments_and_or_likes) == 0:
            print("There are no videos that have either the comments or likes disabled \n")
        else:
            videos_with_no_comments_and_or_likes.append(
                f"{videos_with_no_likes_total} total videos has the likes disabled"
            )
            videos_with_no_comments_and_or_likes.append(
                f"{videos_with_no_comments_total} total videos has the comments disabled"
            )
            for video in videos_with_no_comments_and_or_likes:
                print(video)

    def get_info_for_all_channel_videos(self):
        each_youtube_video_info = []

        youtube = build('youtube', 'v3', developerKey=self.api_key)
        channel_request = youtube.channels().list(part="contentDetails, snippet, statistics, topicDetails",
                                                  id=self.channel_id, maxResults=50)

        channel_response = channel_request.execute()

        video_uploads_playlist = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        # todo figure out why I had this index at [0] before going into items

        if self.channel_name == "":
            self.channel_name = channel_response['items'][0]['snippet']['title']

        next_youtube_page_token = None

        while True:
            looping_through_all_youtube_videos_on_channel = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=video_uploads_playlist,
                maxResults=50,
                pageToken=next_youtube_page_token
            )

            looping_through_all_youtube_videos_on_channel_response = \
                looping_through_all_youtube_videos_on_channel.execute()

            youtube_video_ids = [item['contentDetails']['videoId'] for item in
                                 looping_through_all_youtube_videos_on_channel_response['items']]

            youtube_video_info_request = youtube.videos().list(
                part='contentDetails, id, snippet, statistics',
                id=','.join(youtube_video_ids)
            )

            youtube_video_info_response = youtube_video_info_request.execute()

            for video_info in youtube_video_info_response['items']:
                video_id = video_info['id']
                youtube_video_link = f'https://youtu.be/{video_id}'
                video_length = video_info['contentDetails']['duration']

                total_hours = hours_pattern.search(video_length)
                total_minutes = minutes_pattern.search(video_length)
                total_seconds = seconds_pattern.search(video_length)

                total_hours = int(total_hours.group(1)) if total_hours else 0
                total_minutes = int(total_minutes.group(1)) if total_minutes else 0
                total_seconds = int(total_seconds.group(1)) if total_seconds else 0

                video_seconds = timedelta(
                    hours=total_hours,
                    minutes=total_minutes,
                    seconds=total_seconds
                )

                video_length_in_hours_min_sec = {
                    'hours': total_hours,
                    'min': total_minutes,
                    'secs': total_seconds,
                    'altogether': video_seconds
                }

                # these lines take the date published from the YouTube api and converts it to datetime object,
                # removing the time
                video_published_date_time = video_info['snippet']['publishedAt']
                video_published_date_only = re.findall(date_pattern, video_published_date_time)
                video_published_date_only = ", ".join(video_published_date_only)
                video_published_date_only = datetime.strptime(video_published_date_only, "%Y-%m-%d")

                video_title = video_info['snippet']['title']

                each_youtube_video_info.append(
                    {
                        'views': int(video_info['statistics']['viewCount']),
                        'view_string': '{:,}'.format(int(video_info['statistics']['viewCount'])),
                        'total_likes': video_info['statistics']['likeCount']
                        if 'likeCount' in video_info['statistics'] else "disabled",
                        'total_comments': video_info['statistics']['commentCount']
                        if 'commentCount' in video_info['statistics'] else "disabled",
                        'url': youtube_video_link,
                        'length': video_length_in_hours_min_sec,
                        'date': video_published_date_time,
                        'date_only': video_published_date_only.date(),
                        'date_only_with_month_names': video_published_date_only.strftime("%B %d, %Y"),
                        'title': video_title
                    }
                )
            next_youtube_page_token = looping_through_all_youtube_videos_on_channel_response.get('nextPageToken')

            if not next_youtube_page_token:
                break
        return each_youtube_video_info


def main():
    # Used a .env file to store sensitive information
    load_dotenv()

    new_youtube_channel_report = YoutubeChannelReport(
        api_key=os.getenv('API_KEY'),
        channel_id=os.getenv('CHANNEL_ID')

    )
    new_youtube_channel_report.find_videos_with_disabled_comments_and_or_likes()
    print("\n")
    new_youtube_channel_report.get_top_10_videos_by_views()
    print("\n")
    new_youtube_channel_report.get_videos_posted_this_month()
    print("\n")
    new_youtube_channel_report.get_videos_posted_this_week()


if __name__ == '__main__':
    main()
