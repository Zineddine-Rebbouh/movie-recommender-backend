from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import pickle
import requests

app = FastAPI()

# Load your models
movies = pickle.load(open("movies.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

class MovieRequest(BaseModel):
    title: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_movie_details(title: str):
    """Fetch movie details by title."""
    url = f"https://api.themoviedb.org/3/search/movie?api_key=cafa902e957127d3136b990e44c129bb&query={title}"
    data = requests.get(url).json()
    image = data['results'][0]['poster_path'] if data['results'] else None
    genres = data['results'][0]['genre_ids'] if data['results'] else None
    year = data['results'][0]['release_date'][:4] if data['results'] else None
    rating = data['results'][0]['vote_average'] if data['results'] else None
    return {     
        "posterUrl": f"https://image.tmdb.org/t/p/w500{image}" if image else None,
        "genres": genres,
        "year": year,
        "rating": rating
    } 

@app.post("/recommend")
def recommend_movies(data: MovieRequest):
    print("Received request for movie:", data.title)
    title = data.title.lower()
    
    # Find the index of the movie
    matches = movies[movies['title'].str.lower() == title]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Movie not found")

    index = matches.index[0]
    distances = similarity[index]
    top_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    
    recommendations = []
    for i in top_indices:
        movie = movies.iloc[i[0]]
        recommendations.append({
            "title": movie["title"],
            "posterUrl": fetch_movie_details(movie["title"])["posterUrl"],
            "genres": fetch_movie_details(movie["title"])["genres"],
            "year": fetch_movie_details(movie["title"])["year"],
            "rating": fetch_movie_details(movie["title"])["rating"]
        })
    return {"recommendations": recommendations}



