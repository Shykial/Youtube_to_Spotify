from googleapiclient.discovery import build
import json
import requests
import google_auth_oauthlib.flow
import pickle
import time
import csv
import concurrent.futures


class YoutubeAPI:

    def __init__(self):
        self.yt = self.create_yt_service_instance()

    def create_yt_service_instance(self):
        api_service_name = 'youtube'
        api_version = 'v3'
        credentials = self.get_yt_credentials()
        return build(api_service_name, api_version, credentials=credentials)

    def get_yt_credentials(self):
        client_secrets_file = 'yt_secrets.json'
        scopes = ['https://www.googleapis.com/auth/youtube.readonly']
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        try:
            with open('creds', 'rb+') as f:
                try:
                    return pickle.load(f)
                except EOFError:
                    print('Tworzenie nowego tokenu')
                    credentials = flow.run_console()
                    pickle.dump(credentials, f)
                    return credentials
        except FileNotFoundError:
            with open('creds', 'wb') as f:
                credentials = flow.run_console()
                pickle.dump(credentials, f)
                return credentials

    def list_playlists(self):
        request = self.yt.playlists().list(
            part='snippet',
            mine=True
        )

        print(request)
        response = request.execute()
        print(json.dumps(response, indent=4))

    def testing(self):
        token = '4/3wGgOEQdhABSNQ-lAaLzg3Ty2az44u597OgeaLXmNPk-NYGtBPeEo00'
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        r = requests.get('https://www.youtube.com/feed/my_videos', headers=headers)
        print(r.json())

    def get_IDs_from_playlist(self, playlist_id) -> list:
        IDs = []
        print('Pobieranie ID filmów z playlisty', end='')

        # getting first page of the returned content
        request = self.yt.playlistItems().list(
            part='snippet',
            maxResults='50',  # number of items can be from range (1, 50) inclusive
            playlistId=playlist_id
        )

        response = request.execute()
        for item in response['items']:
            # print(json.dumps(item, indent=4))
            IDs.append(item['snippet']['resourceId']['videoId'])

        # while loop to get all the next pages by referring to the previous one,
        # breaking from the loop when the response is None - meaning there is no subsequent page
        while True:
            print('.', end=' ')
            request = self.yt.videos().list_next(request, response)

            if request:
                response = request.execute()
            else:
                break

            for item in response['items']:
                IDs.append(item['snippet']['resourceId']['videoId'])
                # print(json.dumps(item, indent=4))

        print()
        # print(IDs)
        return IDs

    def get_videos_topics(self, IDs) -> dict:
        # print(IDs)
        print('Pobieranie informacji o wybranych filmach', end='')
        responses = []
        items = {}
        step = 50
        item_packs = [IDs[i:i + step] for i in range(0, len(IDs), step)]
        start = time.time()
        for pack in item_packs:
            # print(', '.join(pack))
            print('.', end=' ')
            request = self.yt.videos().list(
                part='snippet, topicDetails',
                id=','.join(pack)
            )
            response = request.execute()
            for item in response['items']:
                items[item['snippet']['title']] = item['topicDetails'][
                    'topicCategories'] if 'topicDetails' in item else None

        return items

    def get_titles_from_playlist(self, playlist_id) -> list:
        titles = []
        print('Pobieranie tytułów z playlisty', end='')

        # getting first page of the returned content
        playlist_items_request = self.yt.playlistItems().list(
            part='snippet',
            maxResults='50',  # number of items can be from range (1, 50) inclusive
            playlistId=playlist_id
        )

        response = playlist_items_request.execute()
        for item in response['items']:
            # print(json.dumps(item, indent=4))
            titles.append(item['snippet']['title'])

        # while loop to get all the next pages by referring to the previous one,
        # breaking from the loop when the response is None - meaning there is no subsequent page
        while True:
            print('.', end=' ')
            playlist_items_request = self.yt.videos().list_next(playlist_items_request, response)

            if playlist_items_request:
                response = playlist_items_request.execute()
            else:
                break

            for item in response['items']:
                titles.append(item['snippet']['title'])
                print(item)

        return [t for t in titles if t not in ('Private video', 'Deleted video')]

    def get_topic_videos_from_playlist(self, playlist_id, topic) -> list:
        IDs = self.get_IDs_from_playlist(playlist_id)
        videos_with_topics = self.get_videos_topics(IDs)
        return filter_videos_by_topic(videos_with_topics, topic)


def write_titles_to_file(yt_vids, file_path='yt_vids_list.txt'):
    with open(file_path, 'w+', encoding='UTF-8') as f:
        for vid in yt_vids:
            f.write(vid + '\n')


def write_topics_to_file(video_topics: dict):
    with open('topics_data.tsv', 'w', encoding='utf-8', newline='') as f:
        tsv_writer = csv.writer(f, delimiter='\t')
        tsv_writer.writerow(['Title', 'Topic'])
        for key, val in video_topics.items():
            if not val:
                topics = ['None']
            else:
                topics = val if val and type(val) is not str else [val]
            tsv_writer.writerow([key, *topics])

    with open('topics_data.csv', 'w', encoding='utf-8') as f:
        f.write('Title\tTopic\n')
        for key, val in video_topics.items():
            topics_string = '\t'.join(val) if val and type(val) is not str else val
            f.write(f'{key}\t{topics_string}\n')


def get_IDs_from_file(file_path) -> list:
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


def write_IDs_to_file(video_IDs, file_path='video_IDs.txt'):
    print(f'Zapisywanie wartości ID do pliku {file_path}')
    with open(file_path, 'w') as f:
        for ID in video_IDs:
            f.write(ID + '\n')


def filter_videos_by_topic(videos_with_topics, queried_topic) -> list:
    filtered_titles = []
    for title, topics in videos_with_topics.items():
        if type(topics) is str:
            topics = [topics]
        if not topics or any(queried_topic.lower() in topic.lower() for topic in topics):
            filtered_titles.append(title)
    return filtered_titles


def main():
    youtube = YoutubeAPI()

    # choice = input('wczytac z pliku? ')
    # choice = True if choice[0] in ('t', 'y') else False
    # yt_vids = youtube.get_titles_from_playlist('LLdbdHlxCs0jEI6oPKl5um3g')  # my liked items playlist
    # write_titles_to_file(choice, yt_vids)
    # youtube.list_playlists()
    # youtube.testing()
    video_IDs = get_IDs_from_file('video_IDs.txt')
    # video_IDs = youtube.get_IDs_from_playlist('PLFgquLnL59alcyTM2lkWJU34KtfPXQDaX')
    # write_IDs_to_file(video_IDs)
    # # print(len(video_IDs))
    start = time.time()
    video_topics = youtube.get_videos_topics(video_IDs)
    print(time.time() - start)
    write_topics_to_file(video_topics)
    filtered_videos = filter_videos_by_topic(video_topics, 'music')
    write_titles_to_file(filtered_videos, file_path='filtered_videos.txt')
    # z = youtube.get_topic_videos_from_playlist('LLdbdHlxCs0jEI6oPKl5um3g', 'Music')
    # for item in z:
    #     print(item)
    # print(len(z))
    pass


if __name__ == '__main__':
    main()
