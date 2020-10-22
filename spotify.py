import concurrent.futures
import csv
import datetime as dt
import json
import os
import re
import time

import requests

from decorators import timer
# from spotify_secrets import spotify_client_ID as s_client_ID, spotify_client_Secret as s_client_Secret
# from spotify_secrets import spotify_token as s_token
from spotify_secrets import *


def request_token(data) -> str:
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


def get_playlist_id_from_link(link: str) -> str:
    if 'playlist' in (t := link.split('/')):
        return t[-1]
    raise AttributeError


class SpotifyAPI:

    def __init__(self, gui=False):
        self.gui = gui
        self.redirect_uri = 'https://i.pinimg.com/564x/0c/1c/a1/0c1ca1955e2b0c5469ba17da2b1b9b96.jpg'
        if not self.gui:
            self.token = self.get_token()
            # self.token = self.obtain_new_token()
            self.set_auth_header()
            self.set_user_id()

    def set_user_id(self):
        self.user_id = self.get_user_id()

    def set_auth_header(self):
        self.auth_header = {'Authorization': f'Bearer {self.token}'}

    def get_auth_link(self) -> str:
        params = {'client_id': s_client_ID,
                  'response_type': 'code',
                  'redirect_uri': self.redirect_uri,
                  'scope': 'user-read-private playlist-modify-private playlist-modify-public'}
        r = requests.get('https://accounts.spotify.com/authorize', params=params)
        return r.url

    def obtain_new_token(self, redirected_link=None) -> str:
        if not self.gui:
            redirected_link = input(f'''Zaloguj się do aplikacji Spotify za pomocą poniższego linku:
{self.get_auth_link()}
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
        return request_token(data)

    def get_token(self) -> str:
        time_format = '%d-%m-%Y %H:%M:%S'
        # if input('Stworzyć nowy token? [t/n]: ')[0] not in 'ty':
        # checking if token didn't expire already
        try:
            if s_token and dt.datetime.strptime(s_token_expiry_date, time_format) > dt.datetime.now():
                print('token nadal ważny')
                return s_token
            elif s_refresh_token:
                print('tworzę nowy token')
                data = {'grant_type': 'refresh_token',
                        'refresh_token': s_refresh_token,
                        'client_id': s_client_ID,
                        'client_secret': s_client_Secret}
                return request_token(data)
            else:
                raise BaseException

            # add request obtaining new token from the refreshed one
        except (ValueError, BaseException):
            return self.obtain_new_token() if not self.gui else None
        # else:
        #     return self.obtain_new_token()
        # return token

    def get_user_id(self) -> str:
        headers = self.auth_header
        r = requests.get('https://api.spotify.com/v1/me', headers=headers)
        return r.json()['id']

    def get_user_name(self) -> str:
        headers = self.auth_header
        r = requests.get('https://api.spotify.com/v1/me', headers=headers)
        return r.json()['display_name']

    def get_playlist_name(self, playlist_id: str) -> str:
        headers = self.auth_header
        r = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers)
        return r.json()['name']

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

    @timer
    def search_items(self, search_queries, old_items, res_type='track',
                     limit=1) -> list:  # returns list of objects URIs todo delete old items when no longer needed
        headers = self.auth_header
        items_list = []
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
                        if (t := re.compile(r'\d{4}')).search(params['q']):
                            params['q'] = t.sub('', params['q'])
                            continue

                        if (t := re.compile(r'\blive\b', flags=re.IGNORECASE)).search(params['q']):
                            params['q'] = t.sub('', params['q'])
                            continue
                        items_not_found[params['q']] = old_item
                    break
                except KeyError:
                    if r.json()['error']['message'] == 'No search query':
                        break
                    time.sleep(int(r.headers['retry-after']))
                    print(f'attempt: {attempt}')
                    continue
                except (ConnectionError, TimeoutError):
                    os.system('rundll32 user32.dll,MessageBeep')
                    os.system('rundll32 user32.dll,MessageBeep')
                    input('Connection error, check connection and press enter to proceed')
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
        print(f'With potential duplicates: {len(items_list)}')
        return list(set(items_list))  # using list -> set -> list to filter duplicate items

    @timer
    def search_items_threading(self, search_queries, old_items, res_type='track',
                               limit=1) -> list:  # returns list of objects URIs
        headers = self.auth_header
        items_list = []
        items_not_found = {}
        self.counter = 1

        def inner(query, old_item):
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
            self.counter += 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for query, old_item in zip(search_queries, old_items):
                time.sleep(0.07)
                executor.submit(inner, query, old_item)
        print(f'With potential duplicates: {len(items_list)}')
        return list(set(items_list))  # using list -> set -> list to filter duplicate items


def reset_stored_token():
    with open('spotify_secrets.py', 'r') as f:
        contents = f.read().splitlines()
        for i, line in enumerate(contents):
            if 's_token = ' in line:
                contents[i] = f"s_token = ''"
                contents[i + 1] = f"s_token_expiry_date = ''"
                contents[i + 2] = f"s_refresh_token = ''"
                break

    with open('spotify_secrets.py', 'w') as f:
        f.write('\n'.join(contents))


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

    # pattern = re.compile(
    #     r'(?:official|music|lyrics?|HD|original)\s*video | (?:with\s)?lyrics?(?:\son\s(?:the\s)?screen)? | '
    #     r'of+icial | M[/\\]?V | \baudio\b | HQ | High\sQuality| movie\sclip |(?:480|720|1080)p | Uncensored |'
    #     r'\bHD\b |High\sDefinition | instrumental | vevo(?:\s+ctrl|\s+DSCVR)? | \bfeat.?\b | \bft\.?\b | remix | '
    #     r'\bedit\b | \bcover\b | \blive\b (?:\s+session|\s+performance) | (?<=\.)(?:wmv|avi|mp3|mp4) | \|.* |'
    #     r'\bx\b | prod\.?.* |(?<=\s)& | (?<=\s)and(?=\s.*-)| (?<!\w)-(?!\w) | (?<=\s)(?:with|vs\.?)(?=\s.*-) |'
    #     r'[12][9012]\d{2}$ | \(.*?\) | 【.*?】 | (?<!p)!(?!nk) |\[.*] |[._] | [^\w\s.\'*$\u00c0-\u017e&!-]',
    #     flags=re.IGNORECASE | re.X | re.MULTILINE | re.UNICODE)

    pattern = re.compile(
        r'(?:official|music|lyrics?|HD|original)\s*video | (?:with\s)?lyrics?(?:\son\s(?:the\s)?screen)? | of+icial | M[/\\]?V | \baudio\b | HQ | High\sQuality| (?:movie|promo)\sclip |(?:480|720|1080)p | 4K | Uncensored | \bU?HD\b |High\sDefinition | instrumental | vevo(?:\s+ctrl|\s+DSCVR)? | \bfeat.?\b | \bft\.?\b | remix | \bedit\b | \bcover\b | \blive\b (?:\s+session|\s+performance) | MTV(?:\sUnplugged)? |(?<=\.)(?:wmv|avi|mp3|mp4) | (?:\||(?://)).* |\bx\b | prod\.?.* |(?<=\s)& | (?<=\s)and(?=\s.*-)| (?<!\w)-(?!\w) | (?<=\s)(?:with|vs\.?)(?=\s.*-) |[12][9012]\d{2}$ | (?:\d{2}[/.-]){2}(?:[12][9012])?\d{2}(?!\d) |\(.*?\) | 【.*?】 | (?<!p)!(?!nk) |\[.*] | [._] | [^\w\s.\'*$\u00c0-\u017e&!-]',
        flags=re.IGNORECASE | re.X | re.MULTILINE | re.UNICODE)
    # 466 yo // 1000/1109 yo 1019 yo 1024 yo 1033 yo # 468/500 # 1042/1109 yo # 1069/1109
    # different playlist 449/495 # 465 # 469/495
    # 469/500
    # 664/696
    # 1021/1058 update 1023/1058
    # 465/487
    # 3350/3413 >98% !!! update 3358
    # 407/426 update 410 update 411
    # 468/487
    # 4515/4989 update 4559 update 4678
    # 1073/1110 96,(6)%
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
    # playlist_1 = spotify.create_playlist('From my liked items 2')
    playlist_1 = spotify.create_playlist('prysznic')
    with open('filtered_videos.txt', 'r', encoding='utf-8') as f:
        old_items = [line.strip() for line in f]
    titles = get_corrected_titles(old_items)
    tracks = spotify.search_items(titles, old_items)
    # tracks = spotify.search_items_threading(titles, items)
    print(len(tracks))
    print('yoo')
    # spotify.add_tracks_to_playlist('7jL6SyXjlt1P0Rz9uDoo9o', *tracks)
    spotify.add_tracks_to_playlist(playlist_1, *tracks)
    # input('yoo')
    # spotify.clear_playlist('7jL6SyXjlt1P0Rz9uDoo9o')
    # one = spotify.search_items('Kendrick Lamar', 'Eminem', 'Rihanna', 'Kanye West', 'Mozart', 'Friderick Chopin', 'rysiek z klanu hehe xD', res_type='artist')
    os.system('rundll32 user32.dll,MessageBeep')
