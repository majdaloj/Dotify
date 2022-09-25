"""
Contains the code that runs the pygame visualization and handles user interaction with pygame.
"""
from typing import Tuple
import pygame
import networkx
from song_graph import GenreGraph, SongGraph
from graph_visualization import plot_genre_graph, plot_graph, visualize_part_genre_graph, \
    graph_to_nx, genre_graph_to_nx

SONG_DATA = 'Data/data.csv'
ARTIST_DATA_W_GENRES = 'Data/data_w_genres.csv'
GENRE_DATA = 'Data/data_by_genres.csv'

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 900


def initialize_screen(screen_size: tuple[int, int]) -> pygame.Surface:
    """
    Initialize pygame and the display window.

    Note that this code was adapted form tutorial 8 part 3
    """
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screen_size)
    screen.fill((255, 255, 255))
    pygame.display.flip()
    pygame.event.clear()

    return screen


def init_genre_graph(genre_graph: GenreGraph, screen: pygame.Surface) -> dict:
    """
    Display the genre graph on the pygame window.
    (i.e plot a vertices and edges). Also colour it rainbow :)
    This is the function that is called on startup and also when you type 'genre' or 'genres' and
    press enter.

    return a dictionary the contains the vertex positions of the genre graph. (This is needed
    for sub_genre_graph).

    Preconditions:
        - screen.width() > 350 and screen.height() > 350
        - genre_graph has been created (i.e vertices and edges added)

    Note that this code was adapted form tutorial 8 part 3
    """
    graph_nx = genre_graph_to_nx(genre_graph)

    center = (screen.get_width() // 2, screen.get_height() // 2)
    scale = screen.get_width() // 2 - 10 - 100
    vertex_pos = networkx.circular_layout(graph_nx, center=center, scale=scale)

    for vertex in vertex_pos:
        red_v = 255 - (255 * vertex_pos[vertex][0] // screen.get_width())
        green_v = 255 - (255 * vertex_pos[vertex][1] // screen.get_width())
        blue_v = 255 * vertex_pos[vertex][0] // screen.get_width()
        pygame.draw.circle(screen, (red_v, green_v, blue_v), vertex_pos[vertex], 2)

    visited = set()
    for vertex in vertex_pos:
        visited.add(vertex)
        for other_genre in genre_graph.genres[vertex].neighbours:
            if other_genre not in visited:
                red_l = 255 - (255 * (vertex_pos[vertex][0] + vertex_pos[other_genre][0]) // 2
                               // screen.get_width())
                green_l = 255 - (255 * (vertex_pos[vertex][1] + vertex_pos[other_genre][1]) // 2
                                 // screen.get_width())
                blue_l = 255 * (vertex_pos[vertex][0] + vertex_pos[other_genre][0]) // 2 // \
                    screen.get_width()
                pygame.draw.line(screen, (red_l, green_l, blue_l), vertex_pos[vertex],
                                 vertex_pos[other_genre], width=1)
    pygame.display.flip()

    return vertex_pos


def init_song_graph(song_graph: SongGraph, screen: pygame.Surface) -> None:
    """
    Display a song graph on the pygame window. (i.e plot a vertices and edges)
    This is the function that is called when you type out a genre and press enter

    Preconditions:
        - screen.width() > 350 and screen.height() > 350
        - song_graph has been created (i.e vertices and edges added)

    Note that this code was adapted form tutorial 8 part 3
    """
    graph_nx = graph_to_nx(song_graph)
    screen.fill((255, 255, 255))

    center = (screen.get_width() // 2, screen.get_height() // 2)
    scale = screen.get_width() // 2 - 10 - 100
    vertex_pos = networkx.circular_layout(graph_nx, center=center, scale=scale)

    for vertex in vertex_pos:
        red_v = 255 - (255 * vertex_pos[vertex][0] // screen.get_width())
        green_v = 255 - (255 * vertex_pos[vertex][1] // screen.get_width())
        blue_v = 255 * vertex_pos[vertex][0] // screen.get_width()
        pygame.draw.circle(screen, (red_v, green_v, blue_v), vertex_pos[vertex], 4)

    visited = set()
    for vertex in vertex_pos:
        visited.add(vertex)
        for other_song in song_graph.songs[vertex].neighbours:
            if other_song not in visited:
                red_l = 255 - (255 * (vertex_pos[vertex][0] + vertex_pos[other_song][0]) // 2
                               // screen.get_width())
                green_l = 255 - (255 * (vertex_pos[vertex][1] + vertex_pos[other_song][1]) // 2
                                 // screen.get_width())
                blue_l = 255 * (vertex_pos[vertex][0] + vertex_pos[other_song][0]) // 2 // \
                    screen.get_width()
                pygame.draw.line(screen, (red_l, green_l, blue_l), vertex_pos[vertex],
                                 vertex_pos[other_song], width=1)
    pygame.display.flip()


def run(result: GenreGraph) -> None:
    """
    Call this function to start the visualization. This is the only function that needs to be
    called by a user to get the pygame window and its functionality.

    Preconditions:
        - result is a genre graph that has all its vertices and edges added.

    The constants SCREEN_WIDTH and SCREEN_HEIGHT should be both more than ~ 350 if you want to
    change them.
    """
    screen_width = SCREEN_WIDTH
    screen_height = SCREEN_HEIGHT
    screen = initialize_screen((screen_width, screen_height))

    vertex_pos = init_genre_graph(result, screen)
    loop_pygame(result, screen, vertex_pos)


def get_sub_genre_graph(genre_graph: GenreGraph, target_genre: str, vertex_pos: dict,
                        screen: pygame.Surface) -> None:
    """
    Display the genre graph with the neighbours of target_genre highlighted.
    This is the function that is called when you type a genre name and click.

    Preconditions:
        - genre_graph  has all its vertices and edges added.
        - target_genre in genre_graph.genres
        - vertex_pos is the current vertex positions of the genre graph
        - screen.width() > 350 and screen.height() > 350
    """
    sub_genres = [target_genre]
    sub_genres.extend(genre_graph.genres[target_genre].neighbours)
    screen.fill((255, 255, 255))

    for genre in genre_graph.genres:
        pygame.draw.circle(screen, (0, 0, 0), vertex_pos[genre], 3)

    for genre in sub_genres:
        red_v = 255 - (255 * vertex_pos[genre][0] // screen.get_width())
        green_v = 255 - (255 * vertex_pos[genre][1] // screen.get_width())
        blue_v = 255 * vertex_pos[genre][0] // screen.get_width()
        pygame.draw.circle(screen, (red_v, green_v, blue_v), vertex_pos[genre], 3)

        if genre != target_genre:
            red_l = 255 - (255 * (vertex_pos[genre][0] + vertex_pos[target_genre][0]) // 2
                           // screen.get_width())
            green_l = 255 - (255 * (vertex_pos[genre][1] + vertex_pos[target_genre][1]) // 2
                             // screen.get_width())
            blue_l = 255 * (vertex_pos[genre][0] + vertex_pos[target_genre][0]) // 2 // \
                screen.get_width()
            pygame.draw.line(screen, (red_l, green_l, blue_l), vertex_pos[target_genre],
                             vertex_pos[genre])

    pygame.display.flip()


def to_plotly_graph(genre_graph: GenreGraph, genre: str = 'None', sub_genre: bool = False) -> None:
    """
    Call the appropriate plotly method to graph the current graph on screen.
    This is the function that is called when you press tab.

    Preconditions:
        - genre_graph has all its vertices and edges added.
        - genre in genre_graph.genres
    """
    if genre == 'None':
        plot_genre_graph(genre_graph)
    elif not sub_genre and genre != 'None':
        plot_graph(genre_graph.genres[genre].song_graph)
    elif sub_genre and genre != 'None':
        visualize_part_genre_graph(genre_graph, genre)


def handle_typing(input_string: str, key: str) -> str:
    """
    Handles changing the input_string (What the user has typed in the pygame window) when the user
    types.

    Preconditions:
        - key is the str representation of the common name for the key the user just typed
    """
    if key == 'space':
        curr_string = input_string + ' '
    elif key == 'backspace':
        curr_string = input_string[:-1]
    elif key == 'right shift':
        curr_string = ''
    else:
        curr_string = input_string + key

    return curr_string


def handle_return_press(genre_graph: GenreGraph, screen: pygame.Surface,
                        input_str: str, curr_vert_pos: dict) -> Tuple[str, str, dict]:
    """
    Returns what the values of the curr_genre, input_str and curr_vert_pos should be when
    the user presses enter. Also display the correct graph on pygame.

    Preconditions:
        - genre_graph has all its vertices and edges added.
        - screen.get_height() > 350 and screen.get_width() > 350
    """
    if input_str in genre_graph.genres:
        # input str is a genre, display the its song graph update vert pos, clear input string
        # and set the curr_genre as the inputted genre ->this is needed to tell plotly what to graph
        init_song_graph(genre_graph.genres[input_str].song_graph, screen)
        return input_str, '', curr_vert_pos

    elif input_str in {'genre', 'genres'}:
        # draw the genre graph.
        screen.fill((255, 255, 255))
        vert_pos = init_genre_graph(genre_graph, screen)
        return 'None', '', vert_pos

    else:
        # input_str is not a valid input so do not do anything.
        return 'None', input_str, curr_vert_pos


def loop_pygame(genre_graph: GenreGraph, screen: pygame.Surface, init_vertex_pos: dict) -> None:
    """
    The main pygame loop that keeps the window open and checks for inputs

    Preconditions:
        - genre_graph has all its vertices and edges added.
        - screen.get_height() > 350 and screen.get_width() > 350
        - init_vertex_pos are the vertex positions of the genre graph on the initial call of run
    """
    run_pygame = True
    curr_vert_pos = init_vertex_pos
    input_string = ''

    font = pygame.font.SysFont(name='', size=30)
    rect = pygame.rect.Rect((0, 0), (1000, 50))

    curr_genre = 'None'
    sub_genre = False

    while run_pygame:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:

                if pygame.key.name(event.key) == 'return':
                    sub_genre = False
                    pygame.draw.rect(screen, (255, 255, 255), rect)

                    curr_genre, input_string, curr_vert_pos, = \
                        handle_return_press(genre_graph, screen, input_string, curr_vert_pos)

                elif pygame.key.name(event.key) == 'tab':
                    to_plotly_graph(genre_graph, curr_genre, sub_genre)
                else:
                    input_string = handle_typing(input_string, pygame.key.name(event.key))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_string in genre_graph.genres:
                    curr_genre = input_string
                    sub_genre = True
                    get_sub_genre_graph(genre_graph, input_string, curr_vert_pos, screen)
                    input_string = ''

            elif event.type == pygame.QUIT:
                run_pygame = False

            pygame.draw.rect(screen, (255, 255, 255), rect)
            text = font.render(input_string, False, (0, 0, 0))
            screen.blit(text, (0, 0))
            pygame.display.flip()

    pygame.display.quit()
    pygame.quit()


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
#         'allowed-io': ['genres_to_songs', 'load_genres', 'load_artists_to_genres', 'load_songs']
#     })
