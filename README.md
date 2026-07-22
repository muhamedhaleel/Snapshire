# 📸 SnapsHire API

A RESTful backend API for **SnapsHire**, a photographer booking platform that enables users to discover photographers, book photography sessions, manage bookings, and handle payments through a secure and scalable backend.

The project is built with **Python**, **Django**, and **Django REST Framework**, following REST API best practices with role-based access for **Users**, **Photographers**, and **Administrators**.

---

# ✨ Features

## 👤 User

* User Registration
* User Login & Logout (JWT Authentication)
* User Profile Management
* Browse Photographer Profiles
* Search & Filter Photographers
* View Photographer Portfolio
* Book Photography Sessions
* View Booking History
* Cancel Bookings

---

## 📷 Photographer

* Photographer Registration
* Photographer Profile Management
* Portfolio Management
* Availability Management
* Booking Management
* Earnings Dashboard

---

## 🛠️ Administrator

* Manage Users
* Manage Photographers
* Verify Photographer Accounts
* Manage Bookings
* Manage Payments
* Manage Promotional Banners
* Dashboard Statistics

---

# 🛠️ Technology Stack

* Python 3
* Django
* Django REST Framework
* MySQL
* JWT Authentication
* Swagger (drf-yasg)
* Git
* GitHub

---

# 📁 Project Structure

```text
SnapsHire/
│
├── accounts/          # Authentication & authorization
├── users/             # User management
├── photographers/     # Photographer management
├── bookings/          # Booking management
├── payments/          # Payment management
├── dashboard/         # Admin dashboard
├── media/             # Uploaded media files
├── static/            # Static assets
├── config/            # Project configuration
├── manage.py
└── requirements.txt
```

---

# 🔐 Authentication

The API uses **JSON Web Token (JWT)** authentication to secure protected endpoints.

Authentication includes:

* Access Token
* Refresh Token
* Protected API Endpoints
* Role-Based Authorization

---

# 📖 API Documentation

Interactive API documentation is available through **Swagger UI**, allowing developers to explore and test API endpoints directly from the browser.

---

# 📦 Main Modules

* Authentication
* User Management
* Photographer Management
* Portfolio Management
* Booking Management
* Payment Management
* Admin Dashboard

---

# 🔒 Security Features

* JWT Authentication
* Password Hashing
* Role-Based Authorization
* Request Validation
* Secure File Uploads
* Protected REST API Endpoints

---

# 📊 Project Status

**Status:** 🟢 Active Development

## ✅ Completed

* JWT Authentication
* User & Photographer Registration
* Role-Based Authentication & Authorization
* User Profile Management
* Photographer Profile Management
* Portfolio Management
* Search & Filter Photographers
* Booking Management
* Payment Records Management
* Admin Dashboard
* Photographer Verification
* Banner Management
* Swagger API Documentation

## 🚧 In Progress

* Recurring Booking System
* Photographer Availability & Scheduling
* Booking Conflict Prevention
* Booking Cancellation & Refund Policy
* Payment Gateway Integration

## 📅 Planned

* Email Notifications
* Reviews & Ratings
* Wishlist
* Real-Time Chat
* Push Notifications
* React Frontend
* Docker Deployment
* CI/CD Pipeline
* Unit & Integration Testing

---

# 🚀 Getting Started

### Clone the Repository

```bash
git clone https://github.com/your-username/snapshire.git
cd snapshire
```

### Create a Virtual Environment

```bash
python -m venv venv
```

### Activate the Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file and configure your database and secret key.

### Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run the Development Server

```bash
python manage.py runserver
```

The API will be available at:

```
http://127.0.0.1:8000/
```

Swagger documentation:

```
http://127.0.0.1:8000/swagger/
```

---

#

