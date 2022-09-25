"""Graph computations"""
import collections
import math
import random
import datetime
from typing import Union, Optional
import song_graph

WEIGHTS = {'acousticness': 1, 'danceability': 1, 'energy': 1, 'instrumentalness': 1, 'key': 1 / 9,
           'mode': 1, 'liveness': 1, 'loudness': 1 / 59, 'speechiness': 1, 'tempo': 1 / 145,
           'valence': 1}


def par_rating(song: song_graph.Song, weights: dict) -> float:
    """Based on user preferences, this function returns a weighted score on a song for the user"""
    rating = 0
    for key in weights:
        if list(weights.keys()).index(key) <= 5:
            rating += (weights[key] / 100) * song.properties[key]
    return rating


def sim_par_rating(song: song_graph.Song, other_id: str, pref_weights: dict) -> float:
    """This is a helper function. It uses similarity score and parameter score to calculate
    a rating of similarity for a song"""
    sim_score = song.neighbours[other_id]
    par_score = par_rating(song, pref_weights)
    ret_score = sim_score
    if par_score != 0:
        ret_score += 1 / par_score
    return ret_score


def bfs_gen(graph: song_graph.GenreGraph, song_list: list[song_graph.Song],
            n: int) -> list[song_graph.Song]:
    """This function uses a level-based generation technique to generate songs.

    The algorithm does the following PER base_song in song_list:
        1) initialize a queue with just base_song
        2) while the queue isn't empty, pop the leftmost vertex
            a) sort its neighbours
            b) add its neighbours in order of sorted (best in first, worst in last)
        3) repeat until song_per is reached (new songs needed per base_song)

    This is similar to breadth first search, in the manner that it goes down one level at a time
    rather then recursively down one pathway (hence the name bfs)"""
    visited = set.union({song.name for song in song_list},
                        {song.information['id'] for song in song_list})
    ret = []
    for base_song in song_list:
        songs_so_far = 0
        q = collections.deque()
        q.append(base_song)
        sg = graph.genres[base_song.genre].song_graph
        while len(q) > 0:
            popped = q.popleft()
            if songs_so_far < n and popped.name not in visited \
                    and popped.information['id'] not in visited:
                ret.append(popped)
                songs_so_far += 1
            visited.add(popped.name)
            visited.add(popped.information['id'])
            nodes_to_add = []
            for thing in popped.neighbours:
                if sg.songs[thing].name and thing not in visited:
                    nodes_to_add.append((sg.songs[thing], popped.neighbours[thing]))
            nodes_to_add = list(sorted(nodes_to_add, key=lambda x: x[1]))
            for el in nodes_to_add:
                q.append(el[0])

            if songs_so_far >= n:
                break

    return ret


def par_gen(graph: song_graph.GenreGraph, song_list: list[song_graph.Song],
            n: int, parameters: dict) -> list[song_graph.Song]:
    """This generation method uses parameter weight to generate songs. It tailors more
    to the user's preferences."""
    ret_playlist = []
    visited = set.union({song.name for song in song_list},
                        {song.information['id'] for song in song_list})
    for base_song in song_list:
        song_g = graph.genres[base_song.genre].song_graph
        base_neighbours_w_scores = []
        for song_id in base_song.neighbours:
            if song_g.songs[song_id].name not in visited and song_id not in visited:
                par_score = par_rating(song_g.songs[song_id], parameters)
                base_neighbours_w_scores.append((song_id, par_score))
        base_neighbours_w_scores = sorted(base_neighbours_w_scores, key=lambda x: x[1])
        c = 0
        for i in range(len(base_neighbours_w_scores)):
            if c == n:
                break
            if base_neighbours_w_scores[i][0] not in visited \
                    and song_g.songs[base_neighbours_w_scores[i][0]].name not in visited:
                ret_playlist.append(song_g.songs[base_neighbours_w_scores[i][0]])
                visited.add(song_g.songs[base_neighbours_w_scores[i][0]].name)
                visited.add(base_neighbours_w_scores[i][0])
                c += 1

    return ret_playlist


