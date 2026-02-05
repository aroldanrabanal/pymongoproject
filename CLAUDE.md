# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 6.0.1 web application for video game rankings and reviews. Uses a hybrid database architecture with SQLite for authentication and MongoDB for game data.

## Development Commands

### Running the Server
```bash
python manage.py runserver
```

### Database Operations
```bash
# Create migrations (only affects SQLite models)
python manage.py makemigrations

# Apply migrations to default database
python manage.py migrate

# Load initial game data
python manage.py loaddata rankingsafa/fixtures/videojuegos_data.json
```

### User Management
```bash
# Create superuser
python manage.py createsuperuser
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test rankingsafa

# Run with verbosity
python manage.py test --verbosity=2
```

### Shell Access
```bash
# Django shell
python manage.py shell
```

## Architecture

### Multi-Database Pattern

The project uses a custom database router (`pymonproject/db_routers.py`) to separate concerns:

- **SQLite (`default`)**: User authentication and Django admin
- **MongoDB (`mongodb`)**: Game data, categories, reviews, rankings

Models are routed based on their `managed` field:
- `managed=True` → SQLite (Django manages schema)
- `managed=False` → MongoDB (external schema)

### Key Models

**User** (SQLite, managed)
- Custom auth model at `rankingsafa.User`
- Roles: 'admin' or 'cliente'
- Uses email and username for authentication

**Videojuego** (MongoDB, unmanaged)
- Game catalog with category arrays and platform arrays
- Fields include pricing, age rating, multiplayer support

**Categoria** (MongoDB, unmanaged)
- Categories for organizing games
- Has code (PK), name, description, and image

**Review** (MongoDB, unmanaged)
- User reviews with 0-5 rating scale
- Linked to game by `serie` (game code) and user

**Ranking** (MongoDB, unmanaged)
- User-created tier lists by category
- `rankingList` is an ordered array of game codes
- Global rankings computed by averaging position-based points

### URL Structure

- `/rankingsafa/` - Main app routes (auth, games, categories, rankings)
- `/admin/` - Django admin interface
- `/rankingsafa/admin-dashboard/` - Custom admin dashboard

### Permission Model

- `@login_required` - Requires authentication
- `@staff_member_required` - Admin-only routes (categories CRUD, JSON upload)
- Ownership checks in views for user-specific content (reviews, rankings)

### Important Files

- `pymonproject/settings.py` - Database config, installed apps, custom auth model
- `pymonproject/db_routers.py` - Database routing logic
- `rankingsafa/models.py` - All data models
- `rankingsafa/views.py` - Core business logic (~533 lines)
- `rankingsafa/forms.py` - Form definitions with Bulma CSS classes
- `rankingsafa/urls.py` - URL routing

## MongoDB Integration

MongoDB models use `managed=False` in Meta class. This prevents Django from attempting migrations but allows ORM operations:

```python
class Videojuego(models.Model):
    # ... fields ...
    class Meta:
        managed = False
        db_table = 'videojuegos'
```

The router automatically directs queries to the MongoDB database. Use standard Django ORM:
- `Videojuego.objects.using('mongodb').filter(...)`
- `Review.objects.using('mongodb').create(...)`

## Ranking System

The global ranking algorithm computes position-based scores:
- Position 1 → 10 points
- Position 2 → 8 points
- Position 3 → 6 points
- Position 4 → 4 points
- Position 5 → 2 points

Games are ranked by total points across all user rankings in a category.

## Templates

Uses Bulma CSS framework. Base template in `templates/base.html`. All templates extend this base.

## Static Files

Located in `static/` directory (currently empty). Configure via `STATICFILES_DIRS` in settings.

## Admin Features

Staff users can:
- Manage categories (create, edit, delete with image upload)
- Bulk import games/categories via JSON upload at `/rankingsafa/upload-json/`
- Access Django admin at `/admin/`
- View custom dashboard at `/rankingsafa/admin-dashboard/`
