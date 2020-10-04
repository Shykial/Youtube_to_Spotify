from googleapiclient.discovery import build
import json
import google_auth_oauthlib.flow
import pickle
import csv
from decorators import timer


def get_yt_credentials():
    client_secrets_file_web = 'yt_secrets.json'
    client_secrets_file_native = 'yt_secrets_old.json'
    scopes = ['https://www.googleapis.com/auth/youtube.readonly']
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file_web, scopes)
    try:
        with open('creds.p', 'rb') as f:
            return pickle.load(f)

    except (FileNotFoundError, EOFError):
        with open('creds.p', 'wb') as f:
            print('Tworzenie nowego tokenu')
            try:
                credentials = flow.run_local_server(authorization_prompt_message='', port=8080, prompt='consent',
                                                    success_message='Gugiel zatrybił, możesz wrócić do aplikacji :D')
            except UnicodeDecodeError:  # UnicodeDecodeError may occur if user's hostname contains non ASCII characters
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file_native, scopes)
                credentials = flow.run_console('Zaloguj się do aplikacji za pomocą linku: {url}',
                                               'Wprowadź otrzymany kod uwierzytelnienia: ')
            print(credentials.to_json())
            pickle.dump(credentials, f)
            return credentials


def create_yt_service_instance():
    api_service_name = 'youtube'
    api_version = 'v3'
    credentials = get_yt_credentials()
    yt = build(api_service_name, api_version, credentials=credentials)
    print('Utożsamienie w youtube pomyślne')
    return yt


class YoutubeAPI:

    def __init__(self):
        self.yt = create_yt_service_instance()

    def list_playlists(self):
        request = self.yt.playlists().list(
            part='snippet',
            mine=True
        )

        print(request)
        response = request.execute()
        print(json.dumps(response, indent=4))

    def get_liked_videos_playlist_id(self) -> str:
        request = self.yt.channels().list(part='contentDetails', mine=True)
        response = request.execute()
        return response['items'][0]['contentDetails']['relatedPlaylists']['likes']

    def get_user_name(self) -> str:
        request = self.yt.channels().list(part='snippet', mine=True)
        response = request.execute()
        return response['items'][0]['snippet']['title']

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

    @timer
    def get_videos_topics(self, IDs) -> dict:
        print('Pobieranie informacji o wybranych filmach', end='')
        items = {}
        step = 50
        item_packs = [IDs[i:i + step] for i in range(0, len(IDs), step)]
        for pack in item_packs:
            print('.', end=' ')
            request = self.yt.videos().list(
                part='snippet, topicDetails',
                id=','.join(pack)
            )
            response = request.execute()
            for item in response['items']:
                items[item['snippet']['title']] = item['topicDetails'][
                    'topicCategories'] if 'topicDetails' in item else None
        print()
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
        return [line.strip() for line in f]


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
        else:
            pass
    return filtered_titles


def main():
    youtube = YoutubeAPI()

    # choice = input('wczytac z pliku? ')
    # choice = True if choice[0] in ('t', 'y') else False
    # yt_vids = youtube.get_titles_from_playlist('LLdbdHlxCs0jEI6oPKl5um3g')  # my liked items playlist
    # write_titles_to_file(choice, yt_vids)
    # youtube.list_playlists()
    # youtube.testing()
    # playlist_id = input('Podaj ID playlisty: ')

    # video_IDs = get_IDs_from_file('videcho_IDs.txt')
    # liked_playlist = youtube.get_liked_videos_playlist_id()
    # video_IDs = youtube.get_IDs_from_playlist('PLeCdlPO-XhWFzEVynMsmosfdRsIZXhZi0')  # 500 music videos
    # video_IDs = youtube.get_IDs_from_playlist(playlist_id)
    # video_IDs = youtube.get_IDs_from_playlist('PL3666F5DD61E96B6D')  # 1109 music videos
    video_IDs = youtube.get_IDs_from_playlist('PL4hyqxN3umpYkkEEbBJCQD9vy4JLSE3-k')  # 1109 music videos
    # video_IDs = youtube.get_IDs_from_playlist(liked_playlist)
    # video_IDs = youtube.get_IDs_from_playlist('PL8cG8AVijUMg0PScFy9IcUUKxL6qW8Bfa')  # Em's songs
    # video_IDs = youtube.get_IDs_from_playlist('PLbpvZGLuRoECKlZ2i8eshh-88aEiQ63n0')  # Polish songs
    # video_IDs = youtube.get_IDs_from_playlist('PLkqz3S84Tw-RrA5S0qoVYlQ3CmwIljp3j')  # different 499 music videos
    # video_IDs = youtube.get_IDs_from_playlist('PLURwsAewiTh2Teoh_xo3so_INYL9m5Jh-')  # 1066 "upbeat songs"
    # video_IDs = youtube.get_IDs_from_playlist('PLgaFNC_I_Zkk5nCZM5RVyF0giKHfMx2Sn')  # 3413 2010 decade songs
    # video_IDs = youtube.get_IDs_from_playlist('PL2LdWs9O2ICpu0oYkVjNio_fzoWU7mZ6v')  # Huge music playlist 3329 songs
    # video_IDs = youtube.get_IDs_from_playlist('PLWwAypAcFRgKAIIFqBr9oy-ZYZnixa_Fj')  # 5k rock playlist 4989
    # video_IDs = youtube.get_IDs_from_playlist('PL6T-wOsBCQccPn2QSjgUSU8lKvbBv0NCN')  # Muzyka lata 2000-2010 / 1542 songs
    # video_IDs = youtube.get_IDs_from_playlist('PLd9auH4JIHvupoMgW5YfOjqtj6Lih0MKw')  # 80s music 426
    write_IDs_to_file(video_IDs)
    print(len(video_IDs))
    video_topics = youtube.get_videos_topics(video_IDs)
    write_topics_to_file(video_topics)
    filtered_videos = filter_videos_by_topic(video_topics, 'music')
    print(len(filtered_videos))
    write_titles_to_file(filtered_videos, file_path='filtered_videos.txt')
    # z = youtube.get_topic_videos_from_playlist('LLdbdHlxCs0jEI6oPKl5um3g', 'Music')
    # for item in z:
    #     print(item)
    # print(len(z))
    pass


if __name__ == '__main__':
    main()
    pass
