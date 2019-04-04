# Many credits to pythonprogramming.net for their tutorial series about dash.
# See for the tutorials: https://pythonprogramming.net/data-visualization-application-dash-python-tutorial-introduction/ 

import os
import re 
import datetime
import pprint as pp
import networkx as nx
import tqdm

import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

party_color_map = {'Labour': '#ff00ff' , 'Deputy Speaker': '#e5e500', 'Speaker': '#ffff00', 'Conservative': '#0000ff', 
                    'Independent': '#ffa500',  'Green Party': '#00cd00', 'Liberal Democrat': '#800080', 
                    'Scottish National Party': '#E56914', 'Democratic Unionist Party' : '#00ffff', 'Plaid Cymru': '#ffffff', 'Sinn F?in': '#000000'}



class VotingHistory(object):
    def __init__(self, folder:str):
        # self.members_of_parliament = MembersOfParliamentIndex()
        self._load_divisions(folder)


    def __str__(self):
        return str(pp.pformat(self.__dict__))

    def __repr__(self):
        return str(pp.pformat(self.__dict__))

    def _load_divisions(self, folder:str) -> None:
        filelist = [tuple([filenm, os.path.join(folder, filenm)]) for filenm in sorted(os.listdir(folder))]

        self.divisions = {}

        for i, (filenm, fullpath) in enumerate(filelist):
            # print(filenm)

            division = {}

            with open(fullpath, 'rt') as f:
                content = f.readlines()
                # print(content[0])
                division['division_nr'] = process_division_number(content[0])
                division['date'] = process_division_date(content[1])
                division['title'] = content[3].strip()
                division['aye_count'] = process_count(content[5])
                division['noes_count'] = process_count(content[6])
                division['votes_raw'] = process_votes_to_raw(content[10:], division['division_nr'])
                # pp.pprint(list(division.votes_raw.items())[:10])
        
            self.divisions[division['division_nr']] = division

    def get_selection_options(self):
        options = []
        for division_nr, division in self.divisions.items():
            option = {'label': division['title'], 'value': int(division_nr)}
            options.append(option)
            
        return options




def process_division_number(division_number_line:str) -> int:
    """A unique identifier (index) for a vote.
    
    :param division_number_line: Line containing the identifier
    :type division_number_line: str
    :return: The indentifier number
    :rtype: int
    """

    division_number_line = division_number_line.strip()
    match = re.match(r'[^0-9]+([0-9]+).*', division_number_line)
    nr = int(match.group(1))
    # print(nr)

    return nr

def process_division_date(date_line:str) -> datetime.datetime:
    """Parse the date on which the vote was held from a string
    
    :param date_line: line containing the date
    :type date_line: str
    :return: Datetime object of the date.
    :rtype: datetime.datetime
    """

    date_line = date_line.strip()
    datestr = date_line.split(':')[-1].strip()

    date = datetime.datetime.strptime(datestr, "%d/%m/%Y")

    return date

def process_count(count_line:str) -> int:
    """Parse the line with the count
    
    :param count_line: The line containing the count
    :type count_line: str
    :return: The count.
    :rtype: int
    """

    count_line = count_line.strip()
    count = int(count_line.split(':')[-1].strip())
    return count

def process_votes_to_raw(votes_list:list, division_nr:int) -> dict:
    """Extracts votes from the voting record
    
    :param votes_list: A list containing raw strings from the voting records
    :type votes_list: list
    :param division_nr: The index of the voting record
    :type division_nr: int
    :return: A dictionary with the individual vote ids as keys and the vote info as values 
    :rtype: dict
    """

    votes_raw = {}
    for i, vote in enumerate(votes_list):
        vote_id = f"{division_nr:04}_{i+1:03}"

        vote = vote.strip()
        vote = vote.split('","')
        assert len(vote) == 5

        votes_raw[vote_id] = vote
        

    return votes_raw

def has_node(gr: nx.Graph, att:str, val:str) -> bool:
    """Checks whether a node with value (val) for attribute (att) exists in the network.
    
    source: https://stackoverflow.com/questions/49103913/check-whether-a-node-exists-in-networkx 
    :param gr: The graph that needs to be searched
    :type gr: nx.Graph
    :param att: What attribute must be searched.
    :type att: str
    :param val: What value should the attribute have
    :type val: str
    :return: True if the queried node is in the network. False Otherwise.
    :rtype: bool
    """

    return any([node for node in gr.nodes(data=True) if node[1].get(att, None) == val])

def create_network(voting_history:VotingHistory, selection:list) -> nx.Graph:
    """Creates a voting network from all votes in voting history that are selected.
    
    :param voting_history: An object as defined above that contains voting records.
    :type voting_history: VotingHistory
    :param selection: A list of numbers (indices) of what votes are selected.
    :type selection: list
    :return: A voting graph.
    :rtype: nx.Graph
    """


    print("create network ...", flush = True)
    division_nodemap = {}
    mp_nodemap = {}

    mp_count = 1e6

    G = nx.Graph() 
    for i, (divisionnr, division) in tqdm.tqdm(enumerate(sorted(voting_history.divisions.items(), key = lambda x:x[0]))):
        if not int(divisionnr) in selection:
            continue
        G.add_node(int(i), type = 'division', division_nr = divisionnr, date = division['date'], title = division['title'], aye_count = division['aye_count'], noes_count = division['noes_count'])
        division_nodemap[divisionnr] = i

        for vote_id, vote in division['votes_raw'].items():
            mp = vote[0].strip('"')
            # print(mp)
            if not has_node(G, 'name', mp):
                G.add_node(int(mp_count), type = 'mep', name = mp, party = vote[1], constituency = vote[2])
                # parties.add(vote[1])

                mp_nodemap[mp] = mp_count
                mp_count += 1
                # G.add_node() 
            
            if vote[3].lower() == 'aye':
                G.add_edge(mp_nodemap[mp], division_nodemap[divisionnr])

            # print(vote)
    print(mp_count-1e6)


    return G, division_nodemap, mp_nodemap

