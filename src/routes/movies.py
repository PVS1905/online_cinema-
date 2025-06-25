from typing import Optional
from sqlalchemy import desc, asc, update
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import extract
from database import MovieModel, User
from database import get_db
from database import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from database.models.movies import (
    Certification,
    DirectorModel,
    MovieLike,
    Comment,
    MoviesGenresModel,
    FavoriteMovie, MovieRating, Notification, CommentLike,
)
from schemas import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema
)
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieLikeSchema,
    CommentResponse,
    CommentCreate,
    MovieFilter,
    MovieSortParams,
    MovieSearch,
    FavoriteMovieOut,
    FavoriteMovieCreate,
    GenreWithCountOut, MovieRatingCreate
)

from sqlalchemy.orm import selectinload

from security.jwt_manager_instance import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status

from services.comments import create_reply, like_comment

# async def create_reply(comment_id: int, content: str, user: User, db: AsyncSession):
#     comment = await db.get(Comment, comment_id)
#     if not comment:
#         raise HTTPException(status_code=404, detail="Comment not found")
#
#     reply = Comment(
#         content=content,
#         user_id=user.id,
#         parent_id=comment.id,
#         movie_id=comment.movie_id
#     )
#     db.add(reply)
#
#     if comment.user_id != user.id:
#         notification = Notification(
#             recipient_id=comment.user_id,
#             message=f"User {user} replied to your movie comment.",
#         )
#         db.add(notification)
#
#     await db.commit()
#     return reply
#
#
# async def like_comment(comment_id: int, user: User, db: AsyncSession):
#     comment = await db.get(Comment, comment_id)
#     if not comment:
#         raise HTTPException(status_code=404, detail="Comment not found")
#
#     like = CommentLike(user_id=user.id, comment_id=comment_id)
#     db.add(like)
#
#     if comment.user_id != user.id:
#         notification = Notification(
#             recipient_id=comment.user_id,
#             message=f"User {user} liked your comment.",
#         )
#         db.add(notification)
#
#     await db.commit()


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    summary="Get a paginated list of movies",
    description=(
            "<h3>This endpoint retrieves a paginated list of movies from the database. "
            "Clients can specify the `page` number and the number of items per page using `per_page`. "
            "The response includes details about the movies, total pages, and total items, "
            "along with links to the previous and next pages if applicable.</h3>"
    ),
    responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            },
        }
    }
)
async def get_movie_list(
        page: int = Query(1, ge=1, description="Page number (1-based index)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    """
    Fetch a paginated list of movies from the database (asynchronously).

    This function retrieves a paginated list of movies, allowing the client to specify
    the page number and the number of items per page. It calculates the total pages
    and provides links to the previous and next pages when applicable.

    :param page: The page number to retrieve (1-based index, must be >= 1).
    :type page: int
    :param per_page: The number of items to display per page (must be between 1 and 20).
    :type per_page: int
    :param db: The async SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: A response containing the paginated list of movies and metadata.
    :rtype: MovieListResponseSchema

    :raises HTTPException: Raises a 404 error if no movies are found for the requested page.
    """
    offset = (page - 1) * per_page

    count_stmt = select(func.count(MovieModel.id))
    result_count = await db.execute(count_stmt)
    total_items = result_count.scalar() or 0

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    order_by = MovieModel.default_order_by()
    stmt = select(MovieModel).options(
        selectinload(MovieModel.languages),
        selectinload(MovieModel.directors),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.country),
        selectinload(MovieModel.certification),
    )

    if order_by:
        stmt = stmt.order_by(*order_by)

    stmt = stmt.offset(offset).limit(per_page)

    result_movies = await db.execute(stmt)
    movies = result_movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_items + per_page - 1) // per_page

    response = MovieListResponseSchema(
        movies=movie_list,
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    summary="Add a new movie",
    description=(
            "<h3>This endpoint allows clients to add a new movie to the database. "
            "It accepts details such as name, date, genres, actors, languages, and "
            "other attributes. The associated country, genres, actors, and languages "
            "will be created or linked automatically.</h3>"
    ),
    responses={
        201: {
            "description": "Movie created successfully.",
        },
        400: {
            "description": "Invalid input.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data."}
                }
            },
        }
    },
    status_code=201
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    """
    Add a new movie to the database.

    This endpoint allows the creation of a new movie with details such as
    name, release date, genres, actors, and languages. It automatically
    handles linking or creating related entities.

    :param movie_data: The data required to create a new movie.
    :type movie_data: MovieCreateSchema
    :param db: The SQLAlchemy async database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The created movie with all details.
    :rtype: MovieDetailSchema

    :raises HTTPException:
        - 409 if a movie with the same name and date already exists.
        - 400 if input data is invalid (e.g., violating a constraint).
    """
    existing_stmt = select(MovieModel).where(
        (MovieModel.name == movie_data.name),
        (MovieModel.year == movie_data.year)
    )
    existing_result = await db.execute(existing_stmt)
    existing_movie = existing_result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.year}' already exists."
            )
        )

    try:
        cert_stmt = select(Certification).where(
            Certification.name == movie_data.certification
        )
        cert_result = await db.execute(cert_stmt)
        certification = cert_result.scalars().first()

        if not certification:
            certification = Certification(name=movie_data.certification)
            db.add(certification)
            await db.flush()

        country_stmt = select(CountryModel).where(CountryModel.code == movie_data.country)
        country_result = await db.execute(country_stmt)
        country = country_result.scalars().first()
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
            actor_result = await db.execute(actor_stmt)
            actor = actor_result.scalars().first()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            lang_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
            lang_result = await db.execute(lang_stmt)
            language = lang_result.scalars().first()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            languages.append(language)

        directors = []
        for director_name in movie_data.directors:
            dir_stmt = select(DirectorModel).where(
                DirectorModel.name == director_name
            )
            dir_result = await db.execute(dir_stmt)
            director = dir_result.scalars().first()

            if not director:
                director = DirectorModel(name=director_name)
                db.add(director)
                await db.flush()
            directors.append(director)

        movie = MovieModel(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            gross=movie_data.gross,
            certification=certification,
            directors=directors,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,



        )
        db.add(movie)
        await db.commit()

        result = await db.execute(
            select(MovieModel)
            .where(MovieModel.id == movie.id)
            .options(
                selectinload(MovieModel.certification),
                selectinload(MovieModel.country),
                selectinload(MovieModel.directors),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages)
            )
        )
        movie_with_relations = result.scalars().first()

        return MovieDetailSchema.model_validate(movie_with_relations)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Get movie details by ID",
    description=(
            "<h3>Fetch detailed information about a specific movie by its unique ID. "
            "This endpoint retrieves all available details for the movie, such as "
            "its name, genre, crew, budget, and gross. If the movie with the given "
            "ID is not found, a 404 error will be returned.</h3>"
    ),
    responses={
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        }
    }
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    """
    Retrieve detailed information about a specific movie by its ID.

    This function fetches detailed information about a movie identified by its unique ID.
    If the movie does not exist, a 404 error is returned.

    :param movie_id: The unique identifier of the movie to retrieve.
    :type movie_id: int
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :return: The details of the requested movie.
    :rtype: MovieDetailResponseSchema

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.
    """

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.certification),
        )
        .where(MovieModel.id == movie_id)
    )

    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/movies/{movie_id}/",
    summary="Delete a movie by ID",
    description=(
            "<h3>Delete a specific movie from the database by its unique ID.</h3>"
            "<p>If the movie exists, it will be deleted. If it does not exist, "
            "a 404 error will be returned.</p>"
    ),
    responses={
        204: {
            "description": "Movie deleted successfully."
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    },
    status_code=204
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific movie by its ID.

    This function deletes a movie identified by its unique ID.
    If the movie does not exist, a 404 error is raised.

    :param movie_id: The unique identifier of the movie to delete.
    :type movie_id: int
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.

    :return: A response indicating the successful deletion of the movie.
    :rtype: None
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


@router.patch(
    "/movies/{movie_id}/",
    summary="Update a movie by ID",
    description=(
            "<h3>Update details of a specific movie by its unique ID.</h3>"
            "<p>This endpoint updates the details of an existing movie. If the movie with "
            "the given ID does not exist, a 404 error is returned.</p>"
    ),
    responses={
        200: {
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    }
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    """
    Update a specific movie by its ID.

    This function updates a movie identified by its unique ID.
    If the movie does not exist, a 404 error is raised.

    :param movie_id: The unique identifier of the movie to update.
    :type movie_id: int
    :param movie_data: The updated data for the movie.
    :type movie_data: MovieUpdateSchema
    :param db: The SQLAlchemy database session (provided via dependency injection).
    :type db: AsyncSession

    :raises HTTPException: Raises a 404 error if the movie with the given ID is not found.

    :return: A response indicating the successful update of the movie.
    :rtype: None
    """
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.certification),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    simple_fields = {
        "name", "year", "score", "overview", "status",
        "budget", "time", "gross", "imdb", "votes", "meta_score"
    }

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        if field in simple_fields:
            setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}


@router.post("/movies/like", status_code=201)
async def like_movie(
    like_data: MovieLikeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Чи вже існує запис?
    existing = await db.execute(
        select(MovieLike).where(
            MovieLike.user_id == current_user.id,
            MovieLike.movie_id == like_data.movie_id
        )
    )
    record = existing.scalar_one_or_none()

    if record:
        record.is_like = like_data.is_like  # оновити like/dislike
    else:
        record = MovieLike(
            user_id=current_user.id,
            movie_id=like_data.movie_id,
            is_like=like_data.is_like,
        )
        db.add(record)

    await db.commit()
    return {"message": "Like saved"}


@router.get("/movies/{movie_id}/likes")
async def get_likes_stats(movie_id: int, db: AsyncSession = Depends(get_db)):
    likes = await db.execute(
        select(
            func.count().filter(MovieLike.is_like.is_(True)),
            func.count().filter(MovieLike.is_like.is_(False))
        ).where(MovieLike.movie_id == movie_id)
    )
    like_count, dislike_count = likes.one()
    return {"likes": like_count, "dislikes": dislike_count}


@router.post("/comments/", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = Comment(
        content=comment_data.content,
        user_id=current_user.id,
        movie_id=comment_data.movie_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/movies_filter/")
async def filter_movies(
    filter_data: MovieFilter = Depends(),
    db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel).options(selectinload(MovieModel.genres))

    if filter_data.year:
        query = query.where(extract('year', MovieModel.year) == filter_data.year)
    if filter_data.imdb_min:
        query = query.where(MovieModel.imdb >= filter_data.imdb_min)
    if filter_data.imdb_max:
        query = query.where(MovieModel.imdb <= filter_data.imdb_max)
    if filter_data.name:
        query = query.where(MovieModel.name.ilike(f"%{filter_data.name}%"))
    if filter_data.genre_id:
        query = query.join(MoviesGenresModel).where(MoviesGenresModel.c.genre_id == filter_data.genre_id)

    result = await db.execute(query)
    movies = result.scalars().unique().all()
    return movies


@router.get("/movies_sorted/")
async def get_movies_sorted(
    sort_data: MovieSortParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel)

    sort_column = None
    if sort_data.sort_by == "price":
        sort_column = MovieModel.budget
    elif sort_data.sort_by == "year":
        sort_column = MovieModel.year
    elif sort_data.sort_by == "imdb":
        sort_column = MovieModel.imdb
    elif sort_data.sort_by == "votes":
        sort_column = MovieModel.votes

    if sort_column is not None:
        query = query.order_by(asc(sort_column) if sort_data.order == "asc" else desc(sort_column))

    result = await db.execute(query)
    movies = result.scalars().unique().all()
    return movies


@router.get("/movies_search/")
async def get_movies_search(
    search_data: MovieSearch = Depends(),
    db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.directors),
    )

    if search_data.genres:
        query = query.join(MovieModel.genres).where(GenreModel.name.in_(search_data.genres))

    if search_data.actors:
        query = query.join(MovieModel.actors).where(ActorModel.name.in_(search_data.actors))

    if search_data.directors:
        query = query.join(MovieModel.directors).where(DirectorModel.name.in_(search_data.directors))

    if search_data.overview:
        query = query.where(MovieModel.overview.ilike(f"%{search_data.overview}%"))

    result = await db.execute(query)
    movies = result.scalars().unique().all()
    return movies


@router.post("/favorites/")
async def add_to_favorites(
    favorite_data: FavoriteMovieCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(FavoriteMovie).where(
            FavoriteMovie.user_id == user.id,
            FavoriteMovie.movie_id == favorite_data.movie_id
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Movie already in favorites")

    new_favorite = FavoriteMovie(user_id=user.id, movie_id=favorite_data.movie_id)
    db.add(new_favorite)
    await db.commit()
    movie_result = await db.execute(
        select(MovieModel).options(selectinload(MovieModel.genres)).where(MovieModel.id == favorite_data.movie_id)
    )
    movie = movie_result.scalar_one()

    return movie


@router.get("/favorites/", response_model=list[FavoriteMovieOut])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    year: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    imdb: Optional[float] = Query(None),
    sort_data: MovieSortParams = Depends(),
):
    stmt = (
        select(MovieModel)
        .join(FavoriteMovie, FavoriteMovie.movie_id == MovieModel.id)
        .where(FavoriteMovie.user_id == user.id)
    )

    if year:
        stmt = stmt.where(extract("year", MovieModel.year) == year)
    if name:
        stmt = stmt.where(MovieModel.name.ilike(f"%{name}%"))
    if imdb:
        stmt = stmt.where(MovieModel.imdb == imdb)

    if sort_data.sort_by in ["year", "imdb", "name"]:
        sort_attr = getattr(MovieModel, sort_data.sort_by)
        stmt = stmt.order_by(
            sort_attr.asc() if sort_data.order == "asc" else sort_attr.desc()
        )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/favorite_remove/", status_code=204)
async def remove_favorite(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    movie_id: Optional[int] = Query(None),
):
    stmt = select(FavoriteMovie).where(
        FavoriteMovie.user_id == user.id,
        FavoriteMovie.movie_id == movie_id,
    )

    result = await db.execute(stmt)
    favorite = result.scalars().first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()
    return {"detail": "Movie was removed from favorites."}


@router.get("/genres/", response_model=list[GenreWithCountOut])
async def list_genres_with_counts(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(MoviesGenresModel.c.movie_id).label("movie_count")
        )
        .join(MoviesGenresModel, GenreModel.id == MoviesGenresModel.c.genre_id)
        .group_by(GenreModel.id)
        .order_by(func.count(MoviesGenresModel.c.movie_id).desc())
    )
    result = await db.execute(stmt)
    return [
        GenreWithCountOut(id=id_, name=name, movie_count=movie_count)
        for id_, name, movie_count in result.all()
    ]


@router.get("/genres/{genre_id}/movies/", response_model=list[MovieListItemSchema])
async def get_movies_by_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.languages),
            selectinload(MovieModel.directors),
        )
        .join(MoviesGenresModel, MovieModel.id == MoviesGenresModel.c.movie_id)
        .where(MoviesGenresModel.c.genre_id == genre_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/ratings/", status_code=status.HTTP_201_CREATED)
async def rate_movie(
    rating_data: MovieRatingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MovieRating).where(
            MovieRating.user_id == user.id,
            MovieRating.movie_id == rating_data.movie_id,
        )
    )
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this movie")
    else:
        new_rating = MovieRating(
            user_id=user.id,
            movie_id=rating_data.movie_id,
            rating=rating_data.rating,
        )
        db.add(new_rating)

    await db.commit()
    return {"movie_id": rating_data.movie_id, "rating": rating_data.rating}


@router.get("/notifications/", response_model=list[str])
async def get_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification).where(Notification.recipient_id == user.id).order_by(Notification.created_at.desc())
    )
    return [n.message for n in result.scalars().all()]


@router.post("/notifications/mark-read/")
async def mark_notifications_as_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"detail": "Notifications read"}

@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(
    comment_id: int,
    content: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    reply = await create_reply(comment_id, content, user, db)
    return reply

@router.post("/comments/{comment_id}/like")
async def like_comment_endpoint(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await like_comment(comment_id, user, db)
    return {"detail": "Comment liked"}