def artist_gen(graph: song_graph.GenreGraph, song_list: list[song_graph.Song]) \
        -> list[song_graph.Song]:
    """This method uses recursion to generate songs, and involves the artist to make optimal
    recommendations. """
    ret = []
    visited = set.union({base_song.name for base_song in song_list},
                        {base_song.information['id'] for base_song in song_list})
    for song in song_list:
        sg = graph.genres[song.genre].song_graph
        returned = rec(sg, song, visited, song.information['artists'], 0)
        if returned is not None:
            ret.append(returned)
            visited.add(returned.name)
            visited.add(returned.information['id'])
    return ret


def rec(graph: song_graph.SongGraph, song: song_graph.Song, visited: set,
        artists: list, depth: int) -> Optional[song_graph.Song]:
    """This function is the RECURSIVE step that takes in a song and traverses the graph
    to return one with the same artists"""
    if depth == 250:
        return song

    if song.name not in visited and song.information['id'] not in visited:
        for art in song.information['artists']:
            if art in artists:
                return song
    visited.add(song.name)
    visited.add(song.information['id'])
    neighbours = [(graph.songs[n_id], song.neighbours[n_id]) for n_id in song.neighbours
                  if graph.songs[n_id].name not in visited and n_id not in visited]
    neighbours = list(sorted(neighbours, reverse=True, key=lambda x: x[1]))

    for tup in neighbours:
        returned = rec(graph, tup[0], visited, artists, depth + 1)
        if returned is not None:
            return returned
    return None


def explore_new_genres(graph: song_graph.GenreGraph, song_list: list[song_graph.Song],
                       bias: float, preferences: dict) -> list[song_graph.Song]:
    """
    Search method that returns a list of songs that can be biased to return new genres.
    bias is within range [0, 1], at 1 the method will return only songs that have a genre that
    are different to all genres of the songs in the input list, at 0 the method will just search
    as normal.

    Preconditions:
        - 0 <= bias <= 1
        - all([key in WEIGHTS for key in preferences])
        - all{[genre in graph.genres for genre in viable_genres]}
    """
    inputted_genres = set()
    inputted_genres_g = set()
    for song in song_list:
        if song.genre not in inputted_genres:
            inputted_genres.add(song.genre)
            inputted_genres_g.add(graph.genres[song.genre])

    genre_weights = []
    for genre in graph.genres:
        genre_weights.append((genre, get_genre_rating(graph.genres[genre], inputted_genres_g)))

    genre_weights.sort(key=lambda x: x[1])

    viable_genres = get_viable_genres(inputted_genres, genre_weights)
    viable_genres.extend(inputted_genres)
    songs_w_scores = get_songs_with_scores(viable_genres, song_list, graph, bias, preferences)
    songs_w_scores.sort(key=lambda x: x[1])

    temp_songs_w_scores = []
    for i in range(0, len(songs_w_scores) - 1):
        if songs_w_scores[i] != songs_w_scores[i + 1]:
            temp_songs_w_scores.append(songs_w_scores[i])

    songs_w_scores = temp_songs_w_scores

    if 11 > len(songs_w_scores):
        return [songs_w_scores[index][0] for index in range(0, len(songs_w_scores))]
    else:
        return [songs_w_scores[index][0] for index in range(0, 11)]


def get_viable_genres(inputted_genres: set, genre_weights: list) -> list:
    """
    Return a list of genres that are similar to the set of inputted_genres.
    """
    viable_genres = []
    spread = max(10 / len(inputted_genres), 1)
    for i in range(0, len(genre_weights)):
        if genre_weights[i][0] in inputted_genres:
            offset = 1
            while offset <= spread:
                if i - offset > 0 and genre_weights[i - offset][0] not in inputted_genres:
                    viable_genres.append(genre_weights[i - offset][0])
                elif len(genre_weights) > i + offset and \
                        genre_weights[i + offset][0] not in inputted_genres:
                    viable_genres.append(genre_weights[i + offset][0])

                offset += 1
    return viable_genres


