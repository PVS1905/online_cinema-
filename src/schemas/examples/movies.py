movie_item_schema_example = {
    "id": 9933,
    "name": "The Swan Princess: A Royal Wedding",
    "year": "2020-07-20",
    "score": 70,
    "overview": "Princess Odette and Prince Derek are going to a wedding at Princess Mei Li and her beloved Chen. "
                "But evil forces are at stake and the wedding plans are tarnished and "
                "true love has difficult conditions."
}

movie_list_response_schema_example = {
    "movies": [
        movie_item_schema_example
    ],
    "prev_page": "/theater/movies/?page=1&per_page=1",
    "next_page": "/theater/movies/?page=3&per_page=1",
    "total_pages": 9933,
    "total_items": 9933
}

movie_create_schema_example = {
    "name": "New Mvi",
    "overview": "An amazing movie.",
    "score": 85.5,
    "status": "Released",
    "year": "2025-01-21",
    "time": 120,
    "imdb": 8.7,
    "votes": 1500,
    "meta_score": 71,
    "certification": "PG-13",
    "directors": ["Jane Director"],
    "actors": ["John D", "Jane Doe"],
    "budget": 1000000,
    "country": "UA",
    "genres": ["Action", "Adventure"],
    "gross": 5000000,
    "languages": ["English", "French"],
}


language_schema_example = {
    "id": 1,
    "name": "English"
}

country_schema_example = {
    "id": 1,
    "code": "US",
    "name": "United States"
}

genre_schema_example = {
    "id": 1,
    "name": "Comedy"
}

genre_schema_create_example = {
    "name": "Comedy"
}
actor_schema_example = {
    "id": 1,
    "name": "JimmyFallon"
}
actor_schema_create_example = {
    "name": "JimmyFallon"
}
director_schema_example = {
    "id": 1,
    "name": "JimmyDirectors"
}


movie_detail_schema_example = {
    **movie_item_schema_example,
    "status": "Released",
    "budget": 1000000.00,
    "gross": 5000000.00,
    "actors": [actor_schema_example],
    "country": country_schema_example,
    "genres": [genre_schema_example],
    "languages": [language_schema_example]
}

movie_update_schema_example = {
    "name": "Update Movie",
    "year": "2025-01-01",
    "score": 85.5,
    "overview": "An amazing movie.",
    "status": "Released",
    "budget": 1000000.00,
    "gross": 5000000.00,
    "genre_ids": ["id"],
}
