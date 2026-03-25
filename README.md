# TuitionHub API

TuitionHub is a Django REST Framework backend for managing tutor-student tuition workflows. It supports role-based authentication, tuition publishing, student applications, enrollments, progress tracking, reviews, and payment integration.

## Features

- Custom email-based user model with role support (`User`, `Tutor`)
- JWT auth via Djoser + SimpleJWT
- Tuition CRUD with filtering, search, ordering, and pagination
- Student application flow with tutor selection and enrollment creation
- Enrollment progress endpoints with nested topics and assignments
- Tuition review system with enrollment-based validation
- SSLCommerz payment initiation and callback handling
- Payment history, tutor wallet, and invoice read APIs
- Swagger and ReDoc API docs

## Tech Stack

- Django 5.2.6
- Django REST Framework 3.16.1
- djoser 2.3.3
- djangorestframework-simplejwt 5.5.1
- drf-nested-routers 0.94.2
- django-filter 25.1
- drf-yasg 1.21.10
- PostgreSQL (configured in settings)
- Whitenoise, django-cors-headers, django-debug-toolbar

## Project Structure

```text
api/                  # API router registration and auth/payment route wiring
users/                # Custom user model + serializers + manager
tuition/              # Tuition model, serializer, filters, pagination, payment handlers
applications/         # Applications, enrollments, topics, assignments, reviews, payment/wallet/invoice
tuition_media/        # Django settings, root URLs, WSGI/ASGI
manage.py
requirements.txt
```

## Prerequisites

- Python 3.10+
- PostgreSQL
- pip

## Local Setup

1. Clone and enter project

```bash
git clone https://github.com/Kamrul785/Tuition-Hub
cd Tuition-Hub
```

2. Create and activate virtual environment

```bash
python -m venv .tuition_env
# Windows PowerShell
.\.tuition_env\Scripts\Activate.ps1
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create `.env` in project root

```env
# Database (required)
dbname=your_db_name
user=your_db_user
password=your_db_password
host=localhost
port=5432

# Email (required by djoser activation/reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_USE_TLS=True
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_app_password

# Frontend/backend URLs used in djoser + payment redirects
FRONTEND_PROTOCOL=https
FRONTEND_DOMMAIN=your-frontend-domain.com
FRONTEND_URL=https://your-frontend-domain.com
BACKEND_URL=http://127.0.0.1:8000
```

5. Run migrations and create superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Start development server

```bash
python manage.py runserver
```

## Important Configuration Notes

- `DEBUG` is currently `False` in `settings.py`.
- Database is configured for PostgreSQL (not SQLite).
- Default DRF permission is `IsAuthenticated`; some endpoints override this.
- JWT header type is `JWT`, so use:

```http
Authorization: JWT <access_token>
```

- Djoser activation email is enabled (`SEND_ACTIVATION_EMAIL=True`).
- Code expects `FRONTEND_DOMMAIN` (double `MM`) because that exact variable name is used in settings.

## Base URLs

- API base: `http://127.0.0.1:8000/api/v1/`
- Swagger: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`
- Admin: `http://127.0.0.1:8000/admin/`

## Auth Endpoints

- `POST /api/v1/auth/users/` register
- `POST /api/v1/auth/jwt/create/` obtain access/refresh
- `POST /api/v1/auth/jwt/refresh/` refresh access token
- `GET /api/v1/auth/users/me/` current user
- `POST /api/v1/auth/users/set_password/` change password
- Djoser activation/reset routes are also available under `/api/v1/auth/`

## API Endpoints (By Resource)

### Tuitions

- `GET /api/v1/tuitions/`
- `POST /api/v1/tuitions/` (Tutor only)
- `GET /api/v1/tuitions/{id}/`
- `PUT/PATCH /api/v1/tuitions/{id}/` (owner tutor)
- `DELETE /api/v1/tuitions/{id}/` (owner tutor)

Supported query options:

- `class_level__icontains`
- `subject__icontains`
- `tutor`
- `search` across `title, description, subject, class_level`
- `ordering` by `created_at, class_level`
- pagination page size is `10`

### Applications

- `GET /api/v1/applications/`
- `POST /api/v1/applications/` (role `User` only)
- `GET /api/v1/applications/{id}/`
- `POST /api/v1/applications/{id}/select/` (Tutor accepts, creates enrollment)

