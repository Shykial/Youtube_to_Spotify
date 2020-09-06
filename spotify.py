import csv

import requests
import json
import re
import concurrent.futures
import datetime as dt
import time

# from spotify_secrets import spotify_client_ID as s_client_ID, spotify_client_Secret as s_client_Secret
# from spotify_secrets import spotify_token as s_token
from spotify_secrets import *


class SpotifyAPI:

    def __init__(self):
        self.redirect_uri = 'https://i.pinimg.com/564x/0c/1c/a1/0c1ca1955e2b0c5469ba17da2b1b9b96.jpg'
        self.token = self.get_token()
        self.auth_header = {'Authorization': f'Bearer {self.token}'}
        self.user_id = self.get_user_id()

    def request_token(self, data) -> str:
        r = requests.post('https://accounts.spotify.com/api/token', data=data)
        response_dict = r.json()
        print(response_dict)
        token = response_dict['access_token']

        # new refresh_token is not given within json response when querying for a token with valid refresh_token
        refresh_token = response_dict['refresh_token'] if 'refresh_token' in response_dict else s_refresh_token
        token_exp_time = dt.datetime.now() + dt.timedelta(seconds=response_dict['expires_in'])
        time_format = '%d-%m-%Y %H:%M:%S'

        with open('spotify_secrets.py', 'r') as f:
            contents = f.read().splitlines()
            for i, line in enumerate(contents):
                if 's_token = ' in line:
                    contents[i] = f"s_token = '{token}'"
                    contents[i + 1] = f"s_token_expiry_date = '{token_exp_time.strftime(time_format)}'"
                    contents[i + 2] = f"s_refresh_token = '{refresh_token}'"
                    break

        with open('spotify_secrets.py', 'w') as f:
            f.write('\n'.join(contents))

        return token

    def obtain_new_token(self) -> str:
        params = {'client_id': s_client_ID,
                  'response_type': 'code',
                  'redirect_uri': self.redirect_uri,
                  'scope': 'user-read-private playlist-modify-private playlist-modify-public'}

        r = requests.get('https://accounts.spotify.com/authorize', params=params)

        redirected_link = input(f'''Zaloguj się do aplikacji Spotify za pomocą poniższego linku:
{r.url}
I wpisz poniżej link, do którego zostałeś przekierowany/a po zalogowaniu:
''')

        auth_code = redirected_link.split('code=')[-1]

        # client_creds = f'{s_client_ID}:{s_client_Secret}'.encode()
        # client_creds_b64 = base64.b64encode(client_creds).decode()

        # headers = {'Authorization': f'Basic {client_creds_b64}'}

        data = {'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': s_client_ID,
                'client_secret': s_client_Secret}
        return self.request_token(data)

    def get_token(self) -> str:
        time_format = '%d-%m-%Y %H:%M:%S'
        if input('Stworzyć nowy token? [t/n]: ')[0] not in 'ty':
            # checking if token didn't expire already
            try:
                if dt.datetime.strptime(s_token_expiry_date, time_format) > dt.datetime.now():
                    print('token nadal ważny')
                    return s_token
                else:
                    print('tworzę nowy token')
                    data = {'grant_type': 'refresh_token',
                            'refresh_token': s_refresh_token,
                            'client_id': s_client_ID,
                            'client_secret': s_client_Secret}
                    return self.request_token(data)

                # add request obtaining new token from the refreshed one
            except ValueError:
                return self.obtain_new_token()
        else:
            return self.obtain_new_token()
        # return token

    def get_user_id(self) -> str:
        headers = self.auth_header
        r = requests.get('https://api.spotify.com/v1/me', headers=headers)
        return r.json()['id']

    def create_playlist(self, name) -> str:
        headers = {**self.auth_header,
                   'Content-Type': 'application/json'}
        payload = {'name': name,
                   'public': 'false',
                   'description': 'testowa playlista'}
        data = json.dumps(payload)

        r = requests.post(f'https://api.spotify.com/v1/users/{self.user_id}/playlists', headers=headers, data=data)
        # print(r.text)
        return r.json()['id']

    def add_tracks_to_playlist(self, playlist_id, *items):
        headers = self.auth_header

        # request can handle at most 100 items at once, therefore splitting into packs
        step = 100
        item_packs = [items[i:i + step] for i in range(0, len(items), step)]
        print('Dodawanie utworów do playlisty', end='')
        for pack in item_packs:
            print(' .', end='')
            payload = {'uris': pack}
            data = json.dumps(payload)
            requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, data=data)

    def clear_playlist(self, playlist_id):
        headers = self.auth_header
        data = json.dumps({'uris': []})
        print(data)
        r = requests.put(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, data=data)
        print(r.text)

    def search_items(self, search_queries, old_items, res_type='track',
                     limit=1) -> list:  # returns list of objects URIs todo delete old items when no longer needed
        headers = self.auth_header
        items_list = []
        # items_not_found = []
        items_not_found = {}
        counter = 1
        for query, old_item in zip(search_queries, old_items):
            print(f'Wyszukanie {counter}, obecnie w liście: {len(items_list)}')
            params = {'q': query,
                      'type': res_type,
                      'limit': limit}
            response_type = res_type + 's'
            # 5 attempts on getting proper API response as it may result in incorrect response sometimes
            for attempt in range(1, 6):
                r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                try:
                    if returned_items := r.json()[response_type]['items']:
                        items_list.append(returned_items[0]['uri'])
                    else:
                        # pattern = re.compile(r'ft\.?|feat.?', flags=re.IGNORECASE)
                        # if pattern.search(params['q']):
                        #     params['q'] = pattern.sub('', params['q'])
                        #     continue
                        # items_not_found.append(query)
                        items_not_found[query] = old_item
                    break
                except KeyError:
                    if r.json()['error']['message'] == 'No search query':
                        break
                    time.sleep(int(r.headers['retry-after']))
                    print(f'attempt: {attempt}')
                    continue
                # try:
                #     r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                #     returned_items = r.json()[response_type]['items']
                #     if returned_items:
                #         items_list.append(returned_items[0]['uri'])
                # except KeyError:
                #     r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                #     returned_items = r.json()[response_type]['items']
                #     if returned_items:
                #         items_list.append(returned_items[0]['uri'])
            counter += 1
        write_dict_items_to_file(items_not_found, 'titles_not_found.tsv')
        # write_items_to_file(items_not_found, 'titles_not_found.txt')
        return list(set(items_list))  # using list -> set -> list to filter duplicate items

    def search_items_threading(self, *query_strings, res_type='track', limit=1) -> list:  # returns list of objects URIs
        headers = self.auth_header
        items_list = []
        self.counter = 1

        def inner(query):
            self.counter += 1
            print(f'Wyszukanie {self.counter}, obecnie w liście: {len(items_list)}')
            params = {'q': query,
                      'type': res_type,
                      'limit': limit}
            response_type = res_type + 's'
            # 5 attempts on getting proper API response as it may result in incorrect response sometimes
            for attempt in range(1, 100):
                r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                try:
                    if returned_items := r.json()[response_type]['items']:
                        items_list.append(returned_items[0]['uri'])
                    break
                except KeyError:
                    time.sleep(int(r.headers['retry-after']))
                    print(f'attempt: {attempt}')
                    continue
                # try:
                #     r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                #     returned_items = r.json()[response_type]['items']
                #     if returned_items:
                #         items_list.append(returned_items[0]['uri'])
                # except KeyError:
                #     r = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
                #     returned_items = r.json()[response_type]['items']
                #     if returned_items:
                #         items_list.append(returned_items[0]['uri'])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for query in query_strings:
                time.sleep(.075)
                executor.submit(inner, query)

        return items_list


