
import osmnx as ox
import pandas as pd
import geopandas as gpd
import json
from sqlalchemy import create_engine
import time

def geoencoding_logradouros():
    city_name = 'Criciúma, Santa Catarina, Brazil'

    usuario = 'postgres'
    senha = 'postgres123'
    host = 'localhost'
    porta = 5432
    database = 'tabarato'
    conexao = f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{database}'
    engine = create_engine(conexao)

    # IMPORTANDO LOGRADOUROS...
    graph = ox.graph_from_place(city_name, network_type='drive')
    nodes, edges = ox.graph_to_gdfs(graph) # nós, arestas

    edges = edges.reset_index()

    edges["node_pair"] = edges.apply(lambda row: tuple(sorted([row.u, row.v])), axis=1)

    duplicate_edges = edges[edges.duplicated(subset="node_pair", keep=False)]

    unique_edges = edges.drop_duplicates(subset="node_pair", keep="first")

    ruas = unique_edges[['osmid', 'lanes', 'highway', 'length', 'geometry', 'ref', 'name']]

    ruas.rename(columns={'lanes': 'nr_faixas', 'highway': 'tipo_via', 
                        'length': 'comprimento', 'ref': 'observacao', 
                        'name': 'nome'}, inplace=True)

    
    ruas['source'] = pd.Series([pd.NA] * len(ruas), dtype='Int64')
    ruas['target'] = pd.Series([pd.NA] * len(ruas), dtype='Int64')
    
    ruas.to_postgis(name="logradouros_criciuma", con=engine, schema='public', if_exists="replace", index=False)

geoencoding_logradouros()