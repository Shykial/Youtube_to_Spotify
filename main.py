import requests
import os
import json
#
# payload = {'v': 'tb8gHvYlCFs', 't': '1053s'}
# r = requests.get('https://www.youtube.com/watch', params=payload)
#
# print(r.url) # https://www.youtube.com/watch?v=tb8gHvYlCFs&t=1053s
# os.system(f'start {r.url}')
#
# from secrets import Youtube_API_Key

from googleapiclient.discovery import build
import google_auth_oauthlib.flow
import pickle


def get_yt_credentials():
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


def main():
    # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    choice = input('wczytac z pliku? ')
    choice = True if choice[0] in ('t', 'y') else False

    with open('yt_vids_list.txt', 'w+', encoding='UTF-8') as f:
        if (t := f.readlines()) and choice:
            yt_vids = [line.strip() for line in t]
        else:

            api_service_name = "youtube"
            api_version = "v3"

            credentials = get_yt_credentials()

            youtube_service = build(api_service_name, api_version,
                                    credentials=credentials)

            yt_vids = []
            print('mowie do API', end='')
            s_liked_request = youtube_service.playlistItems().list(
                part="snippet",
                # myRating="like",
                maxResults="50",
                # playlistId="LLdbdHlxCs0jEI6oPKl5um3g"
                playlistId="PL813690032BF2CE3C"
            )

            response = s_liked_request.execute()
            for item in response["items"]:
                yt_vids.append(item["snippet"]["title"])

            while True:
                print('.', end=' ')
                s_liked_request = youtube_service.videos().list_next(s_liked_request, response)

                # s_liked_request = youtube_service.videos().list(
                #     part="snippet",
                #     myRating="like",
                #     maxResults="25",
                #     pageToken=nextPageToken
                # )
                #
                if s_liked_request:
                    response = s_liked_request.execute()
                else:
                    break
                # # print(json.dumps(response, indent=4))
                #
                # # for item in response["items"]:
                # #     print(item["snippet"]["title"])
                # #
                for item in response["items"]:
                    yt_vids.append(item["snippet"]["title"])
                #
                # # if (t := response["nextPageToken"]):
                # #     nextPageToken = t
                #
                # try:
                #     nextPageToken = response["nextPageToken"]
                # except KeyError:
                #     break
                yt_vids = [vid for vid in yt_vids if vid not in ("Private video", "Deleted video")]
            for line in yt_vids:
                f.write(line + '\n')
            print('jajo')
        # print(yt_vids)
        print('\n'.join(yt_vids))
        print(len(yt_vids))

        # formatted_response = json.dumps(response, indent=4)
        # print(formatted_response)

        # s = json.dumps(kb_response['items'], indent=4)
        # print('\nKrzysztof Bober youtube stats:')
        # print(s)
        import timeit
        #
        # def f1():
        #     import pprint as pp
        #     s = pp.pformat(response['items'])
        #     return s
        #
        # def f2():
        #     import json
        #     s = json.dumps(response['items'], indent=4)
        #     return s
        #
        # print(timeit.timeit(f1, number=1000))
        # print(timeit.timeit(f2, number=1000))


pass

if __name__ == '__main__':
    main()
