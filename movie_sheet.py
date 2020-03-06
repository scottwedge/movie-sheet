import gspread
from oauth2client.service_account import ServiceAccountCredentials

def authorize():
    global ws_future_movies
    global ws_ratings
    global ws_users
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('sheetapi-269619-39d07591cb19.json', scope)
    gs = gspread.authorize(credentials)

    gsheet = gs.open("apitest")
    ws_future_movies = gsheet.worksheet("future movie")
    ws_ratings = gsheet.worksheet("ratings")
    ws_users = gsheet.worksheet("users")

def pre_authorize(func):
    def inner(*args, **kwargs):
        authorize()
        returned_value = func(*args, **kwargs)
        return returned_value
    return inner

@pre_authorize    
def get_nick(id):
    ids = ws_users.col_values(1)[1:]
    try:
        index = ids.index(id) + 1
    except:
        raise ValueError('id not found. try registering')
    
    nick = ws_users.row_values(index)[1]
    return nick

@pre_authorize
def register(id, nick):
    nicks = ws_users.col_values(2)[1:]
    if nick in nicks:
        raise ValueError('nick already taken')
    
    ids = ws_users.col_values(1)[1:]
    if id in ids:
        raise ValueError('id is already registered')
    
    row = [id, nick]
    index = len(ws_users.get_all_values()) + 1
    ws_users.insert_row(row, index)
    
@pre_authorize
def find_movie(sheet, movie):
    movies = sheet.col_values(1)
    movies = [movie.lower() for movie in movies]
    try:
        index = movies.index(movie.lower()) + 1
    except ValueError:
        return None
    return index

@pre_authorize
def add_movie(sheet, movie, chooser):
    if find_movie(sheet, movie):
        raise ValueError("movie already exists")
    
    row = [movie, chooser]
    index = len(sheet.get_all_values()) + 1
    sheet.insert_row(row, index)
    return index
    
@pre_authorize    
def delete_movie(sheet, movie):
    index = find_movie(sheet, movie)
    if index:
        sheet.delete_row(index)

@pre_authorize
def find_reviewer(reviewer):
    reviewers = ws_ratings.row_values(1)
    reviewers = [reviewer.lower() for reviewer in reviewers]
    try:
        col = reviewers.index(reviewer.lower()) + 1
    except ValueError:
        return None
    return col

@pre_authorize
def add_reviewer(reviewer):
    if find_reviewer(reviewer):
        raise ValueError("reviewer already exists")
    
    col = len(ws_ratings.row_values(1)) + 1
    ws_ratings.update_cell(1, col, reviewer)
    return col

@pre_authorize
def rate_movie(movie, reviewer, rating):
    if rating <1 or rating >10:
        raise ValueError('rating must be between 1 and 10')

    col = find_reviewer(reviewer)
    if not col:
        col = add_reviewer(reviewer)
    
    ratings_index = find_movie(ws_ratings, movie)
    if not ratings_index:
        future_movies_index = find_movie(ws_future_movies, movie)
        if not future_movies_index:
            raise ValueError("movie could not be found")
        chooser = ws_future_movies.row_values(future_movies_index)[1]
        ratings_index = add_movie(ws_ratings, movie, chooser)
        ws_ratings.update_cell(ratings_index, 1, movie)
        ws_ratings.update_cell(ratings_index, 2, chooser)
        delete_movie(ws_future_movies, movie)
    
    ws_ratings.update_cell(ratings_index, col, rating)

@pre_authorize    
def average_ignore_blank(str_list):
    """Returns the average of a list of ints, floats, and strings that can be converted. Blanks and letters are ignored."""
    count = 0
    total = 0
    for i in str_list:
        if i != "":
            try:
                total += float(i)
            except ValueError:
                continue
            count += 1
    if count == 0:
        return 0
    return total/count        

