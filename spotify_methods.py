"""This file contains all the spotipy methods we will use in this project"""
import datetime
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import song_graph

G_TO_PROPS = song_graph.load_genres('Data/data_by_genres.csv')

# User Data
MY_ID = '1b85b05bab6a4880b0918b422db19fea'
SECRET_ID = '46a2286d8dbb4d1db0e89ce4315e3d0d'
USERNAME = '772iyi0qo383twmj0wecb2wap'
CRED_MGR = SpotifyClientCredentials(client_id=MY_ID, client_secret=SECRET_ID)
# Authorization Token
SCOPE = 'playlist-modify-public'
REDIRECT_URL = 'http://localhost:8080'
AUTH = SpotifyOAuth(client_id=MY_ID, client_secret=SECRET_ID, redirect_uri=REDIRECT_URL,
                    scope=SCOPE, username=USERNAME)
SP = spotipy.Spotify(client_credentials_manager=CRED_MGR, auth_manager=AUTH)


def spot_song_to_vert(song_data: dict, graph: song_graph.GenreGraph, all_songs: dict) \
        -> song_graph.Song:
    """This method converts a song into a Song vertex"""
    if song_data['id'] in all_songs:  # return existing vertex
        return graph.genres[all_songs[song_data['id']]].song_graph.songs[song_data['id']]

    name = song_data['name']
    date_list = list(map(int, song_data['album']['release_date'].split('-')))
    if len(date_list) >= 3:
        date = datetime.datetime(year=date_list[0], month=date_list[1], day=date_list[2])
    elif len(date_list) == 2:
        date = datetime.datetime(year=date_list[0], month=date_list[1], day=1)
    elif len(date_list) == 1:
        date = datetime.datetime(year=date_list[0], month=1, day=1)
    else:  # should never happen
        date = datetime.datetime(1699, 6, 9)
    information = {'artists': [person['name'] for person in song_data['artists']],
                   'duration': song_data['duration_ms'],
                   'explicit': song_data['explicit'], 'id': song_data['id'], 'name': name,
                   'release_date': date,
                   'year': date.year,
                   'popularity': song_data['popularity']}
    audio_info = SP.audio_features(information['id'])[0]
    properties = {'acousticness': audio_info['acousticness'],
                  'danceability': audio_info['danceability'],
                  'energy': audio_info['energy'],
                  'instrumentalness': audio_info['instrumentalness'],
                  'key': audio_info['key'],
                  'mode': audio_info['mode'],
                  'liveness': audio_info['liveness'],
                  'loudness': audio_info['loudness'],
                  'speechiness': audio_info['speechiness'],
                  'tempo': audio_info['tempo'],
                  'valence': audio_info['valence']}
    new_song = song_graph.Song(information=information, properties=properties, name=name)
    genre = song_to_genre_guess(new_song)
    if genre == 'None Found':
        genre = song_graph.song_to_genre(new_song, song_graph.GENRES,
                                         song_graph.load_genres(song_graph.GENRE_DATA))
    new_song.genre = genre
    return new_song


def find_track_options(song_name: str, graph: song_graph.GenreGraph,
                       all_songs: dict, artist: str = None) -> list[song_graph.Song]:
    """This method retrieves search results for a given song search query.
    Returns the name, artist, and track ID

    For example: Searching for "Deutschland" by "Rammstein" will return all songs related
    to 'Deutschland' and/or 'Rammstein', and order them on relevancy. Spotipy does this
    implicitly.
    """
    data_returned = SP.search(q=song_name + '+' + artist, type='track')
    if data_returned['tracks']['items'] == []:  # search returned nothing
        return []
    songs = []
    for song in data_returned['tracks']['items']:
        # print(song['name'])
        songs.append(spot_song_to_vert(song, graph, all_songs))
    return songs


def pull_playlist(playlist_name: str, graph: song_graph.GenreGraph, all_songs: dict) \
        -> list[song_graph.Song]:
    """Returns list of tracks corresponding to a user's playlist. This is used
    for loading a whole playlist into the user's interface."""
    all_playlists = SP.user_playlists(user=USERNAME)
    playlist = None
    for item in all_playlists['items']:
        if item['name'] == playlist_name:
            playlist = item
            break
    if playlist is None:
        return []
    track_data = SP.user_playlist_tracks(user=USERNAME, playlist_id=playlist['id'])
    return_data = []
    for song in track_data['items']:
        return_data.append(spot_song_to_vert(song['track'], graph, all_songs))
    return return_data


def get_playlist_id(name: str, playlists: list) -> Optional[str]:
    """Gets a playlist id from user's playlists"""
    for playlist in playlists:
        if playlist['name'] == name:
            return playlist['id']
    return None


def generate_playlist(playlist_name: str, tracks: list[str]) -> None:
    """This method generates a playlist for the user"""

    # check if playlist exists:
    my_playlists = SP.user_playlists(USERNAME)
    playlist_id = get_playlist_id(playlist_name, my_playlists['items'])
    if playlist_id is None:  # playlist doesn't exist so create it
        SP.user_playlist_create(USERNAME, playlist_name)
        # update playlist_id
        my_playlists = SP.user_playlists(USERNAME)
        playlist_id = get_playlist_id(playlist_name, my_playlists['items'])

    # make the playlist
    SP.user_playlist_add_tracks(user=USERNAME, playlist_id=playlist_id, tracks=tracks)


def song_to_genre_guess(song: song_graph.Song) -> str:
    """
    Returns the likely genre of a song
    """

    artist = song.information['artists'][0]

    if artist == 'n/a':
        artist = song.information['artists'][1]

    data = SP.search(q=artist, limit=1, type='artist')
    # Based on the formatting of how spotify returns data:
    genres = data['artists']['items'][0]['genres']

    # Normalize these properties so they are ~ [0, 1] as the other properties
    loudness_range = 59
    key_range = 10
    tempo_mod = 145

    # Note that the maximum difference between songs cannot be greater than 15 so this is fine
    min_difference = 999999
    curr_difference = 0

    closest_genre = ''

    for genre in genres:
        if genre in G_TO_PROPS:
            average_props = G_TO_PROPS[genre]

            for prop in average_props:
                if prop == 'tempo':
                    curr_difference += abs(song.properties[prop]
                                           - G_TO_PROPS[genre][prop]) / tempo_mod
                elif prop == 'loudness':
                    curr_difference += abs(song.properties[prop]
                                           - G_TO_PROPS[genre][prop]) / loudness_range
                elif prop == 'key':
                    curr_difference += abs(song.properties[prop]
                                           - G_TO_PROPS[genre][prop]) / key_range
                elif prop not in ['popularity', 'duration_ms']:
                    curr_difference += abs(song.properties[prop]
                                           - G_TO_PROPS[genre][prop])

            if curr_difference < min_difference:
                closest_genre = genre
                min_difference = curr_difference

            curr_difference = 0

    if closest_genre == '':
        return 'None Found'
    else:
        return closest_genre


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
