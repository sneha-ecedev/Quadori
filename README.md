# Quadori

Quadori is a Django booking site for flights, buses, trains, hotels, restaurants, and movies. It uses Django's built-in authentication, SQLite, Bootstrap 5, and sample service listings.

## Requirements

- Python 3.13
- SQLite (included with Python)
- Packages listed in `requirements.txt`

## Set up locally

From the project directory, create and activate a virtual environment, then install the dependencies:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create the database tables and an administrator account:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Main pages

| Page | Path |
| --- | --- |
| Landing page | `/` |
| Register | `/accounts/register/` |
| Login | `/accounts/login/` |
| Password reset | `/accounts/password-reset/` |
| User profile | `/accounts/profile/` |
| User dashboard | `/dashboard/` |
| Flights | `/flights/` |
| Buses | `/buses/` |
| Trains | `/trains/` |
| Hotels | `/hotels/` |
| Restaurants | `/restaurants/` |
| Movies | `/movies/` |
| My bookings | `/my-bookings/` |
| Admin dashboard | `/admin-dashboard/` |
| Django admin | `/admin/` |

The admin dashboard requires a staff account. `createsuperuser` creates one.

## Notes

- Booking catalogs currently use sample listings. Booking records are stored in the local SQLite database.
- Password reset email is printed to the development console by Django's console email backend.
- Profile photos are stored under `media/profile_photos/` during local development.
- The project includes a Profile model migration. Run `python manage.py migrate` after pulling changes.
- Bootstrap 5 and Bootstrap Icons are loaded from their CDNs, so the rendered pages need a network connection for those assets.

## Checks

```powershell
python manage.py check
python manage.py test
```
