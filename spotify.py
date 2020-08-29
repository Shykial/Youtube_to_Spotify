import requests
import json
import base64
import datetime as dt
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
                  'scope': 'user-read-private playlist-modify-private'}

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
        r = requests.get('https://api.spotify.com/v1/me', headers=self.auth_header)
        return r.json()['id']

    def create_playlist(self, name) -> str:
        headers = {**self.auth_header,
                   'Content-Type': 'application/json'}
        payload = {'name': name,
                   'public': 'false',
                   'description': 'testowa playlista'}
        data = json.dumps(payload)

        r = requests.post(f'https://api.spotify.com/v1/users/{self.user_id}/playlists', headers=headers, data=data)
        print(r.text)
        return r.json()['id']

    def add_items_to_playlist(self, playlist_id, items):
        # request can handle at most 100 items at once, therefore splitting into packs
        headers = {**self.auth_header,
                   'Content-Type': 'application/json'}

        step = 100
        item_packs = [items[i:i + step] for i in range(0, len(items), step)]
        for pack in item_packs:
            payload = {'uris': pack}
            data = json.dumps(payload)
            r = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, data=data)
        pass

if __name__ == '__main__':
    spotify = SpotifyAPI()
