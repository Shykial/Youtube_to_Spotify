import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from httplib2 import ServerNotFoundError
from requests import ConnectionError
import spotify
import youtube
import time



class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.wm_minsize(width=700, height=500)
        self.title('Youtube to Spotify')
        self.spotify = None
        self.youtube = None
        self.bg_color = '#03333F'
        # dimension
        self.frame = tk.Frame(self, borderwidth=12, bg=self.bg_color)
        self.frame.place(relheight=0.4, relwidth=1)
        # spotify_logo = ImageTk.PhotoImage(Image.open('images/spotify_icon.png'))
        self.spotify_logo = ImageTk.PhotoImage(Image.open('images/spotify_icon.png'))
        # self.spotify_logo = tk.PhotoImage(file='images/spotify_icon.png')
        self.spotify_logo_greyed = tk.PhotoImage(file='images/spotify_icon_greyed.png')
        self.youtube_logo = tk.PhotoImage(file='images/youtube_icon.png')
        self.style = ttk.Style()
        # s_label = ttk.Label(frame, image=spotify_logo)
        # s_label.image = spotify_logo
        # s_label.pack()
        self.style.configure('TLabel', font='Calibri 12', foreground='black', background='white')
        self.style.configure('w.Emergency.TLabel', foreground='green')
        self.style.configure('z.Emergency.TLabel', background=self.bg_color, foreground='green')
        self.style.configure('button.TButton', borderwidth=10, bordercolor='green', disabledbackground='red')
        self.style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)
        self.s_auth_button = ttk.Button(self.frame, image=self.spotify_logo, command=self.spotify_init,
                                        style='button.TButton')
        # self.s_auth_button = tk.Button(frame, image=self.spotify_logo, command=self.spotify_init)
        # s_auth_button = tk.Button(frame, image=spotify_logo, command=self.spotify_init, borderwidth=0, background=bg_color)
        # self.s_auth_button = tk.Button(frame, image=spotify_logo, command=self.spotify_init, borderwidth=0)
        self.yt_auth_button = ttk.Button(self.frame, image=self.youtube_logo, command=self.youtube_init,
                                         style='button2.TButton')
        self.s_auth_button.place(height=110, width=110, relx=0.75, rely=0.5, anchor='center')
        self.yt_auth_button.place(height=110, width=110, relx=0.25, rely=0.5, anchor='center')

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

    def spotify_init(self):
        try:
            self.spotify = spotify.SpotifyAPI()
        except ConnectionError:
            self.show_connection_error()
            return
        # style = ttk.Style()
        # style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)
        # style.configure('button2.Tbutton', borderwidth=0, background=self.bg_color)
        # self.s_auth_button.config(state='disabled', style='button2.TButton')
        s_auth_label = ttk.Label(self.frame, text='Poprawnie zalogowano w spotify!', style='w.Emergency.def.TLabel')
        s_auth_label.place(relx=0.75, rely=0.92, anchor='center')
        self.update()
        time.sleep(1)
        self.s_auth_button = tk.Button(self.frame, image=self.spotify_logo,
                                       background=self.bg_color, state='disabled')
        self.s_auth_button.place(height=110, width=110, relx=0.75, rely=0.5, anchor='center')
        # self.s_auth_button.config(background=self.bg_color)
        self.s_auth_button.config(state='disabled')
        s_auth_label.config(style='z.Emergency.TLabel')

    def youtube_init(self):
        try:
            self.youtube = youtube.YoutubeAPI()
        except ServerNotFoundError:
            self.show_connection_error()
            return
        yt_auth_label = ttk.Label(self.frame, text='Poprawnie zalogowano w youtube!', style='w.Emergency.def.TLabel')
        yt_auth_label.place(relx=0.25, rely=0.92, anchor='center')
        # yt_auth_label.after_idle(yt_auth_label.config(style='z.Emergency.TLabel'))
        self.update()
        time.sleep(1)
        # self.after(1000, yt_auth_label.config(style='z.Emergency.TLabel'))
        self.yt_auth_button = tk.Button(self.frame, image=self.youtube_logo,
                                        background=self.bg_color, state='disabled')
        self.yt_auth_button.place(height=110, width=110, relx=0.25, rely=0.5, anchor='center')
        yt_auth_label.config(style='z.Emergency.TLabel')

    def show_connection_error(self):
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
