import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from httplib2 import ServerNotFoundError
from requests import ConnectionError
import spotify
import youtube
import time
import webbrowser


def open_link(url):
    webbrowser.open(url, new=2)


def say_sth(sth):
    print(sth)

def quit_and_destroy(widget):
    widget.quit()
    widget.destroy()


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.wm_minsize(width=700, height=500)
        self.title('Youtube to Spotify')
        self.spotify = None
        self.youtube = None
        self.bg_color = '#F0B3D1'
        # dimension
        self.frame = tk.Frame(self, borderwidth=12, bg=self.bg_color)
        self.frame.place(relheight=0.3, relwidth=1)
        # spotify_logo = ImageTk.PhotoImage(Image.open('images/spotify_icon.png'))
        self.spotify_logo = ImageTk.PhotoImage(Image.open('images/spotify_icon.png'))
        # self.spotify_logo = tk.PhotoImage(file='images/spotify_icon.png')
        self.spotify_logo_greyed = tk.PhotoImage(file='images/spotify_icon_greyed.png')
        self.youtube_logo = tk.PhotoImage(file='images/youtube_icon.png')
        self.tick_image = tk.PhotoImage(
            file='images/tick.png')  # keeping referance to the image so that it's not garbage collected

        self.style = ttk.Style()

        # s_label = ttk.Label(frame, image=spotify_logo)
        # s_label.image = spotify_logo
        # s_label.pack()
        self.style.configure('x.TLabel', font='Calibri 12', foreground='black', background='white')
        self.style.configure('w.Emergency.TLabel', foreground='green')
        self.style.configure('z.Emergency.TLabel', background=self.bg_color, foreground='green')
        self.style.configure('button.TButton', borderwidth=10, bordercolor='green', disabledbackground='red')
        self.style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)

        self.s_auth_button = ttk.Button(self.frame, image=self.spotify_logo, command=self.spotify_init,
                                        style='button.TButton')
        self.yt_auth_button = ttk.Button(self.frame, image=self.youtube_logo, command=self.youtube_init,
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
        self.yt_auth_button.place(height=110, width=110, relx=self.yt_auth_button_relx, rely=self.yt_auth_button_rely,
                                  anchor='center')

        self.logon_label = tk.Label(self.frame, text='Zaloguj się\nza pomocą przycisków obok', font='Calibri 13',
                                    bg=self.bg_color)
        self.logon_label.place(relx=0.5, rely=0.5, anchor='center')

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

    def check_buttons_state(self):
        if all(state == 'disabled' for state in (self.yt_auth_button['state'], self.s_auth_button['state'])):
            # self.logon_label.destroy()
            # self.tick_label = tk.label
            self.logon_label.config(image=self.tick_image, width=75, height=75)
            self.after(1000, self.logon_label.destroy)

    def spotify_init(self):

        def authenticate_response(response_link):
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
                self.update()
                auth_window.after(2500, lambda: quit_and_destroy(auth_window))

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
                self.style.configure('s.TLabel', font='Arial 10')
                text = ttk.Label(top_frame,
                                 text='Zaloguj się za pomocą przycisku poniżej, a następnie wklej adres linku z koteczkiem',
                                 justify='center', style='s.TLabel')
                text.pack(pady=15)
                self.style.configure('spotify.TButton', font='Calibri 13')
                link_button = ttk.Button(top_frame, text='Link', style='spotify.TButton',
                                         command=lambda: open_link(auth_link))
                link_button.pack(pady=5)
                entry = ttk.Entry(bottom_frame)
                entry.place(relwidth=0.7, relx=0.5, y=40, anchor='center')
                # text.bind('<Button-1>', lambda x: open_link(auth_link))
                self.style.configure('x.TButton', font='Calibri 13 bold')
                submit_button = ttk.Button(bottom_frame, text='Loguj mnie!', style='x.TButton',
                                           command=lambda: authenticate_response(entry.get()))  # ✔
                submit_button.place(width=80, height=40, relx=0.5, y=75, anchor='center')
                auth_window.focus_set()
                auth_window.mainloop()
                print('elo')
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
        s_auth_label = ttk.Label(self.frame, text='Poprawnie zalogowano w spotify!',
                                 style='w.Emergency.def.TLabel', justify='center')
        s_auth_label.place(relx=self.s_auth_button_relx, rely=self.s_auth_button_rely + .43, anchor='center')
        self.update()
        time.sleep(1)
        self.s_auth_button = tk.Button(self.frame, image=self.spotify_logo,
                                       background=self.bg_color, state='disabled')
        self.s_auth_button.place(self.s_auth_button_kwargs)
        # self.s_auth_button.config(background=self.bg_color)
        self.s_auth_button.config(state='disabled')
        s_auth_label.config(text=get_logged_at_text(self.spotify.get_user_name()), style='z.Emergency.TLabel')
        self.check_buttons_state()

    def youtube_init(self):
        def inner():
            self.yt_auth_button = tk.Button(self.frame, image=self.youtube_logo,
                                            background=self.bg_color, state='disabled')
            self.yt_auth_button.place(self.yt_auth_button_kwargs)
            yt_auth_label.config(text=get_logged_at_text(self.youtube.get_user_name()), style='z.Emergency.TLabel')
            self.check_buttons_state()

        try:
            self.youtube = youtube.YoutubeAPI()
        except ServerNotFoundError:
            show_connection_error()
            return
        yt_auth_label = ttk.Label(self.frame, text='Poprawnie zalogowano w youtube!',
                                  style='w.Emergency.def.TLabel', justify='center')
        yt_auth_label.place(relx=self.yt_auth_button_relx, rely=self.yt_auth_button_rely + .43, anchor='center')
        # yt_auth_label.after_idle(yt_auth_label.config(style='z.Emergency.TLabel'))
        self.update()
        time.sleep(1)
        inner()
        # self.after(1000, inner())

        # self.after(1000, yt_auth_label.config(style='z.Emergency.TLabel'))


def get_logged_at_text(str) -> str:
    logged = 'Zalogowana' if str.split()[0][-1] == 'a' else 'Zalogowany'
    return f'{logged}:\n{str}'


def show_connection_error():
    tk.messagebox.showerror('Błąd połączenia', 'Sprawdź połączenie sieciowe i spróbuj ponownie')


if __name__ == '__main__':
    gui = GUI()

    # root = tk.Tk()
    # root.title('test')
    # root.wm_minsize(width=700, height=500)
    # spotify_logo = tk.PhotoImage(file='images/spotify_icon.png')
    # img_label = tk.Label(image=spotify_logo)
    # img_label.pack(pady=20)
    # tk.mainloop()
