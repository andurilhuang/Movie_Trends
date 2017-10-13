#import os
#os.chdir("C:\\Users\\Anna Huang\\Desktop\\598\\a6-movie-trends-JackHannnnnn")
import requests
import json
import pandas as pd
from apikeys import TMDB_KEY
from datetime import datetime
"""movie trend functions start here"""
def get_genres_dict():
    '''Returns a dictitonay whose key is the genre name and whose value is the genre id'''
    genres = requests.get("https://api.themoviedb.org/3/genre/movie/list?api_key=%s&language=en-US" % TMDB_KEY).json()
    return {item['name']: item['id'] for item in genres['genres']}
    
def get_movies_by_genre(genre, year=2016):
    '''Return a list of movies with details given a genre id and a release year'''
    
    query = "https://api.themoviedb.org/3/discover/movie?api_key=%s" \
            + "&language=en-US&sort_by=release_date.desc&primary_release_year=%d&page=%d" \
            + "&with_genres=%d" \
            + "&include_adult=false&include_video=false"
    total_pages = requests.get(query % (TMDB_KEY, 2016, 1, genre)).json()['total_pages']

    start = datetime.now()
    print("Getting the movies of the genre id %d released in %d..." % (genre, year))
    print("Total number of pages:", total_pages)
    movies = []
    for page_id in range(1, total_pages + 1):
        if page_id % 10 == 0:
            print("#Pages retrieved:", page_id, "\tTime elapsed: ", datetime.now() - start)
        movies.extend(requests.get(query % (TMDB_KEY, 2016, page_id, genre)).json()['results'])
    print()
    return movies

def get_distribution_by_month(movies_genre):
    '''Return a dict whose key is the month and whose value is the number of movies given movie data of a genre'''
    result = {}
    for month in range(1, 13):
        result[month] = sum([1 for movie in movies_genre if int(movie['release_date'].split('-')[1]) == month])
    return result

def get_genre_visualization_data(genres, year=2016):
    '''Return the data needed for visualization given a list of genres'''
    res = {}
    genres_dict = get_genres_dict()
    for genre in genres:
        res[genre] = get_distribution_by_month(get_movies_by_genre(genres_dict[genre], year))
    return res

def draw_line_charts(genre_visualization_data):
    '''Draw a line for each genre in the visualization data'''
    from bokeh.plotting import figure, output_file, show
    from bokeh.models import Range1d
    from bokeh.palettes import Spectral11

    output_file("genre_by_season.html")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    x = months
    # Adjust y range to have a more elegant layout
    y_max = max([num for genre in genre_visualization_data.keys() for num in genre_visualization_data[genre].values()])
    p = figure(title="Releases by genre: 2016", 
               x_range=months, 
               y_range=Range1d(0, y_max * 1.5))
    p.yaxis.axis_label = 'Releases'
    p.xaxis.axis_label = 'Month'
    
    num_lines=len(genre_visualization_data)
    my_palette=Spectral11[0:num_lines]
    for i, genre in enumerate(genre_visualization_data.keys()):
        y = [num for m, num in genre_visualization_data[genre].items()]
        p.line(x, y, line_width=2, legend=genre, line_color=my_palette[i])
    show(p)
    
"""actor popularity functions start here"""    
def get_actor_data(actor):
    """Locate actor ID, and pull out all movie ids and related release date base on the actor ID"""
    url = "https://api.themoviedb.org/3/search/person"
    payload = {'api_key':TMDB_KEY, 'query':actor, 'language':'en-US'}
    result = requests.get( url, data=payload)
    result_dict = result.json()
    actor_id = result_dict['results'][0]['id']
    actor_data = requests.get("https://api.themoviedb.org/3/person/%d/movie_credits?api_key=%s&language=en-US" % (actor_id, TMDB_KEY)).json()
    return {item['id']: item['release_date'] for item in actor_data['cast']}

def query_movie(id):
    """call procedure to get profit data of a particular movie (id)"""
    query = "https://api.themoviedb.org/3/movie/%d?" \
        +"api_key=%s" \
        +"&language=en-US"
    request = requests.get(query %(id,TMDB_KEY)).json()
    return {request['id']:(request['revenue']-request['budget'])/1000000}
    
def get_profit_data(actor):
    """pull each movie id and its profit into a list by id, filtered by profit not negative"""
    start = datetime.now()
    profit_stat_dict = {}
    actor_dict = get_actor_data(actor)
    movie_id_list = list(actor_dict.keys())
    for i in movie_id_list:
        movie_data = query_movie(i)
        print ('Movie ID ' + str(i) +' and release date retrieved, Time elapsed',datetime.now()-start)
        if movie_data[i]>0:
            profit_stat_dict.update(movie_data)
    print ('Profit calculated, Time elapsed', datetime.now()-start)
    return profit_stat_dict
    
def merge_data(actor):
    """combine movie id, year, and profit into a data frame"""
    actor_dict = get_actor_data(actor)
    profit_stat_dict = get_profit_data(actor)
    data = {'id':[],'date':[], 'profit':[]}
    data['id'] = list(profit_stat_dict.keys())
    for i in list(profit_stat_dict.values()):
        data['profit'].append(i)
    for i in actor_dict.keys():
        if i in data['id']:
            data['date'].append(datetime.strptime(actor_dict[i],'%Y-%m-%d'))
    data = pd.DataFrame(data)
    data = data.sort_values(['date'])
    return data
    
def plot_visualization(actor):
    """start plotting visulaization"""
    data = merge_data(actor)
    from bokeh.plotting import figure, output_file, show 
    from bokeh.models import DatetimeTickFormatter
    start = datetime.now()
    output_file("actor_popularity.html")
    p = figure(title = 'Historical Movie Profits of ' + actor,plot_width=600, plot_height=600)
    p.line(x = data['date'].tolist(), y = data['profit'].tolist())
    p.yaxis.axis_label = 'Profit (in million)'
    p.xaxis.axis_label = 'Date'   
    p.xaxis.formatter=DatetimeTickFormatter(
            hours=["%Y"],
            days=["%Y"],
            months=["%Y"],
            years=["%Y"],
        )
    print ('Visualization graphed, Time elapsed', datetime.now()-start)
    show(p)        

if __name__ == '__main__':
    """input genre first"""
    genres = input("Enter a list of genre names seperated by a space: ").split()
    if len(genres) == 0:
        genre_data = get_genre_visualization_data(['Action', 'Adventure', 'Animation', 'Comedy', 'Crime'])
    else:
        genre_data = get_genre_visualization_data(genres)
    draw_line_charts(genre_data)
    """input actor name"""
    actor = input("Please enter actor name: ")
    if len(actor) == 0:
        actor = 'Nicolas Cage'
    plot_visualization(actor)
