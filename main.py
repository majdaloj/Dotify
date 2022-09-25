"""This runs the GUI for our project"""
import tkinter as tk
import random
import spotify_methods
import computations
import song_graph
import pygame_visualization

###################################
#      FUNCTIONAL DEFINITIONS
###################################


def make_playlist(playlist: list, preferences: dict,
                  graph: song_graph.GenreGraph, all_songs: dict) -> list[song_graph.Song]:
    """This method generates you a new playlist!

    The song vertices currently stored aren't in the graph, they just represent the vertex. Now
    this song MAY have a vertex representation already in the graph or may not, so we need to
    first decide if we need ot add this new vertex in as a new vertex, or use the existing one!

    Then, computations.py handles the playlist generation depending on the mode selected"""
    # print("Making Playlist...")
    song_verts = []
    for song in playlist:
        if not song.information['id'] in all_songs:
            graph.insert_song(song)
            all_songs[song.information['id']] = song.genre
        song_verts.append(graph.get_song(song))
    new_playlist = []
    if song_verts != []:
        if preferences['gen_mode'] == 'level gen':
            new_playlist = computations.bfs_gen(graph, song_verts, 2)
        elif preferences['gen_mode'] == 'custom gen':
            new_playlist = computations.par_gen(graph, song_verts, 2, preferences)
        elif preferences['gen_mode'] == 'artist pref':
            new_playlist = computations.artist_gen(graph, song_verts)
        elif preferences['gen_mode'] == 'new genre':
            if preferences['bias'] is not None:
                new_playlist = computations.explore_new_genres(graph, song_verts,
                                                               preferences['bias'],
                                                               preferences)
        elif preferences['gen_mode'] == 'unique songs':
            new_playlist = computations.find_uniquely_connected(graph, song_verts, preferences)
        elif preferences['gen_mode'] == 'recent songs':
            new_playlist = computations.get_new_songs(graph, song_verts)
        else:
            new_playlist = []

    playname_id = list(range(10))
    random.shuffle(playname_id)
    play_name = preferences['gen_mode'] + " " + "".join([str(x) for x in playname_id])
    if new_playlist == []:
        print('Playlist FAILED, check the input')
        return []

    spotify_methods.generate_playlist(play_name,
                                      [vert.information['id'] for vert in new_playlist])
    print('Playlist Made, Check your Spotify Account! \n \n Playlist Name: ' + str(play_name))
    return new_playlist


###################################
#         EVENT METHODS
###################################
def search_song(fields: tuple[tk.Entry, tk.Entry],
                search_res: tk.Listbox, current_result: list,
                graph: song_graph.GenreGraph, all_songs: dict) -> None:
    """Searches for a song and updates results list. This method calls the
    spotipy_methods.find_track_options and loads the results into a list"""
    song_name = fields[0].get()
    artist_name = fields[1].get()
    if song_name is not None:
        search_results = spotify_methods.find_track_options(song_name, graph,
                                                            all_songs, artist_name)
        current_result.clear()
        search_res.delete(0, search_res.size())
        if len(search_results) > 0:  # found a song
            for i in range(len(search_results)):
                search_res.insert(i, search_results[i].name + ' by '
                                  + search_results[i].information['artists'][0])
                current_result.append(search_results[i])


def add_song(search_res: tk.Listbox,
             playlist_res: tk.Listbox, current_results: list, playlist: list) -> None:
    """This method adds a song to the playlist data and listview. Given a
    selected song from the search results list, you can add the selected song
    to your song list."""
    cur_selection = search_res.curselection()
    if len(cur_selection) == 0:  # nothing selected
        pass
    else:
        selected_index = cur_selection[0]
        selected_song = current_results[selected_index]
        playlist_res.insert('end', selected_song.name + " by "
                            + selected_song.information['artists'][0])
        playlist.append(selected_song)


def rem_song(playlist_res: tk.Listbox, playlist: list) -> None:
    """Removes a song from playlist data and listview. Given a
    selected song from the song list, you can remove the selected song
    sed list."""
    cur_selection = playlist_res.curselection()
    if len(cur_selection) == 0:  # nothing selected
        pass
    else:
        selected_index = cur_selection[0]
        playlist.pop(selected_index)
        playlist_res.delete(selected_index, selected_index)


def pull_playlist(name_entry: tk.Entry, playlist_res: tk.Listbox, playlist: list,
                  graph: song_graph.GenreGraph, all_songs: dict) -> None:
    """Pulls a playlist from tethered account. You can load a whole playlist into the song
    list. This function is for ease of the user."""
    name = name_entry.get()
    if name is None:
        # Error Message
        return
    else:
        track_list = spotify_methods.pull_playlist(name, graph, all_songs)
        if track_list == []:
            return
        for i in range(len(track_list)):
            playlist_res.insert('end', track_list[i].name + ' by '
                                + track_list[i].information['artists'][0])
            playlist.append(track_list[i])