def get_songs_with_scores(viable_genres: list, song_list: list, graph: song_graph.GenreGraph,
                          bias: float, preferences: dict) -> list:
    """
    Return a list of songs with their similarity scores from song_graphs that correspond to
    genres in viable genres

    Preconditions:
        - all{[genre in graph.genres for genre in viable_genres]}
        - 0 <= bias <= 1
        - all([key in WEIGHTS for key in preferences])

    """
    songs_w_scores = []
    for genre in viable_genres:
        curr_song_graph = graph.genres[genre].song_graph
        for song in curr_song_graph.songs:
            scores = set()
            for inputted_song in song_list:
                score = get_biased_sim_score(bias, preferences, curr_song_graph.songs[song],
                                             inputted_song)
                scores.add(score)
            songs_w_scores.append((curr_song_graph.songs[song], sum(scores) / len(scores)))

    return songs_w_scores


def get_biased_sim_score(bias: float, preferences: dict, song_1: song_graph.Song,
                         song_2: song_graph.Song) -> float:
    """
    Get the similarity score between two songs taking into account the bias for
    finding new genres. The higher the bias the better the similarity score for two songs
    from distinct genres.

    Preconditions:
        - 0 <= bias <= 1
        - all([key in WEIGHTS for key in preferences])
    """

    if song_1.genre == song_2.genre:
        sim_score = (bias + 1) * get_song_rating(song_1, song_2)
    else:
        sim_score = get_song_rating(song_1, song_2)

    par_score_1 = par_rating(song_1, preferences)
    par_score_2 = par_rating(song_2, preferences)
    ret_score = sim_score
    if par_score_1 != 0 and par_score_2 != 0:
        ret_score += 1 / abs((par_score_1 + par_score_2) / 2)
    return ret_score


def get_song_rating(song_1: song_graph.Song, song_2: Union[song_graph.Song, list]) -> float:
    """
    Return the rating of a song:

    The rating is calculated by: FILLER RATING FOR NOW
    Preconditions:
        - song.properties != {}
    """
    rating = 0
    for prop in song_1.properties:
        if not isinstance(song_2, list):
            rating += WEIGHTS[prop] * abs(song_1.properties[prop] - song_2.properties[prop])
        else:
            rating += WEIGHTS[prop] * abs(song_1.properties[prop]
                                          - sum([song.properties[prop]
                                                 for song in song_2]) / len(song_2))

    return rating


def get_genre_rating(genre: song_graph.Genre, genre_list: set) -> float:
    """
    Get the similarity of a genre to a list of genres. done by comparing the
    differences in each property. Smaller, the rating the better.

    Preconditions:
        - genre.average_properties != {}
    """
    rating = 0
    for prop in genre.average_properties:
        if prop in WEIGHTS:
            rating += WEIGHTS[prop] * abs(genre.average_properties[prop]
                                          - sum([genre_i.average_properties[prop]
                                                 for genre_i in genre_list]) / len(genre_list))

    return rating


def find_uniquely_connected(graph: song_graph.GenreGraph, song_list: list[song_graph.Song],
                            preferences: dict) -> list[song_graph.Song]:
    """
    Search method that returns songs that are uniquely connected to the input list. As in
    the songs that are similar to input song and similar to few other songs are the ones that
    are returned. Done by comparing degrees.

    Preconditions:
        - graph has all vertices and edges in it.
        - all([key in WEIGHTS for key in preferences])
    """
    returned_songs = []
    init_song_list = song_list.copy()
    while len(returned_songs) < 11:
        min_songs, min_song = [], []
        for song in song_list:
            degrees = []
            for neighbour in song.neighbours:
                if graph.genres[song.genre].song_graph.songs[neighbour] not in song_list and \
                        graph.genres[song.genre].song_graph.songs[neighbour] not in returned_songs:
                    degrees.append((graph.genres[song.genre].song_graph.songs[neighbour],
                                    graph.genres[song.genre].song_graph.songs[
                                        neighbour].get_degree()))

            if degrees != []:
                degrees.sort(key=lambda x: x[1])
                i = 0
                while i < len(degrees) - 1 and degrees[i] in min_songs:
                    i += 1
                min_song = degrees[i]
                min_songs.append((min_song[0], min_song[1], song))

        if min_songs != [] and min_song != []:
            scores = [(get_degree_sim_score(song_1=min_song_s[0], song_2=min_song_s[2],
                                            preferences=preferences, degree=min_song_s[1]),
                       min_song_s[0], min_song_s[2]) for min_song_s in min_songs]
            tuple_min = min(scores, key=lambda x: x[0])
            return_song = tuple_min[1]
            replaced_song = tuple_min[2]

            if return_song not in init_song_list and return_song not in returned_songs:
                returned_songs.append(return_song)

                song_list.remove(replaced_song)
                song_list.append(return_song)
            else:
                shuffle_songs(song_list, graph)

    if len(returned_songs) > 11:
        return returned_songs[0:11]
    else:
        return returned_songs


