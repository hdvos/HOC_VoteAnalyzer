import os
import re 
import datetime
import pprint as pp
import numpy as np 
import networkx as nx
import tqdm

import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

party_color_map = {'Labour': '#ff00ff' , 'Deputy Speaker': '#e5e500', 'Speaker': '#ffff00', 'Conservative': '#0000ff', 
                    'Independent': '#ffa500',  'Green Party': '#00cd00', 'Liberal Democrat': '#800080', 
                    'Scottish National Party': '#ee82ee', 'Democratic Unionist Party' : '#00ffff', 'Plaid Cymru': '#ffffff', 'Sinn F?in': '#000000'}
parties = set()

class Voting_Matrix(object):
    def __init__(self):
        self.row_index = {}  # mep_name to rownr
        self.row_index_reversed = {} # rownr to mepname 

        self.col_index = {}    # division_id to colnr
        self.col_index_reversed = {}   # division to vote_id

        self.M = None

    def generate_matrix(self, voting_history):
        #first_sweep
        row_idx = 0
        col_idx = 0

        for divisionnr, division in sorted(voting_history.divisions.items(), key = lambda x:x[0]):
            self.col_index[divisionnr] = col_idx
            self.col_index_reversed[col_idx] = divisionnr

            col_idx += 1
            for vote_id, vote in division['votes_raw'].items():
                mep = vote[0].strip('"')

                if not mep in self.row_index.keys():
                    self.row_index[mep] = row_idx
                    self.row_index_reversed[row_idx] = mep
                    row_idx += 1
        
        self.M = np.zeros(shape = (len(self.row_index), len(self.col_index)))
        print(self.M.shape)
        # second sweep
        for divisionnr, division in sorted(voting_history.divisions.items(), key = lambda x:x[0]):
            for vote_id, vote in division['votes_raw'].items():
                mep = vote[0].strip('"')
                rownr = self.row_index[mep]
                colnr = self.col_index[divisionnr]

                if vote[3].strip('"') == 'No':
                    self.M[rownr, colnr] = -1
                elif vote[3].strip('"') == 'Aye':
                    self.M[rownr, colnr] = 1
                else:
                    self.M[rownr, colnr] = 0

        print(self.M[:10,:10])
    


    pass



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




def process_division_number(division_number_line:str) -> int:
    division_number_line = division_number_line.strip()
    match = re.match(r'[^0-9]+([0-9]+).*', division_number_line)
    nr = int(match.group(1))
    # print(nr)

    return nr

def process_division_date(date_line:str):
    date_line = date_line.strip()
    datestr = date_line.split(':')[-1].strip()

    date = datetime.datetime.strptime(datestr, "%d/%m/%Y")

    return date

def process_count(count_line:str):
    count_line = count_line.strip()
    count = int(count_line.split(':')[-1].strip())
    return count

def process_votes_to_raw(votes_list:list, division_nr:int) -> dict:
    votes_raw = {}
    for i, vote in enumerate(votes_list):
        vote_id = f"{division_nr:04}_{i+1:03}"

        vote = vote.strip()
        vote = vote.split('","')
        assert len(vote) == 5

        votes_raw[vote_id] = vote
        

    return votes_raw

def has_node(gr, att, val):
    return any([node for node in gr.nodes(data=True) if node[1].get(att, None) == val])

def create_network(voting_history, selection):
    

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
                parties.add(vote[1])

                mp_nodemap[mp] = mp_count
                mp_count += 1
                # G.add_node() 
            
            if vote[3].lower() == 'aye':
                G.add_edge(mp_nodemap[mp], division_nodemap[divisionnr])

            # print(vote)
    print(mp_count-1e6)


    return G, division_nodemap, mp_nodemap

def visualize(G):
    global party_color_map
    #Get Node Positions 
    # pos=nx.get_node_attributes(G,'pos')
    print("calculating positions...", flush = True)
    pos = nx.spring_layout(G, iterations=50)
    print(pos)
    dmin=1
    ncenter=0
    for n in pos:
        G.nodes[n]['pos'] = pos[n]
        pp.pprint(G.nodes[n])

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
            # showscale=True,
            # # colorscale options
            # #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            # colorscale='Viridis',
            # reversescale=True,
            color=[],
            size=[],
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))

    for node in G.nodes():
        x, y = G.node[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

    # Color Node Points
    print("Color Node Points ...", flush = True)

    for i, (key, node) in enumerate(G.nodes().items()):

        if node.get('type', False) == 'division':
            if node['aye_count'] - node['noes_count'] > 0:
                node_trace['marker']['color'] += tuple(['green'])    
            else:
                node_trace['marker']['color'] += tuple(['red'])       
            # node_trace['marker']['color'] += tuple([node['aye_count'] - node['noes_count']])     
            node_info = f"Vote: {node['title']} - Aye count: {node['aye_count']} - Noes count: {node['noes_count']}"
            node_trace['text']+=tuple([node_info])
            node_trace['marker']['size'] += tuple([15])
        else:
            node_trace['marker']['color'] += tuple([party_color_map[node['party']]])
            node_info = f"{node['name']} - {node['party']} - {node['constituency']}"
            node_trace['text']+=tuple([node_info])
            node_trace['marker']['size'] += tuple([10])

    # sys.exit(42)
    # Create Network Graph
    print("create network graph ...", flush = True)

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>Network graph made with Python',
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

    # py.iplot(fig, filename='networkx')
    plot(fig)

if __name__ == "__main__":
    # mops_index = MembersOfParliamentIndex()
    voting_history = VotingHistory("/home/hdevos/Documents/work/Commons_Divisions/download_data/csv_files")
    # votingmat = Voting_Matrix()

    # votingmat.generate_matrix(voting_history)

    G, division_nodemap, mp_nodemap = create_network(voting_history, [333, 359, 367, 372, 380])
    print(G)
    

    visualize(G)
    print(parties)
    # voting_history.load_divisions()
    # print(party_set)