def clear(playlist_res: tk.Listbox, playlist: list) -> None:
    """Clears songs list"""
    playlist.clear()
    playlist_res.delete(0, playlist_res.size())


def visualize(graph: song_graph.GenreGraph) -> None:
    """This method visualizes the given graph"""
    pygame_visualization.run(graph)


def open_pref(preferences: dict) -> None:
    """This method loads the user preferences window. It is triggered by clicking
    'settings' """
    settings_window = tk.Tk(screenName='Settings Window')
    settings_window.config(background=BG_BLACK)
    settings_window.geometry(str(SET_WIN_WIDTH) + 'x' + str(SET_WIN_HEIGHT))

    ###################################
    #           GUI METHODS
    ###################################
    def update_prefs(preferences: dict) -> None:
        """This function updates the user's preferences!"""
        for item in sliders:
            preferences[item] = int(sliders[item].get())
        preferences['gen_mode'] = choice_var.get()
        if len(bias_field.get()) > 0:
            preferences['bias'] = float(bias_field.get())
        else:
            preferences['bias'] = None

    ###################################
    #         GUI ELEMENTS
    ###################################
    settings_header = tk.Label(master=settings_window, text="Preferences",
                               background=HEADER_COL)
    settings_header.config(font=("System", 9), width=40)
    settings_header.place(relx=0.5, rely=0.02, anchor='n')

    sliders = {}
    keys = list(preferences.keys())
    for i in range(6):  # nifty loop to load and store the sliders locally
        new_slider = tk.Scale(master=settings_window, label=keys[i], from_=0, to=100,
                              orient=tk.HORIZONTAL)

        new_slider.place(relx=0.25 + (i % 2) * 0.48,
                         rely=0.17 + (i // 2) * 0.19,
                         anchor='center')
        new_slider.set(preferences[keys[i]])
        sliders[keys[i]] = new_slider

    gen_choices = {'level gen', 'custom gen', 'artist pref',
                   'new genre', 'unique songs', 'recent songs'}
    choice_var = tk.StringVar(settings_window)
    choice_var.set(preferences['gen_mode'])

    choice_label = tk.Label(settings_window, text="Generation Mode",
                            background=HEADER_COL)
    choice_label.config(font=("System", 9), width=20)
    choice_label.place(relx=0.5, rely=0.67, anchor='n')

    choice_menu = tk.OptionMenu(settings_window, choice_var, *gen_choices)
    choice_menu.place(relx=0.5, rely=0.77, anchor='center')

    bias_label = tk.Label(settings_window, text="Bias (new genre only) 0 to 1",
                          background=HEADER_COL)
    bias_label.config(font=("System", 5), width=25)
    bias_label.place(relx=0.5, rely=0.81, anchor='n')

    bias_field = tk.Entry(master=settings_window, width=10)
    bias_field.config(font=("System", 9))
    bias_field.place(relx=0.5, rely=0.89, anchor='center')

    apply_button = tk.Button(master=settings_window, text='Apply',
                             command=lambda: update_prefs(preferences),
                             background=HEADER_COL)
    apply_button.config(font=('System', 9), width=7)
    apply_button.place(relx=0.5, rely=0.99, anchor='s')

    settings_window.mainloop()


###################################
#       GUI DEFINITIONS
###################################
WIN_WIDTH, WIN_HEIGHT = 375, 575
SET_WIN_WIDTH, SET_WIN_HEIGHT = 300, 465
HEADER_COL = "#1DB954"  # <- spotify green
SEC1_COL = "#5ca2b8"  # 94ba5f" <- old green
SEC2_COL = "#ac76cc"
WHITE = "#FFFFFF"
BG_BLACK = '#191414'
SPOT_GREY = '#7c7c7c'


def get_window() -> tk.Tk:
    """This function creates the GUI window and returns it"""
    window = tk.Tk(screenName='Thank you Evan Kanter for a terrific semester!')
    window.config(background=BG_BLACK)
    window.geometry(str(WIN_WIDTH) + 'x' + str(WIN_HEIGHT))

    return window


def set_song_header(window: tk.Tk) -> tk.Label:
    """This is a header method to put the song header"""
    song_header = tk.Label(master=window, text="Songs", background=HEADER_COL)
    song_header.config(font=("System", 9), width=40)
    song_header.place(relx=0.5, rely=0.02, anchor='n')

    return song_header


def set_vis_btn(window: tk.Tk, graph: song_graph.GenreGraph) -> None:
    """This is a header method to set the visualization button"""
    vis_btn = tk.Button(master=window, text='Visualize',
                        command=lambda: visualize(graph=graph))
    vis_btn.config(font=('System', 9), width=7)
    vis_btn.place(relx=0.85, rely=0.06, anchor='s')


def set_playlist_res(window: tk.Tk) -> tk.Listbox:
    """This is a header to set the playlist listbox on the GUI"""
    playlist_res = tk.Listbox(master=window, width=40, height=14)
    playlist_res.config(background=WHITE)
    playlist_res.place(relx=0.5, rely=0.28, anchor='center')
    return playlist_res


def set_song_entry_header(window: tk.Tk) -> tk.Label:
    """This is a header to set the song entry item on the GUI"""
    song_entry_header = tk.Label(master=window, text="Song:", background=SEC1_COL)
    song_entry_header.config(font=("System", 9))
    song_entry_header.place(relx=0.25, rely=0.49, anchor='n')
    return song_entry_header


def set_song_field(window: tk.Tk) -> tk.Entry:
    """This method is a header to set the song entry item on the GUI"""
    song_field = tk.Entry(master=window, width=20)
    song_field.config(font=("System", 9))
    song_field.place(relx=0.62, rely=0.51, anchor='center')
    return song_field


def set_art_entry_header(window: tk.Tk) -> tk.Label:
    """This is a header method to set the artist entry title item on the GUI"""
    art_entry_header = tk.Label(master=window, text="Artist:", background=SEC1_COL)
    art_entry_header.config(font=("System", 9))
    art_entry_header.place(relx=0.25, rely=0.54, anchor='n')
    return art_entry_header


def set_art_field(window: tk.Tk) -> tk.Entry:
    """This is a header method to set the artist entry item on the GUI"""
    art_field = tk.Entry(master=window, width=20)
    art_field.config(font=("System", 9))
    art_field.place(relx=0.62, rely=0.56, anchor='center')
    return art_field


def set_search_btn(window: tk.Tk, fields: tuple[tk.Entry, tk.Entry],
                   search_elements: tuple[tk.Listbox, list],
                   graph: song_graph.GenreGraph, all_songs: dict) -> None:
    """This is a header method to set the search button on the GUI"""
    search_btn = tk.Button(master=window, text='Search',
                           command=lambda: search_song(fields=(fields[0], fields[1]),
                                                       search_res=search_elements[0],
                                                       current_result=search_elements[1],
                                                       graph=graph,
                                                       all_songs=all_songs),
                           background=SEC1_COL)
    search_btn.config(font=('System', 9), width=7)
    search_btn.place(relx=0.5, rely=0.64, anchor='s')


def set_search_res(window: tk.Tk) -> tk.Listbox:
    """This method sets the search result listbox on the GUI"""
    search_res = tk.Listbox(master=window, width=40, height=3)
    search_res.config(font=("System", 9), background=WHITE)
    search_res.place(relx=0.5, rely=0.74, anchor='s')
    return search_res


def set_load_play_header(window: tk.Tk) -> tk.Label:
    """This method sets the load playlist title on the GUI"""
    load_play_header = tk.Label(master=window, text="Load Playlist", background=SEC2_COL)
    load_play_header.config(font=("System", 9), width=40)
    load_play_header.place(relx=0.5, rely=0.79, anchor='s')
    return load_play_header


def set_name_entry(window: tk.Tk) -> tk.Entry:
    """This method sets the playlist name entry on the GUI"""
    name_entry = tk.Entry(master=window, width=22)
    name_entry.config(font=("System", 9))
    name_entry.place(relx=0.5, rely=0.83, anchor='center')
    return name_entry


def set_settings_btn(window: tk.Tk, preferences: dict) -> None:
    """This is a method to set the settings button on the GUI"""
    settings_btn = tk.Button(master=window, text='Settings',
                             command=lambda: open_pref(preferences=preferences))
    settings_btn.config(font=('System', 9), width=7)
    settings_btn.place(relx=0.5, rely=0.92, anchor='s')


def set_clear_btn(window: tk.Tk, playlist_res: tk.Listbox, playlist: list) -> None:
    """This method sets the clear button on the GUI"""
    clear_btn = tk.Button(master=window, text='Clear',
                          command=lambda: clear(playlist_res, playlist))
    clear_btn.config(font=('System', 9), width=10)
    clear_btn.place(relx=0.8, rely=0.92, anchor='s')


def set_add_play(window: tk.Tk, name_entry: tk.Entry,
                 playlist_elements: tuple[tk.Listbox, list],
                 graph: song_graph.GenreGraph, all_songs: dict) -> None:
    """This method sets the add playlist button on the GUI"""
    add_play = tk.Button(master=window, text='Add Playlist',
                         command=lambda:
                         pull_playlist(name_entry,
                                       playlist_elements[0], playlist=playlist_elements[1],
                                       graph=graph, all_songs=all_songs))
    add_play.config(font=('System', 9), width=10)
    add_play.place(relx=0.2, rely=0.92, anchor='s')


def set_add_song(window: tk.Tk, search_res: tk.Listbox, playlist_res: tk.Listbox,
                 current_results: list, playlist: list) -> None:
    """This method sets the add song button on the GUI"""
    add_song_btn = tk.Button(master=window, text='Add Song',
                             command=lambda:
                             add_song(search_res, playlist_res, current_results, playlist))
    add_song_btn.config(font=('System', 9), width=9)
    add_song_btn.place(relx=0.2, rely=0.98, anchor='s')


def set_start_btn(window: tk.Tk, playlist: list, preferences: dict, graph: song_graph.GenreGraph,
                  all_songs: dict) -> None:
    """This method sets the start button on the GUI"""
    start_btn = tk.Button(master=window, text='START!',
                          command=lambda: make_playlist(playlist, preferences, graph,
                                                        all_songs))
    start_btn.config(font=('System', 9), width=7)
    start_btn.place(relx=0.5, rely=0.98, anchor='s')


def set_rem_btn(window: tk.Tk, playlist_res: tk.Listbox, playlist: list) -> None:
    """This method sets the remove button on the GUI"""
    rem_btn = tk.Button(master=window, text='Remove',
                        command=lambda: rem_song(playlist_res, playlist))

    rem_btn.config(font=('System', 9), width=9)
    rem_btn.place(relx=0.8, rely=0.98, anchor='s')


def open_tk() -> None:
    """This method starts the GUI"""
    thresh = float(input("Enter the threshold you would like to work with: "))
    print("Starting Sofware with a threshold of " + str(thresh))
    playlist = []  # song list
    preferences = {'acousticness': 0,  # user preferences
                   'danceability': 0,
                   'energy': 0,
                   'instrumentalness': 0,
                   'key': 0,
                   'liveness': 0,
                   'gen_mode': 'new genre',
                   'bias': 0}
    current_result = []
    graph, all_songs = song_graph.create_genre_graph('Data/data.csv', 'Data/data_w_genres.csv',
                                                     'Data/data_by_genres.csv', thresh)

    window = get_window()
    set_song_header(window)
    set_vis_btn(window, graph=graph)
    playlist_res = set_playlist_res(window)
    set_song_entry_header(window)
    song_field = set_song_field(window)
    set_art_entry_header(window)
    art_field = set_art_field(window)
    search_res = set_search_res(window)
    set_search_btn(window, fields=(song_field, art_field),
                   search_elements=(search_res, current_result), graph=graph, all_songs=all_songs)
    set_load_play_header(window)
    name_entry = set_name_entry(window)
    set_settings_btn(window, preferences=preferences)
    set_clear_btn(window, playlist_res=playlist_res, playlist=playlist)

    set_add_play(window, name_entry=name_entry, playlist_elements=(playlist_res, playlist),
                 graph=graph, all_songs=all_songs)
    set_add_song(window, playlist_res=playlist_res, search_res=search_res,
                 current_results=current_result, playlist=playlist)
    set_start_btn(window, playlist, preferences, graph, all_songs)
    set_rem_btn(window, playlist_res=playlist_res, playlist=playlist)
    window.mainloop()


open_tk()

# if __name__ == '__main__':
#     import python_ta.contracts
#     python_ta.contracts.check_all_contracts()
#
#     import doctest
#     doctest.testmod()
#
#     import python_ta
#     python_ta.check_all(config={
#         'max-line-length': 100,
#         'disable': ['E1136'],
#         'extra-imports': ['pygame', 'networkx', 'pygame_visualization', 'song_graph',
#                           'computations', 'tkinter', 'spotify_methods', 'random', 'main',
#                           'spotipy', 'spotipy.oauth2', 'main', 'graph_visualization', 'datetime',
#                           'csv', 'plotly.graph_objects'],
#         'generated-members': ['pygame.*'],
#         'max-nested-blocks': 4,
#         'allowed-io': ['genres_to_songs', 'load_genres', 'load_artists_to_genres', 'load_songs',
#                        'open_tk', 'make_playlist']
#     })
