"""Curated movie names and display metadata for the sample cinema catalogue."""

from pathlib import Path

MOVIE_TITLES = {
    'Tamil': (
        'Leo', 'Vikram', 'Ponniyin Selvan: I', 'Jailer', 'Master', 'Kaithi',
        'Soorarai Pottru', 'Jai Bhim', 'Asuran', 'Super Deluxe', '96',
        'Vada Chennai', 'Thani Oruvan', 'Mersal', 'Enthiran', 'Anbe Sivam',
        'Anniyan', 'Ghilli', 'Thuppakki', 'Petta', 'GOAT', 'Amaran',
    ),
    'Telugu': (
        'RRR', 'Baahubali: The Beginning', 'Baahubali 2: The Conclusion',
        'Pushpa: The Rise', 'Arjun Reddy', 'Eega', 'Jersey',
        'Ala Vaikunthapurramuloo', 'Rangasthalam', 'Magadheera', 'Mahanati',
        'C/o Kancharapalem', 'Sita Ramam', 'Salaar: Part 1 – Ceasefire',
        'Hanu-Man', 'Kalki 2898 AD', 'Athadu', 'Pokiri', 'Okkadu', 'Drushyam',
    ),
    'Hindi': (
        'Dangal', '3 Idiots', 'Lagaan', 'Sholay', 'Queen', 'Gully Boy',
        'Andhadhun', 'Drishyam 2', 'Zindagi Na Milegi Dobara', 'Dil Chahta Hai',
        'Bajrangi Bhaijaan', 'PK', 'Pathaan', 'Jawan', 'Gadar 2',
        'Taare Zameen Par', 'Swades', 'Chak De! India', 'Munna Bhai M.B.B.S.',
        'Kahaani',
    ),
    'Malayalam': (
        'Drishyam', 'Manjummel Boys', 'Premam', 'Kumbalangi Nights',
        'Bangalore Days', 'Kireedam', 'Maheshinte Prathikaaram', 'Ustad Hotel',
        '2018', 'Aavesham', 'Lucifer', 'Minnal Murali', 'The Goat Life',
        'Neru', 'Joji',
    ),
    'Kannada': (
        'KGF: Chapter 1', 'KGF: Chapter 2', 'Kantara', '777 Charlie', 'Lucia',
        'U Turn', 'Kirik Party', 'Sapta Sagaradaache Ello – Side A',
        'Garuda Gamana Vrishabha Vahana', 'Dia', 'Mungaru Male', 'Tagaru',
        'Avane Srimannarayana', 'Raajakumara', 'Ondu Motteya Kathe',
    ),
    'English': (
        'Inception', 'Interstellar', 'The Dark Knight', 'Oppenheimer',
        'Dune: Part Two', 'The Shawshank Redemption', 'Forrest Gump',
        'The Matrix', 'Jurassic Park', 'The Godfather', 'Titanic', 'Avatar',
        'The Lord of the Rings: The Fellowship of the Ring', 'Whiplash',
        'The Grand Budapest Hotel', 'Everything Everywhere All at Once',
        'The Social Network', 'La La Land', 'The Truman Show', 'Gladiator',
    ),
}

# Display values keep the demo catalogue self-contained and do not affect booking.
GENRES = {
    'Tamil': ('Action', 'Crime · Thriller', 'Historical · Drama', 'Drama', 'Action · Thriller'),
    'Telugu': ('Action · Drama', 'Fantasy · Adventure', 'Romance · Drama', 'Action · Thriller', 'Drama'),
    'Hindi': ('Drama', 'Comedy · Drama', 'Action · Thriller', 'Romance · Drama', 'Thriller'),
    'Malayalam': ('Drama · Thriller', 'Comedy · Drama', 'Crime · Thriller', 'Drama', 'Action · Thriller'),
    'Kannada': ('Action · Drama', 'Thriller', 'Drama', 'Crime · Thriller', 'Comedy · Drama'),
    'English': ('Science Fiction', 'Drama', 'Action · Adventure', 'Thriller', 'Fantasy · Adventure'),
}

# Poster searches are accepted only when title, release year, and original language match.
import json
import os
import re
import threading
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


