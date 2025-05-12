# Anki Backend (Django + FastAPI)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-ORM-darkgreen?logo=django&logoColor=white)](https://djangoproject.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-API%20Routes-darkblue?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

This is the backend for an Anki-like spaced repetition system designed to help users effectively memorize information.

The project uses two frameworks: Django (ORM) for database interaction and FastAPI for building API endpoints.

[![WIP](https://img.shields.io/badge/Status-αlpha-orange)](https://github.com/SergeiVasilyev/Anki_backend)




> **Note**  
> 🚧 This project is in an early **stage of development**.
> The architecture and API are subject to significant changes as:
> - Subject Matter Dives
> - Refactoring and optimizations
> - New features are added 


## 🔍 Key Features
- **Flexible Architecture**: Combines the strengths of Django ORM and FastAPI

- **Spaced Repetition Algorithm**: Calculates the optimal time to show a card again

- **Data Models**:

  - Sets (Sets of cards)
  - Flashcards (Card)
  - Learning
  - Friends
  - Likes
  - Sharing

- Authentication: JWT-based authentication via FastAPI


## 🛠 Tech Stack

- **Python 3.13**

- **Django ORM** – for database models and queries

- **FastAPI** – REST API endpoints

- **PostgreSQL** – primary database (can be easily replaced via Django ORM)

- **JWT** – authentication mechanism

- **Django Migrations** – database schema management


## 🚀 Getting Started

1. Clone the repository:
```bash
   git clone https://github.com/SergeiVasilyev/Anki_backend.git
   cd Anki_backend
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Build container 
```Bash
Docker-compose up --build
```




