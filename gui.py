import tkinter as tk
import tkinter.messagebox
# import tkinter.font
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from httplib2 import ServerNotFoundError
from requests import ConnectionError
import spotify
import youtube
import time
import webbrowser


def open_link(url: str):
    webbrowser.open(url, new=2)  # new=2 for browser to open link within new tab if possible


def quit_and_destroy(widget):
    widget.quit()
    widget.destroy()


def enable_widget(widget: tk.Widget):
    if widget['state'] != 'enabled':
        widget.configure(state='enabled')


def disable_widget(widget: tk.Widget):
    if widget['state'] != 'disabled':
        widget.configure(state='disabled')


class GUI(tk.Tk):

    def resize_bg_image(self, event):
        new_size = (event.width, event.height)

        # this is given when root window opens for the first time, therefore needing to ignore it
        if new_size == (1, 1):
            return

        self.bg_PIL_image = self.bg_PIL_image.resize((event.width, event.height), Image.ANTIALIAS)
        self.bg_image = self.bg_image = ImageTk.PhotoImage(self.bg_PIL_image)
        self.bg_label.config(image=self.bg_image)
        print('yo')

    def __init__(self):
        super().__init__()
        self.wm_minsize(width=700, height=600)

        # for item in tkinter.font.families():
        #     print(item)

        self.title('Youtube to Spotify')
        self.spotify = None
        self.youtube = None
        # self.bg_color = '#F0B3D1'
        # self.bg_color = '#B2C6DB'
        self.bg_color = '#C2CBDB'
        # self.bg_color = '#2D0050'
        # self.bg_image = tk.PhotoImage(file='images/background.png')

        self.bg_PIL_image = Image.open('images/background.png').resize((700, 500), Image.ANTIALIAS)
        self.bg_image = ImageTk.PhotoImage(self.bg_PIL_image)

        # self.bg_label = tk.Label(self, image=self.bg_image)
        # self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # self.bg_label.bind('<Configure>', self.resize_bg_image)

        self.style = ttk.Style()
        # ttk.Style().theme_use('xpnative')
        # ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        self.style.configure('.', background=self.bg_color, font=('Arial', 11))
        self.style.configure('smaller_italic.TLabel', background=self.bg_color, font=('Arial', 9, 'italic'))
        self.style.configure('s_auth_label.TLabel', background=self.bg_color, foreground='green',
                             font=('Noto Serif', 11, 'italic'))
        self.style.configure('yt_auth_label.TLabel', background=self.bg_color, foreground='#DB2917',
                             font=('Noto Serif', 11, 'italic'))

        self.init_upper_frame()

        # self.lower_frame = tk.Frame(self, highlightbackground='green', highlightthickness=6)
        self.init_lower_frame()
        # self.upper_frame.place(relheight=0.3, relwidth=1)

        # print(self.s_auth_button['background'])
        # print('elo')
        # self.yt_auth_button.config(image=spotify_logo)

        # s_auth_button.grid(column=0, row=0)
        # yt_auth_button.grid(column=1, row=0)
        # s_auth_button.pack(side='left')
        # yt_auth_button.pack(side='right')
        # self.lift()
        # self.wm_attributes("-disabled", True)
        # self.wm_attributes('-transparentcolor', 'green')
        # self.attributes('-alpha', 0.5)

        self.mainloop()

    def init_upper_frame(self):
        self.upper_frame = tk.Frame(self, borderwidth=12, background=self.bg_color)
        # self.upper_frame = tk.Frame(self.bg_label, borderwidth=12, bg='')
        self.upper_frame.place(relheight=0.3, relwidth=1)
        self.tick_image = tk.PhotoImage(
            file='images/tick.png')  # keeping referance to the image so that it's not garbage collected
        self.init_auth_buttons()
        self.logon_label = tk.Label(self.upper_frame, text='Zaloguj się\nza pomocą przycisków obok',
                                    font=('Courier new Baltic', 13), bg=self.bg_color)
        self.logon_label.place(relx=0.5, rely=0.5, anchor='center')

    def init_lower_frame(self):

        def disable_entry():
            disable_widget(playlist_entry)
            disable_widget(get_playlist_button)
            playlist_entry_label.configure(foreground='grey')
            playlist_title_label.configure(foreground='grey')

        def enable_entry():
            enable_widget(playlist_entry)
            enable_widget(get_playlist_button)
            playlist_entry_label.configure(foreground='black')

        def check_and_label_title(link: str):
            playlist_id = youtube.get_request_param_from_link(link, 'list')
            playlist_name = self.youtube.get_playlist_name(playlist_id)
            playlist_title_label.configure(text=playlist_name)

        self.lower_frame = tk.Frame(self, background=self.bg_color, highlightbackground='green', highlightthickness=6)
        self.lower_frame.place(rely=0.3, relwidth=1, relheight=0.7)

        self.yt_playlist_frame = tk.Frame(self.lower_frame, background=self.bg_color, highlightbackground='black',
                                          highlightthickness=4)
        self.yt_playlist_frame.place(x=0, y=0, relwidth=1, relheight=0.4)

        liked_videos_choice_label = tk.Label(self.yt_playlist_frame, background=self.bg_color,
                                             font=('Calibri', 13, 'bold'),
                                             text='Wybierz playlistę youtube do przetworzenia:')

        liked_videos_choice_label.place(y=15, relx=0.5, anchor='center', height=30)

        selected_playlist = None

        liked_videos_rb = ttk.Radiobutton(self.yt_playlist_frame, text='Moje polubione filmy',
                                          variable=selected_playlist, value='liked items',
                                          command=disable_entry)

        liked_videos_rb.place(in_=liked_videos_choice_label, y=50, relx=0.3, anchor='w')

        other_playlist_rb = ttk.Radiobutton(self.yt_playlist_frame, text='Inna playlista',
                                            variable=selected_playlist, value='other playlist',
                                            command=enable_entry)
        other_playlist_rb.place(in_=liked_videos_rb, y=40, anchor='w')

        playlist_entry_label = tk.Label(self.yt_playlist_frame, background=self.bg_color, foreground='grey',
                                        font=('TkDefaultFont', 10), text='Podaj link do playlisty: ')
        playlist_entry_label.place(rely=0.6, relx=0.015)

        self.update()
        playlist_entry = ttk.Entry(self.yt_playlist_frame, state='disabled')
        playlist_entry.place(in_=playlist_entry_label, x=playlist_entry_label.winfo_width(),
                             width=self.yt_playlist_frame.winfo_width() * 0.58)

        self.update()
        playlist_title_label = ttk.Label(self.yt_playlist_frame, style='smaller_italic.TLabel')
        playlist_title_label.place(in_=playlist_entry, y=playlist_entry.winfo_height() + 13, relx=0.5, anchor='center')

        self.update()
        get_playlist_button = ttk.Button(self.yt_playlist_frame, text='Sprawdź',
                                         state='disabled', command=lambda: check_and_label_title(playlist_entry.get()))
        get_playlist_button.place(in_=playlist_entry, x=playlist_entry.winfo_width() + 55, y=13,
                                  anchor='center', height=29)

        self.s_playlist_frame = tk.Frame(self.lower_frame, background=self.bg_color, highlightbackground='black',
                                         highlightthickness=4)
        self.s_playlist_frame.place(x=0, rely=0.4, relwidth=1, relheight=0.6)

    def init_auth_buttons(self):
        self.spotify_logo = tk.PhotoImage(file='images/spotify_icon.png')
        self.youtube_logo = tk.PhotoImage(file='images/youtube_icon.png')
        self.style.configure('button.TButton', borderwidth=10, bordercolor='green', disabledbackground='red')
        self.style.configure('button2.TButton', borderwidth=10, background=self.bg_color)
        self.s_auth_button = ttk.Button(self.upper_frame, image=self.spotify_logo, command=self.spotify_init,
                                        style='button.TButton')
        self.yt_auth_button = ttk.Button(self.upper_frame, image=self.youtube_logo, command=self.youtube_init,
                                         style='button2.TButton')
        self.s_auth_button_relx = 0.8
        self.s_auth_button_rely = 0.5
        self.s_auth_button_kwargs = {'height': 110, 'width': 110,
                                     'relx': self.s_auth_button_relx, 'rely': self.s_auth_button_rely,
                                     'anchor': 'center'}
        self.yt_auth_button_relx = 0.2
        self.yt_auth_button_rely = 0.5
        self.yt_auth_button_kwargs = {'height': 110, 'width': 110,
                                      'relx': self.yt_auth_button_relx, 'rely': self.s_auth_button_rely,
                                      'anchor': 'center'}
        self.s_auth_button.place(self.s_auth_button_kwargs)
        self.yt_auth_button.place(self.yt_auth_button_kwargs)

    def check_buttons_state(self):
        if all(state == 'disabled' for state in (self.yt_auth_button['state'], self.s_auth_button['state'])):
            # self.logon_label.destroy()
            # self.tick_label = tk.label
            self.logon_label.config(image=self.tick_image, width=75, height=75)
            self.after(1500, self.logon_label.destroy)

    def spotify_init(self):

        def inner():
            # print(self.__class__.__name__)
            self.s_auth_button = tk.Button(self.upper_frame, image=self.spotify_logo,
                                           background=self.bg_color, state='disabled')
            self.s_auth_button.place(self.s_auth_button_kwargs)
            # self.s_auth_button.config(background=self.bg_color)
            s_auth_label.config(text=self.spotify.get_user_name(), style='s_auth_label.TLabel')
            # s_auth_label.config(text=get_logged_at_text(self.spotify.get_user_name()), style='auth_label.TLabel')
            self.check_buttons_state()

        def authenticate_response():
            response_link = entry.get()
            if not response_link:
                error_label = tk.Label(bottom_frame, text='Tak, lepiej najpierw uzupełnić pole tekstowe',
                                       font='Arial 11', foreground='red')
                error_label.place(relx=0.5, y=15, anchor='center')
                auth_window.after(2500, error_label.destroy)
            else:
                self.spotify.token = self.spotify.obtain_new_token(entry.get())
                success_label = tk.Label(bottom_frame, text='Udało się!',
                                         font='Arial 11', foreground='red')
                success_label.place(relx=0.5, y=15, anchor='center')
                auth_window.after(1500, lambda: quit_and_destroy(auth_window))
                self.after(1400,
                           self.focus_set)  # bringing back focus to the main window just before auth window gets destroyed

        try:
            self.spotify = spotify.SpotifyAPI(gui=True)
            if token := self.spotify.get_token():
                self.spotify.token = token
            else:
                auth_link = self.spotify.get_auth_link()
                print(auth_link)

                auth_window = tk.Toplevel()
                auth_window.title('Elo Mordeczki')
                auth_window.wm_minsize(width=600, height=280)
                top_frame = tk.Frame(auth_window)
                top_frame.place(relheight=0.5, relwidth=1)
                bottom_frame = tk.Frame(auth_window)
                bottom_frame.place(relheight=0.5, relwidth=1, rely=0.5)
                self.style.configure('s.TLabel', font='Arial 10', background=self['background'])
                text = ttk.Label(top_frame,
                                 text='Zaloguj się za pomocą przycisku poniżej, a następnie wklej adres linku z koteczkiem',
                                 justify='center', style='s.TLabel')
                text.pack(pady=15)
                self.style.configure('spotify.TButton', font='Calibri 12')
                link_button = ttk.Button(top_frame, text='Link', style='spotify.TButton',
                                         command=lambda: open_link(auth_link))
                link_button.pack(pady=5)
                entry = ttk.Entry(bottom_frame)
                entry.place(relwidth=0.7, relx=0.5, y=40, anchor='center')
                # text.bind('<Button-1>', lambda x: open_link(auth_link))
                entry.bind('<Return>', lambda e: authenticate_response())  # handling enter key on the entry box
                self.style.configure('x.TButton', font='Calibri 12 bold')
                submit_button = ttk.Button(bottom_frame, text='Loguj mnie!', style='x.TButton',
                                           command=authenticate_response)  # ✔
                submit_button.place(width=120, height=40, relx=0.5, y=75, anchor='center')
                auth_window.focus_set()
                auth_window.attributes('-topmost',
                                       True)  # always on top so that user can paste response code link straight away
                auth_window.mainloop()
                # self.spotify.token = self.spotify.obtain_new_token(rrr)

            self.spotify.set_auth_header()
            self.spotify.set_user_id()
        except ConnectionError:
            show_connection_error()
            return
        # style = ttk.Style()
        # style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)
        # style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)
        # self.s_auth_button.config(state='disabled', style='button2.TButton')
        s_auth_label = ttk.Label(self.upper_frame, text='Poprawnie zalogowano w spotify!',
                                 justify='center')
        # s_auth_label.place(relx=self.s_auth_button_relx, rely=self.s_auth_button_rely + 0.52, anchor='center')
        s_auth_label.place(in_=self.s_auth_button, y=self.s_auth_button.winfo_height() + 15,
                           relx=0.5, anchor='center')
        self.after(1000, inner)

    def youtube_init(self):
        def inner():
            self.yt_auth_button = tk.Button(self.upper_frame, image=self.youtube_logo,
                                            background=self.bg_color, state='disabled')
            self.yt_auth_button.place(self.yt_auth_button_kwargs)
            yt_auth_label.config(text=self.youtube.get_user_name(), style='yt_auth_label.TLabel')
            # yt_auth_label.config(text=get_logged_at_text(self.youtube.get_user_name()), style='auth_label.TLabel')
            self.update()
            self.check_buttons_state()

        try:
            self.youtube = youtube.YoutubeAPI()
        except ServerNotFoundError:
            show_connection_error()
            return
        yt_auth_label = ttk.Label(self.upper_frame, text='Poprawnie zalogowano w youtube!',
                                  justify='center')
        # yt_auth_label.place(relx=self.yt_auth_button_relx, rely=self.yt_auth_button_rely + 0.52, anchor='center')
        yt_auth_label.place(in_=self.yt_auth_button, y=self.yt_auth_button.winfo_height() + 15,
                            relx=0.5, anchor='center')
        # yt_auth_label.after_idle(yt_auth_label.config(style='auth_label.TLabel'))
        # self.update()
        # time.sleep(1)
        # inner()
        self.after(1000, inner)

        # self.after(1000, yt_auth_label.config(style='auth_label.TLabel'))


# depricated
def get_logged_at_text(string) -> str:
    logged = 'Zalogowana' if string.split()[0][-1] == 'a' else 'Zalogowany'
    return f'{logged}:\n{string}'


def show_connection_error():
    tk.messagebox.showerror('Błąd połączenia', 'Sprawdź połączenie sieciowe i spróbuj ponownie')


if __name__ == '__main__':
    gui = GUI()
