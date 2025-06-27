🎬 Online Cinema
An online cinema platform where users can browse, view, rate, and buy access to movies, while moderators and administrators manage content and users.

📚 Features
🔐 Authentication and Authorization
User registration with email and password.

Email verification via activation link valid for 24 hours.

Resend activation token if the previous one expired.

Token cleanup using celery-beat.

JWT-based login (access & refresh tokens).

Logout invalidates refresh token.

Password change and reset via email with token.

Password strength validation.

User roles: User, Moderator, Admin with different permissions.

Admins can change user groups and activate accounts manually.

👥 User Roles
User: Access to movie browsing, favorites, comments, purchases.

Moderator: Can manage movies, genres, stars, view sales.

Admin: Full access including user/group management and manual activation.

🎥 Movies & Catalog
Movie catalog with pagination, filtering, sorting.

View details, rate movies (0–10), and comment.

Like/dislike movies and comments.

Add/remove from favorites.

Search by title, actor, description, or director.

Genre list with associated movie counts.

Prevent deletion of movies purchased by any user.

⚙️ Celery Tasks
Periodic cleanup of expired activation and reset tokens.

Background tasks for sending emails.

🐳 Docker & Docker Compose
Full containerization with:

FastAPI app

PostgreSQL

Redis

Celery worker & beat

MailHog

MinIO

PgAdmin

Run with a single docker-compose up.

📦 Poetry
Dependency management with Poetry.

Reproducible builds via pyproject.toml.

🔁 CI/CD (GitHub Actions)
Auto formatting/linting (Black, flake8).

Static type checks (mypy).

Test suite (pytest) with coverage report.

Automatic deployment to AWS EC2 after PR merge.

📖 OpenAPI (Swagger) Documentation
Full API docs generated using drf-spectacular.

Access restricted to authorized users only.

🚀 Local Development Setup
Clone the repository:


git clone https://github.com/yourusername/online-cinema.git
cd online-cinema
Create .env file:

POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
EMAIL_HOST=...
EMAIL_PORT=...
SECRET_KEY=...
REDIS_PASSWORD=...


Build and run all containers:
docker-compose -f docker-compose-dev.yml up --build


FastAPI: http://localhost:8000

Swagger: http://localhost:8000/docs

Mailhog: http://localhost:8025

PgAdmin: http://localhost:3333

👤 Pre-created Users for Testing
The following users are automatically created for quick testing:

Role	Email	Password
Admin	admin@example.com	stringAS!1
Moderator	moderator@example.com	stringAS!1
User	user@example.com	stringAS!1

These users are created via initial database scripts or fixtures. Use them to test role-based functionality such as moderation, administration, and user interactions.