MOVIE_RELEASE_YEARS = {
    # Tamil
    'Leo': 2023, 'Vikram': 2022, 'Ponniyin Selvan: I': 2022, 'Jailer': 2023,
    'Master': 2021, 'Kaithi': 2019, 'Soorarai Pottru': 2020, 'Jai Bhim': 2021,
    'Asuran': 2019, 'Super Deluxe': 2019, '96': 2018, 'Vada Chennai': 2018,
    'Thani Oruvan': 2015, 'Mersal': 2017, 'Enthiran': 2010, 'Anbe Sivam': 2003,
    'Anniyan': 2005, 'Ghilli': 2004, 'Thuppakki': 2012, 'Petta': 2019,
    'GOAT': 2024, 'Amaran': 2024,
    # Telugu
    'RRR': 2022, 'Baahubali: The Beginning': 2015,
    'Baahubali 2: The Conclusion': 2017, 'Pushpa: The Rise': 2021,
    'Arjun Reddy': 2017, 'Eega': 2012, 'Jersey': 2019,
    'Ala Vaikunthapurramuloo': 2020, 'Rangasthalam': 2018, 'Magadheera': 2009,
    'Mahanati': 2018, 'C/o Kancharapalem': 2018, 'Sita Ramam': 2022,
    'Salaar: Part 1 ??? Ceasefire': 2023, 'Hanu-Man': 2024, 'Kalki 2898 AD': 2024,
    'Athadu': 2005, 'Pokiri': 2006, 'Okkadu': 2003, 'Drushyam': 2014,
    # Hindi
    'Dangal': 2016, '3 Idiots': 2009, 'Lagaan': 2001, 'Sholay': 1975,
    'Queen': 2013, 'Gully Boy': 2019, 'Andhadhun': 2018, 'Drishyam 2': 2022,
    'Zindagi Na Milegi Dobara': 2011, 'Dil Chahta Hai': 2001,
    'Bajrangi Bhaijaan': 2015, 'PK': 2014, 'Pathaan': 2023, 'Jawan': 2023,
    'Gadar 2': 2023, 'Taare Zameen Par': 2007, 'Swades': 2004,
    'Chak De! India': 2007, 'Munna Bhai M.B.B.S.': 2003, 'Kahaani': 2012,
    # Malayalam
    'Drishyam': 2013, 'Manjummel Boys': 2024, 'Premam': 2015,
    'Kumbalangi Nights': 2019, 'Bangalore Days': 2014, 'Kireedam': 1989,
    'Maheshinte Prathikaaram': 2016, 'Ustad Hotel': 2012, '2018': 2023,
    'Aavesham': 2024, 'Lucifer': 2019, 'Minnal Murali': 2021,
    'The Goat Life': 2024, 'Neru': 2023, 'Joji': 2021,
    # Kannada
    'KGF: Chapter 1': 2018, 'KGF: Chapter 2': 2022, 'Kantara': 2022,
    '777 Charlie': 2022, 'Lucia': 2013, 'U Turn': 2016, 'Kirik Party': 2016,
    'Sapta Sagaradaache Ello ??? Side A': 2023,
    'Garuda Gamana Vrishabha Vahana': 2021, 'Dia': 2020, 'Mungaru Male': 2006,
    'Tagaru': 2018, 'Avane Srimannarayana': 2019, 'Raajakumara': 2017,
    'Ondu Motteya Kathe': 2017,
    # English
    'Inception': 2010, 'Interstellar': 2014, 'The Dark Knight': 2008,
    'Oppenheimer': 2023, 'Dune: Part Two': 2024,
    'The Shawshank Redemption': 1994, 'Forrest Gump': 1994, 'The Matrix': 1999,
    'Jurassic Park': 1993, 'The Godfather': 1972, 'Titanic': 1997, 'Avatar': 2009,
    'The Lord of the Rings: The Fellowship of the Ring': 2001, 'Whiplash': 2014,
    'The Grand Budapest Hotel': 2014, 'Everything Everywhere All at Once': 2022,
    'The Social Network': 2010, 'La La Land': 2016, 'The Truman Show': 1998,
    'Gladiator': 2000,
}

# Alternate official titles/transliterations are permitted only for the same film.
TMDB_TITLE_ALIASES = {
    'Ponniyin Selvan: I': ('Ponniyin Selvan: Part I',),
    'GOAT': ('The Greatest of All Time',),
    'C/o Kancharapalem': ('Care of Kancharapalem',),
    'Salaar: Part 1 ??? Ceasefire': ('Salaar: Part 1 - Ceasefire',),
    'The Goat Life': ('Aadujeevitham', 'The Goat Life'),
    'Sapta Sagaradaache Ello ??? Side A': ('Sapta Sagaradaache Ello: Side A', 'Sapta Sagaradaache Ello - Side A'),
}

# These legacy catalog strings contain a replacement dash character in the source file.
# Positional keys keep their year and official-title matching data attached correctly.
MOVIE_RELEASE_YEARS[MOVIE_TITLES['Telugu'][13]] = 2023
MOVIE_RELEASE_YEARS[MOVIE_TITLES['Kannada'][7]] = 2023


