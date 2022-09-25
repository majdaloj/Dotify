"""
This is a helper file to visualize graphs. This file connects plotly to the pygame and is meant only
to be accessed through pygame.

Contains all plotly methods.

Part of the code was adapted from A3.visualization (the usage of networkx)
"""
from typing import Any, Tuple
import networkx as nx
import plotly.graph_objects as go
import song_graph


def graph_to_nx(graph_raw: song_graph.SongGraph) -> nx.Graph:
    """This is a helper function that converts our song graph to a networkx graph"""
    new_graph = nx.Graph()
    for song in graph_raw.songs:
        new_graph.add_node(song, name=graph_raw.songs[song].name)
        for other_song in graph_raw.songs[song].neighbours:
            new_graph.add_node(other_song, name=graph_raw.songs[other_song].name)
            new_graph.add_edge(song, other_song,
                               weight=graph_raw.songs[song].neighbours[other_song])
    return new_graph


def plot_graph(graph_raw: song_graph.SongGraph) -> Any:
    """This method uses the helper function 'graph_to_nx' to make a networkx graph.
    It then visualizes it with interactive information for the user to see. This will be used
    so the user can see how the different modes of generation make different song networks

    graph_raw is the input graph from our graph software"""

    graph = graph_to_nx(graph_raw)
    pos_data = getattr(nx, 'circular_layout')(graph)  # from a3_visualization.py
    node_x, node_y, edge_x, edge_y, node_text, edge_text = get_plotly_info(graph, pos_data)
    colours = get_rainbow(node_x, node_y)
    fig = plotly_graph_node(node_x, node_y, node_text, colours)
    plotly_edges(fig, edge_x, edge_y, edge_text)


def genre_graph_to_nx(genre_graph: song_graph.GenreGraph) -> nx.Graph:
    """
    Convert a genre graph in to an appropriate nx graph.

    Return the nx graph
    """
    new_graph = nx.Graph()
    for genre in genre_graph.genres:
        new_graph.add_node(genre, name=genre)

        for other_genre in genre_graph.genres[genre].neighbours:
            new_graph.add_node(genre_graph.genres[other_genre].name,
                               name=genre_graph.genres[other_genre].name)
            new_graph.add_edge(genre, other_genre,
                               weight=genre_graph.genres[genre].neighbours[other_genre])
    return new_graph


def part_genre_graph_nx(genre_graph: song_graph.GenreGraph, target_genre: str) -> nx.Graph:
    """
    Return a nx graph which contains all vertices of the genre graph but with only the edges
    that are connected to target_genre

    Preconditions:
        - target_genre in genre_graph.genres
    """
    new_graph = nx.Graph()
    for genre in genre_graph.genres:
        new_graph.add_node(genre, name=genre)

    for other_genre in genre_graph.genres[target_genre].neighbours:
        new_graph.add_edge(target_genre, other_genre,
                           weight=genre_graph.genres[target_genre].neighbours[other_genre])
    return new_graph


def visualize_part_genre_graph(genre_graph: song_graph.GenreGraph, genre: str) -> None:
    """
    Open the plotly graph for the sub_genre graph corresponding to the genre: 'genre'.

    the sub_genre graph is the graph with all vertices of the genre graph but the only
    edges are those that connect to genre.

    Preconditions:
        - genre in genre_graph.genres
    """
    graph = part_genre_graph_nx(genre_graph, genre)
    pos_data = getattr(nx, 'circular_layout')(graph)  # from a3_visualization.py
    node_x, node_y, edge_x, edge_y, node_text, edge_text = get_plotly_info(graph, pos_data)
    colours = get_rainbow(node_x, node_y)
    fig = plotly_graph_node(node_x, node_y, node_text, colours)
    plotly_edges(fig, edge_x, edge_y, edge_text)


def plot_genre_graph(genre_graph: song_graph.GenreGraph) -> None:
    """
    Open the plotly graph for the genre graph
    """
    graph = genre_graph_to_nx(genre_graph)
    pos_data = getattr(nx, 'circular_layout')(graph)  # from a3_visualization.py
    node_x, node_y, edge_x, edge_y, node_text, edge_text = get_plotly_info(graph, pos_data)
    colours = get_rainbow(node_x, node_y)
    fig = plotly_graph_node(node_x, node_y, node_text, colours)
    plotly_edges(fig, edge_x, edge_y, edge_text)


def get_plotly_info(graph: nx.Graph, pos_data: dict) -> Tuple[list, list, list, list,
                                                              list, list]:
    """
    Return the needed parameters to plot the given graph on plotly, I.e node positions
    edge positions etc.

    pos_data is a dict containing the locations of each vertex in the inputted graph
    which is obtained from networkx
    """
    node_x, node_y, node_text = [], [], []
    for node in graph.nodes():
        node_x.append(pos_data[node][0])
        node_y.append(pos_data[node][1])
        node_text.append(graph.nodes.get(node)['name'])

    edge_x, edge_y, edge_text = [], [], []
    edge_colours = []
    for edge in graph.edges():
        start, end = edge[0], edge[1]
        edge_x += [pos_data[start][0], pos_data[end][0], None]
        edge_y += [pos_data[start][1], pos_data[end][1], None]
        colour = str(((pos_data[end][0] - pos_data[start][0] + pos_data[end][1]
                       - pos_data[start][1]) + 4) * 15.9)
        edge_colours.append('rgb(' + colour + ',' + colour + ',' + colour + ')')
        edge_text.append(graph.edges.get(edge)['weight'])

    return node_x, node_y, edge_x, edge_y, node_text, edge_text


def get_rainbow(node_x: list, node_y: list) -> list:
    """
    Return what the colours for each vertex of the plotly graph should be based on the vertex's
    x and y positions so that plotly graph is a rainbow.

    * Note that the reason why so much extra code was added among the two visualization files
    to make the graphs rainbow was because I thought it looked cool.
    """
    colours = []
    for i in range(0, len(node_x)):
        colour_3 = str(255 - max(((node_x[i] + 1) * 127.4), 1))
        colour_1 = str(max(((node_x[i] + 1) * 127.4), 1))
        colour_2 = str(max(((node_y[i] + 1) * 127.4), 1))
        colours.append('rgb(' + colour_1 + ',' + colour_2 + ',' + colour_3 + ')')
    return colours


def plotly_edges(fig: go.Figure, edge_x: list, edge_y: list, edge_text: list) -> None:
    """
    Add the edges to a plotly graph which already has its vertices added.

    Preconditions:
        - fig has vertices added to it
    """
    fig.add_trace(go.Scatter(x=edge_x,
                             y=edge_y,
                             mode='lines',
                             name='edges',
                             line=dict(color="black",
                                       width=0.3),
                             text=edge_text,
                             hoverinfo='text',
                             ))
    fig.show()


def plotly_graph_node(node_x: list, node_y: list, node_text: list, colours: list) -> go.Figure:
    """
    Create a new plotly graph and add vertices to it.

    Return the graph.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers', name='vertices',
                             marker=dict(symbol='circle-dot',
                                         size=5,
                                         color=colours
                                         ),
                             text=node_text,
                             hovertemplate='%{text}',
                             hoverlabel={'namelength': 0}
                             ))

    return fig


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