def remove_loose_nodes(G:nx.Graph) -> None:
    """Removes nodes that do not have any edges: i.e. MEPs that did not vote for any of the selected votes
    
    :param G: A network as created with the "create_network()" function
    :type G: nx.Graph
    :return: Noting. Only mutates the existing graph object.
    :rtype: None
    """

    to_be_removed = []
    for node in G.nodes():
        if len(G.edges(node)) == 0:
            to_be_removed.append(node)

    G.remove_nodes_from(to_be_removed)


def visualize(G:nx.Graph, remove_empty_nodes:bool = True, layout:str = "spring") -> go.Figure:
    """Generates an interactive plot of a voting network.

    :param G: A network as created with the "create_network()" function
    :type G: nx.Graph
    :param remove_empty_nodes: Whether to remove nodes that have no edges: i.e. MEPs that did not vote for any of the bills in the selection, defaults to True
    :param remove_empty_nodes: bool, optional
    :param layout: what layout algorithm should be used. Options are: 'circular', 'random', 'shell', 'spring', 'spectral'. , defaults to "spring"
    :param layout: str, optional
    :raises RuntimeError: If an layout option is given that doesnt exist.
    :return: A plotly figure object containing the plotted network.
    :rtype: go.Figure
    """


    global party_color_map

    if remove_empty_nodes:
        remove_loose_nodes(G)

    #Get Node Positions 
    # pos=nx.get_node_attributes(G,'pos')
    print(f"calculating positions with {layout} layout...", flush = True)
    if layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'random':
        pos = nx.random_layout(G)
    elif layout == 'shell':
        pos = nx.shell_layout(G)
    elif layout == 'spring':
        pos = nx.spring_layout(G, iterations=100)
    elif layout == 'spectral':
        pos = nx.spectral_layout(G)
    else:
        raise RuntimeError(f"Unknown layout option: {layout}")
    # print(pos)
    dmin=1
    ncenter=0
    for n in pos:
        G.nodes[n]['pos'] = pos[n]
        # pp.pprint(G.nodes[n])

        x,y=pos[n]
        
        d=(x-0.5)**2+(y-0.5)**2
        if d<dmin:
            ncenter=n
            dmin=d

    p=nx.single_source_shortest_path_length(G,ncenter)

    # Create Edges
    print(f"create {len(G.edges())} edges ...", flush = True)
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5,color='black'),
        hoverinfo='none',
        mode='lines')

    for edge in tqdm.tqdm(G.edges()):
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

    # Create Nodes
    print("create nodes ...", flush = True)

    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            color=[],
            size=[],
            line=dict(width=2)))

    for node in tqdm.tqdm(G.nodes()):
        x, y = G.node[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

    # Color Node Points
    print("Color Node Points ...", flush = True)

    for i, (key, node) in tqdm.tqdm(enumerate(G.nodes().items())):

        if node.get('type', False) == 'division':
            if node['aye_count'] - node['noes_count'] > 0:
                node_trace['marker']['color'] += tuple(['green'])    
            else:
                node_trace['marker']['color'] += tuple(['red'])       
            node_info = f"Vote: {node['title']} - Ayes count: {node['aye_count']} - Noes count: {node['noes_count']}"
            node_trace['text']+=tuple([node_info])
            node_trace['marker']['size'] += tuple([15])
        else:
            node_trace['marker']['color'] += tuple([party_color_map[node['party']]])
            node_info = f"{node['name']} - {node['party']} - {node['constituency']}"
            node_trace['text']+=tuple([node_info])
            node_trace['marker']['size'] += tuple([10])


    print("create network graph ...", flush = True)

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='Network graph for votes at uk parliament.',
                titlefont=dict(size=16),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="test",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    print("returning figure")
    return fig


if __name__ == "__main__":
    app = dash.Dash()

    voting_history = VotingHistory("csv_files")             # Voting history is a container for all votes

    options = voting_history.get_selection_options()        # All votes you can choose from.    

    # Define the layout of the app.
    # Source: https://pythonprogramming.net/vehicle-data-visualization-application-dash-python-tutorial/
    app.layout = html.Div(children = [
        html.Plaintext('Note that the app might be quite slow, you might need to wait a minute for things to happen. Do not select more than 10 votes because this makes it really slow.', className='row',
                    style={'padding-top': '20px'}),
        dcc.Dropdown(
        id='input',
        options=voting_history.get_selection_options(),
        value=[441, 393, 392, 391],
        multi=True
        ),
        dcc.Graph(id='output')
    ])

    # The update function:
    # Source: https://pythonprogramming.net/dynamic-data-visualization-application-dash-python-tutorial/ 
    @app.callback(
    Output(component_id= 'output', component_property='figure'),
    [Input(component_id='input', component_property='value')])
    def update_value(input_data):
        G, _, _ = create_network(voting_history,input_data)
        fig = visualize(G)
        print('recieved_figure')
        try:
            print('return figure')
            return fig
        except:
            return "Some Error"

    # Initialize server
    app.run_server(debug=False)