TMDB_TITLE_ALIASES[MOVIE_TITLES['Telugu'][13]] = ('Salaar: Part 1 - Ceasefire',)
TMDB_TITLE_ALIASES[MOVIE_TITLES['Kannada'][7]] = (
    'Sapta Sagaradaache Ello: Side A', 'Sapta Sagaradaache Ello - Side A',
)

TMDB_LANGUAGE_CODES = {
    'Tamil': ('ta', 'ta-IN'),
    'Telugu': ('te', 'te-IN'),
    'Hindi': ('hi', 'hi-IN'),
    'Malayalam': ('ml', 'ml-IN'),
    'Kannada': ('kn', 'kn-IN'),
    'English': ('en', 'en-US'),
}

_POSTER_CACHE_FILE = Path(__file__).with_name("tmdb_poster_cache.json")
_POSTER_CACHE_LOCK = threading.Lock()
_TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
_POSTER_PLACEHOLDER_BASE = "https://placehold.co/600x900/17243a/ffffff?text="


def _load_poster_cache():
    try:
        with _POSTER_CACHE_FILE.open("r", encoding="utf-8") as cache_file:
            data = json.load(cache_file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_poster_cache(cache):
    temporary_file = _POSTER_CACHE_FILE.with_suffix(".json.tmp")
    try:
        with temporary_file.open("w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file, ensure_ascii=False, indent=2)
        temporary_file.replace(_POSTER_CACHE_FILE)
    except OSError:
        # A read-only deployment can still use a verified URL for this request.
        try:
            temporary_file.unlink(missing_ok=True)
        except OSError:
            pass


def _normalized_title(value):
    decomposed = unicodedata.normalize("NFKD", value or "")
    return "".join(character.casefold() for character in decomposed if character.isalnum())


def placeholder_poster_url(movie_title):
    """Return the existing title-labelled fallback poster URL."""
    return f"{_POSTER_PLACEHOLDER_BASE}{quote(movie_title)}"


def _is_exact_movie_match(result, movie_title, release_year, language_code):
    if result.get("original_language") != language_code:
        return False
    release_date = result.get("release_date", "")
    if not release_date.startswith(f"{release_year:04d}-"):
        return False

    expected_titles = (movie_title, *TMDB_TITLE_ALIASES.get(movie_title, ()))
    accepted_titles = {_normalized_title(title) for title in expected_titles}
    result_titles = {
        _normalized_title(result.get("title", "")),
        _normalized_title(result.get("original_title", "")),
    }
    return bool(accepted_titles & result_titles)


def get_poster_url(movie_title, release_year, language):
    """Resolve only an exact TMDb title/year/original-language poster match."""
    language_code, _display_locale = TMDB_LANGUAGE_CODES[language]
    cache_key = f"v2|{movie_title}|{release_year}|{language_code}"

    with _POSTER_CACHE_LOCK:
        cache = _load_poster_cache()
        if cache_key in cache:
            return cache[cache_key] or placeholder_poster_url(movie_title)

        api_key = os.environ.get("TMDB_API_KEY", "").strip()
        if not api_key:
            return placeholder_poster_url(movie_title)

        search_titles = (movie_title, *TMDB_TITLE_ALIASES.get(movie_title, ()))
        exact_match = None
        all_searches_succeeded = True
        for search_title in search_titles:
            query = urlencode({
                "api_key": api_key,
                "query": search_title,
                "year": release_year,
                "include_adult": "false",
                "language": "en-US",
                "page": 1,
            })
            request = Request(
                f"https://api.themoviedb.org/3/search/movie?{query}",
                headers={"Accept": "application/json", "User-Agent": "Quadori/1.0"},
            )
            results = None
            for attempt in range(3):
                try:
                    with urlopen(request, timeout=6) as response:
                        results = json.load(response).get("results", [])
                    break
                except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
                    if attempt < 2:
                        time.sleep(0.25 * (attempt + 1))
            if results is None:
                all_searches_succeeded = False
                break

            exact_match = next((
                result for result in results
                if result.get("poster_path")
                and _is_exact_movie_match(result, movie_title, release_year, language_code)
            ), None)
            if exact_match:
                break

        if not all_searches_succeeded:
            return placeholder_poster_url(movie_title)
        poster_url = (
            f"{_TMDB_IMAGE_BASE}{exact_match['poster_path']}"
            if exact_match else None
        )
        if poster_url and any(
            key != cache_key and cached_url == poster_url
            for key, cached_url in cache.items()
        ):
            poster_url = None

        cache[cache_key] = poster_url
        _save_poster_cache(cache)
        return poster_url or placeholder_poster_url(movie_title)