def write_items_to_file(items, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(item + '\n')


def write_dict_items_to_file(items: dict, file_path):  # todo delete this method when no longer needed
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        tsv_writer = csv.writer(f, delimiter='\t')
        for key, val in items.items():
            tsv_writer.writerow([key, val])


def get_corrected_titles(titles):
    """Using regex to filter words from the video title,
     which are most likely meaningless for the music track title itself. """

    pattern = re.compile(
        r'lyrics | (?:official|music)\s*video | of+icial | M[/\\]?V | audio | HQ | High\sQuality| HD |High\sDefinition | instrumental | vevo(?:\s+ctrl|\s+DSCVR)? | \bfeat.?\b | \bft\.?\b | remix | edit | cover| \blive\b (?:\s+session|\s+performance)? | \bx\b | prod\.?.* |(?<=\s)& | (?<=\s)and(?=\s.*-)| (?<!\w)-(?!\w) | (?<=\s)(?:with|vs\.?)(?=\s.*-) |[12][9012]\d{2}$ | \(.*\) | \[.*] |[._] | [^\w\s.\'*$\u00c0-\u017e&-]',
        flags=re.IGNORECASE | re.X | re.MULTILINE | re.UNICODE)  # 466 yo // 1000/1109 yo 1019 yo 1024 yo 1033 yo # 468/500 # 1042/1109 yo # 1069/1109
    # different playlist 449/495 # 465 # 469/495
    # 469/500
    new_titles = []
    for title in titles:
        new_title = pattern.sub('', title)
        new_title = re.sub(re.compile(r'\s{2,}'), ' ', new_title)  # trimming multiple whitespaces
        new_titles.append(new_title)

    return new_titles

    # return [re.sub(re.compile(r'\s{2,}'), ' ', pattern.sub('', title)) for title in titles]

    # print(new_string)


if __name__ == '__main__':
    spotify = SpotifyAPI()
    playlist_1 = spotify.create_playlist('From my liked items better')
    with open('filtered_videos.txt', 'r', encoding='utf-8') as f:
        items = [line.strip() for line in f]
    titles = get_corrected_titles(items)
    tracks = spotify.search_items(titles, items)
    print(len(tracks))
    # tracks = spotify.search_items_threading(*items)
    print('yoo')
    # spotify.add_tracks_to_playlist('7jL6SyXjlt1P0Rz9uDoo9o', *tracks)
    spotify.add_tracks_to_playlist(playlist_1, *tracks)
    # input('yoo')
    # spotify.clear_playlist('7jL6SyXjlt1P0Rz9uDoo9o')
    # one = spotify.search_items('Kendrick Lamar', 'Eminem', 'Rihanna', 'Kanye West', 'Mozart', 'Friderick Chopin', 'rysiek z klanu hehe xD', res_type='artist')
