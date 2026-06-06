from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieRead, Movie, MovieCreate, MovieDetail, MovieUpdate

router = APIRouter()


@router.get("/movies/")
async def movies_list(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count = await db.execute(select(func.count(MovieModel.id)))
    total_items = count.scalar()

    offset = (page - 1) * per_page
    total_pages = (total_items + per_page - 1) // per_page

    movies = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies_result = movies.scalars().all()
    movies_list = [
        Movie.model_validate(movie, from_attributes=True) for movie in movies_result
    ]

    if not movies_result:
        return JSONResponse(status_code=404, content={"detail": "No movies found."})

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page >= total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieRead(
        movies=movies_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", status_code=201, response_model=MovieDetail)
async def movie_create(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    existing_movie = existing_movie.scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    movie_model = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
    )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country_model = country_result.scalar_one_or_none()
    if country_model:
        movie_model.country = country_model
    else:
        country_model = CountryModel(code=movie.country)
        db.add(country_model)
        await db.flush()
        movie_model.country = country_model

    genres_list = []
    for genre in movie.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == genre))
        genre_model = result.scalar_one_or_none()
        if genre_model:
            genres_list.append(genre_model)
        else:
            genre_model = GenreModel(name=genre)
            db.add(genre_model)
            await db.flush()
            genres_list.append(genre_model)
    movie_model.genres = genres_list

    actors_list = []
    for actor in movie.actors:
        result = await db.execute(select(ActorModel).where(ActorModel.name == actor))
        actor_model = result.scalar_one_or_none()
        if actor_model:
            actors_list.append(actor_model)
        else:
            actor_model = ActorModel(name=actor)
            db.add(actor_model)
            await db.flush()
            actors_list.append(actor_model)
    movie_model.actors = actors_list

    languages_list = []
    for language in movie.languages:
        result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == language)
        )
        language_model = result.scalar_one_or_none()
        if language_model:
            languages_list.append(language_model)
        else:
            language_model = LanguageModel(name=language)
            db.add(language_model)
            await db.flush()
            languages_list.append(language_model)
    movie_model.languages = languages_list

    db.add(movie_model)
    await db.commit()
    await db.refresh(movie_model)

    movie_result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_model.id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = movie_result.scalar_one()

    movie_detail = MovieDetail.model_validate(movie, from_attributes=True)
    return movie_detail


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def movies_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie_model = movie.scalar_one_or_none()

    if not movie_model:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    movie_detail = MovieDetail.model_validate(movie_model, from_attributes=True)

    return movie_detail


@router.delete("/movies/{movie_id}/")
async def movie_delete(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_delete = movie.scalar_one_or_none()

    if not movie_to_delete:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie_to_delete)
    await db.commit()

    return Response(status_code=204)


@router.patch("/movies/{movie_id}/", status_code=200)
async def movie_update(
    movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    db_movie = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_model = db_movie.scalar_one_or_none()

    if not movie_model:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if movie.name is not None:
        movie_model.name = movie.name

    if movie.date is not None:
        movie_model.date = movie.date

    if movie.score is not None:
        movie_model.score = movie.score

    if movie.overview is not None:
        movie_model.overview = movie.overview

    if movie.status is not None:
        movie_model.status = movie.status

    if movie.budget is not None:
        movie_model.budget = movie.budget

    if movie.revenue is not None:
        movie_model.revenue = movie.revenue

    await db.commit()
    await db.refresh(movie_model)
    return {"detail": "Movie updated successfully."}