### Enrollments

- `GET /api/v1/enrollments/`
- `GET /api/v1/enrollments/{id}/`
- `PATCH /api/v1/enrollments/{id}/` (student can update only `payment_verified`)
- `GET /api/v1/enrollments/{id}/progress/`

Nested under enrollments:

- `GET/POST /api/v1/enrollments/{enrollment_pk}/topics/`
- `GET/PATCH/DELETE /api/v1/enrollments/{enrollment_pk}/topics/{id}/`
- `GET/POST /api/v1/enrollments/{enrollment_pk}/assignments/`
- `GET/PATCH/DELETE /api/v1/enrollments/{enrollment_pk}/assignments/{id}/`

### Reviews

- `GET /api/v1/reviews/`
- `POST /api/v1/reviews/` (must be enrolled student)
- `GET/PATCH/DELETE /api/v1/reviews/{id}/`

### Payments

- `GET/POST /api/v1/payments/`
- `GET /api/v1/payments/{id}/`
- `GET /api/v1/payments/my_payments/`

Gateway flow endpoints:

- `POST /api/v1/payment/initiate/` body: `{ "amount": <number>, "enrollment_id": <id> }`
- `POST/GET /api/v1/payment/success/`
- `POST/GET /api/v1/payment/fail/`
- `POST/GET /api/v1/payment/cancel/`

### Wallet

- `GET /api/v1/wallet/`
- `GET /api/v1/wallet/my_wallet/`
- `GET /api/v1/wallet/earnings/`

### Invoices

- `GET /api/v1/invoices/`
- `GET /api/v1/invoices/{id}/`
- `GET /api/v1/invoices/my_invoices/`

## Core Data Model

- `users.User`: custom auth model with `email` as username, `role`, `address`, `phone_number`
- `tuition.Tuition`: tutor-owned tuition posts with optional paid fields (`is_paid`, `price`)
- `applications.Application`: student applications with status (`PENDING/ACCEPTED/REJECTED`)
- `applications.Enrollment`: accepted student-tuition link + `payment_verified`
- `applications.Topic` and `applications.Assignment`: nested academic progress units
- `applications.Review`: one review per student per tuition
- `applications.Payment`: one-to-one with enrollment + status and transaction metadata
- `applications.TutorWallet`: tutor earnings ledger fields
- `applications.Invoice`: one-to-one with payment

## Role and Access Rules

- Public: tuition list/retrieve
- `User` role: can apply for tuition and see own applications/enrollments/payments/invoices
- `Tutor` role: can create/manage own tuitions, accept applications, manage topics/assignments
- Reviews: only enrolled students can create review; one per tuition per student
- Payment, wallet, and invoice list endpoints are role-filtered

## Sample Requests

Register:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "StrongPass123!",
    "role": "User",
    "address": "Dhaka",
    "phone_number": "01700000000"
  }'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "StrongPass123!"}'
```

Create tuition (Tutor token):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tuitions/ \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Higher Math Batch",
    "description": "Weekly higher math classes",
    "subject": "Math",
    "class_level": "HSC",
    "availability": true,
    "is_paid": true,
    "price": "1500.00"
  }'
```

Initiate payment:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payment/initiate/ \
  -H "Authorization: JWT <student_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": "1500.00", "enrollment_id": 1}'
```

## Known Gaps / Risks

- SSLCommerz credentials are hardcoded in `tuition/views.py`; move to environment variables for security.
- `DEBUG=False` may complicate local development unless explicitly changed.
- Wallet credit logic in payment success handler is commented out.
- No meaningful automated tests are currently implemented.

## Development Commands

```bash
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser
python manage.py test
```

### Debug Mode
The project includes Django Debug Toolbar for development. Access it at `/__debug__/` when `DEBUG=True`.

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Shell access
python manage.py shell
```

## 🚀 Deployment

1. Set `DEBUG=False` in production
2. Configure proper database (PostgreSQL recommended)
3. Set up proper email backend for notifications
4. Configure static files serving
5. Use environment variables for sensitive settings
6. Set up proper CORS headers if needed for frontend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, email kamrulkhan526785@gmail.com or create an issue in the repository.

---

**TuitionHub** - Connecting Knowledge Seekers with Knowledge Providers 🎓