@pre_authorize
def average_movie_rating(movie):
    ratings_index = find_movie(ws_ratings, movie)
    if not ratings_index:
        raise ValueError("movie could not be found")
    
    movie_row = ws_ratings.row_values(ratings_index)
    scores = movie_row[3:]
    reviewers = ws_ratings.row_values(1)[3:]
    average = average_ignore_blank(scores)
    message = f"------ {movie.upper()} ------\nAverage Score: {average}\n"
    for i, score in enumerate(scores):
        if score:
            message+=(f"{reviewers[i]}: {score}\n")
            
    return message

@pre_authorize
def average_reviewer_rating(reviewer):
    col = find_reviewer(reviewer)
    if not col:
        raise ValueError("reviewer could not be found")
    scores = ws_ratings.col_values(col)[1:]
    average = average_ignore_blank(scores)
    message = f"{reviewer} gives an average score of {average}"
    return message

@pre_authorize
def find_chooser_rows(chooser):
    all_ratings = ws_ratings.get_all_values()
    chooser_rows = [r for r in all_ratings if r[1].lower() == chooser.lower()]
    return chooser_rows

@pre_authorize
def average_chooser_rating(chooser):
    chooser_rows = find_chooser_rows(chooser)
    average_scores = [average_ignore_blank(r[2:]) for r in chooser_rows] 
    overall_average = average_ignore_blank(average_scores)
    return overall_average

@pre_authorize
def find_endorsers(movie):
    index = find_movie(ws_future_movies, movie)
    if not index:
        raise ValueError("movie could not be found")
    movie_row = ws_future_movies.row_values(index)
    current_endorsers = movie_row[2:]
    return current_endorsers
    
@pre_authorize
def endorse_movie(movie, endorser):
    index = find_movie(ws_future_movies, movie)
    if not index:
        raise ValueError("movie could not be found")
    movie_row = ws_future_movies.row_values(index)
    current_endorsers = movie_row[2:]
    if endorser not in current_endorsers:
        ws_future_movies.update_cell(index, len(movie_row)+1, endorser)
        
@pre_authorize
def unendorse_movie(movie, endorser):
    index = find_movie(ws_future_movies, movie)
    if not index:
        raise ValueError("movie could not be found")
        
    movie_row = ws_future_movies.row_values(index)
    try:
        movie_row.remove(endorser)
    except ValueError:
        return f"{endorser} cannot unendorse {movie} because {endorser} has not endorsed {movie}"
    
    delete_movie(ws_future_movies, movie)
    ws_future_movies.insert_row(movie_row, index)
    return f"{endorser} has unendorsed {movie}!"
    
# @pre_authorize
# def find_endorsers(movie):
    # index = find_movie(ws_future_movies, movie)
    # if not index:
        # raise ValueError("movie could not be found")
    # movie_row = ws_future_movies.row_values(index)
    # current_endorsers = movie_row[2:]
    
    # message = f"------ {movie.upper()} ------\n"
    # for e in current_endorsers:
        # message += e + "\n"
    
    # return message

@pre_authorize
def top_endorsed(n):
    """return movies with the most endorsements"""
    endorsements = ws_future_movies.get_all_values()[1:] # skip header row
    endorsements = [[cell for cell in row if cell] for row in endorsements] # remove all blanks
    endorsements.sort(key=len, reverse=True)
    message = "------ MOST ENDORSED MOVIES ------\n" 
    for e in endorsements[:n]:
        message += f"{e[0]} ({e[1]}): {len(e[2:])}\n" 
    return message
    
@pre_authorize
def unendorsed():
    """return movies with no endorsements"""
    endorsements = ws_future_movies.get_all_values()[1:] # skip header row
    endorsements = [[cell for cell in row if cell] for row in endorsements] # remove all blanks
    endorsements = [row for row in endorsements if len(row)<3]
    message = "------ UNENDORSED MOVIES ------\n" 
    for e in endorsements:
        message += f"{e[0]} ({e[1]})\n" 
    return message