def shuffle_songs(song_list: list[song_graph.Song], graph: song_graph.GenreGraph) -> \
        None:
    """
    Shuffle the input song_list so that it contains new songs in similar genres.

    This is to prevent the search methods from going in an infinite loop if there aren't
    at least 11 songs to recommend.

    Preconditions:
        - graph has all vertices and edges in it.
    """
    for i in range(0, max(len(song_list) // 2, 1)):
        index_to_replace = random.randint(0, len(song_list) - 1)
        neighbours = graph.genres[song_list[i].genre].neighbours

        sim_genres = []
        for genre in list(neighbours):
            sim_genres.append((get_genre_rating(graph.genres[song_list[i].genre],
                                                {graph.genres[genre]}),
                               graph.genres[genre]))

        if sim_genres != []:
            genre = min(sim_genres, key=lambda x: x[0])[1].name

            if graph.genres[genre].song_graph.songs != {}:
                sp_i = random.choice(list(graph.genres[genre].song_graph.songs))
                song = graph.genres[genre].song_graph.songs[sp_i]
                song_list[index_to_replace] = song


def get_degree_sim_score(song_1: song_graph.Song, song_2: song_graph.Song, preferences: dict,
                         degree: int) -> \
        float:
    """
    Get a similarity score between two songs that takes into account their degree so that it
    prefers songs with a lower degree.
    """
    sim_score = math.sqrt(degree) * get_song_rating(song_1, song_2)

    par_score_1 = par_rating(song_1, preferences)
    par_score_2 = par_rating(song_2, preferences)
    ret_score = sim_score
    if par_score_1 != 0 and par_score_2 != 0:
        ret_score += 1 / abs((par_score_1 + par_score_2) / 2)
    return ret_score


def get_new_songs(graph: song_graph.GenreGraph, song_list: list[song_graph.Song])\
        -> list[song_graph.Song]:
    """
    Search method to return similar songs that are not older than a certain date.
    That date is the oldest of songs in song_list

    The search method looks at all neighbours of inputted songs calculates their similarity
    scores with respect to the entire list and takes every song posted after said date and then
    takes the 11 most similar songs.

    Preconditions:
        - graph has all vertices and edges in it.
    """
    min_date = datetime.datetime(2022, 1, 1)
    for song in song_list:
        if song.information['release_date'] < min_date:
            min_date = song.information['release_date']

    songs_to_return = []
    while len(songs_to_return) < 11:
        all_genres = set()
        for song in song_list:
            all_genres.add(song.genre)

        sim_scores = []
        for song in song_list:
            for neighbour in song.neighbours:
                sim_scores.append((get_song_rating
                                   (graph.genres[song.genre].song_graph.songs[neighbour],
                                    song_list),
                                   graph.genres[song.genre].song_graph.songs[neighbour]))

        sim_scores.sort(key=lambda x: x[0])

        songs_to_return = []
        for tup_song in sim_scores:
            if tup_song[1].information['release_date'] > min_date and tup_song[1] not in \
                    songs_to_return:
                songs_to_return.append(tup_song[1])

        if len(songs_to_return) < 11:
            shuffle_songs(song_list, graph)

    if len(songs_to_return) > 11:
        return songs_to_return[0:11]
    else:
        return songs_to_return


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
#                           'spotipy', 'spotipy.oauth2', 'graph_visualization', 'datetime',
#                           'csv', 'plotly.graph_objects', 'math', 'collections'],
#         'generated-members': ['pygame.*'],
#         'max-nested-blocks': 4,
#         'allowed-io': ['genres_to_songs', 'load_genres', 'load_artists_to_genres', 'load_songs',
#                        'open_tk', 'make_playlist']
#     })
