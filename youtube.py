import json

from googleapiclient.discovery import build
import google_auth_oauthlib.flow
import pickle


class YoutubeAPI:

    def __init__(self):
        self.yt = self.create_yt_service_instance()

    def create_yt_service_instance(self):
        api_service_name = "youtube"
        api_version = "v3"
        credentials = self.get_yt_credentials()
        return build(api_service_name, api_version, credentials=credentials)

    def get_yt_credentials(self):
        client_secrets_file = "yt_secrets.json"
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        with open('creds', 'rb+') as f:
            try:
                return pickle.load(f)
            except EOFError:
                print('jednak nie to')
                credentials = flow.run_console()
                pickle.dump(credentials, f)
                return credentials

    def get_titles_from_playlist(self, playlist_id) -> list:
        titles = []
        print('mowie do API', end='')

        # getting first page of the returned content
        playlist_items_request = self.yt.playlistItems().list(
            part="snippet",
            # myRating="like",
            maxResults="50",  # number of items can be from range (1, 50) inclusive
            playlistId=playlist_id
        )

        response = playlist_items_request.execute()
        for item in response["items"]:
            # print(json.dumps(item, indent=4))
            titles.append(item["snippet"]["title"])

        # while loop to get all the next pages by referring to the previous one,
        # breaking from the loop when the response is None - meaning there is no subsequent page
        while True:
            print('.', end=' ')
            playlist_items_request = self.yt.videos().list_next(playlist_items_request, response)

            if playlist_items_request:
                response = playlist_items_request.execute()
            else:
                break

            for item in response["items"]:
                titles.append(item["snippet"]["title"])

        return [t for t in titles if t not in ("Private video", "Deleted video")]

    def titles_to_file(self, choice):
        with open('yt_vids_list.txt', 'w+', encoding='UTF-8') as f:
            if (t := f.readlines()) and choice:
                yt_vids = [line.strip() for line in t]
            else:
                yt_vids = self.get_titles_from_playlist("PL_eFXywmQJjE62uK1pwJnNdpCvuQfX2lR")

                for line in yt_vids:
                    f.write(line + '\n')
                print('jajo')
            # print(yt_vids)
            print('\n'.join(yt_vids))
            print(len(yt_vids))


def main():
    # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    youtube = YoutubeAPI()

    choice = input('wczytac z pliku? ')
    choice = True if choice[0] in ('t', 'y') else False
    youtube.titles_to_file(choice)


if __name__ == '__main__':
    main()
