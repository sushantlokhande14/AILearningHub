# AI Learning Hub

AI Learning Hub is a web-based platform that aggregates AI-related content including GitHub repositories, research papers, online courses, and peer articles. It also features an interactive AI chatbot powered by OpenAI. This project is built with Flask, SQLAlchemy, and Bootstrap, and leverages several external APIs and web scrapers to gather dynamic content.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [APIs & Web Scrapers](#apis--web-scrapers)
- [Database Design](#database-design)
- [Usage](#usage)
- [License](#license)

---

## Features

- **User Authentication:** Sign up, login, logout, and a personalized user dashboard.
- **Content Aggregation:**
  - **GitHub Repositories:** Fetch and display popular Python-based AI repositories.
  - **Research Papers:** Aggregate AI research papers from arXiv, Papers With Code, and Google Scholar.
  - **Courses:** List and filter online AI courses from a CSV file.
  - **Peer Articles:** Submit and review peer articles.
- **Content Management:** Save favorite content (repositories, papers, courses) and manage your saved items.
- **AI Chatbot:** Interactive chatbot powered by OpenAI’s API.
- **Admin Panel:** Admin users can review, approve, or reject submitted peer articles.
- **Responsive UI:** Built using Bootstrap and custom CSS for an engaging and responsive user experience.

---

## Tech Stack

- **Backend Framework:** Flask  
  A lightweight, Python-based web framework used for routing, templating (via Jinja2), and session management.

- **Database & ORM:** SQLAlchemy with SQLite  
  - **SQLite:** A lightweight, file-based relational database that stores data in a single file (`app.db`).
  - **SQLAlchemy:** An Object Relational Mapper (ORM) that lets you interact with the SQLite database using Python classes instead of raw SQL.

- **Frontend:** HTML, CSS, and JavaScript  
  - **HTML & Jinja2:** For dynamic content rendering.
  - **CSS & Bootstrap 4:** For responsive, mobile-friendly design.
  - **JavaScript:** To enhance interactivity (e.g., read-more toggles, chat functionality).

- **APIs & Web Scrapers:**  
  - **GitHub API:** Fetches popular AI repositories.
  - **arXiv API:** Retrieves research papers via XML feeds processed with feedparser.
  - **Papers With Code API:** Supplies additional research paper data focused on AI implementations.
  - **Google Scholar:** Integrated via the scholarly library for academic paper search.
  - **OpenAI API:** Powers the AI chatbot feature.
  - **BeautifulSoup:** Used for scraping and processing data (e.g., course details).

- **Other Libraries:**  
  - **Flask-Login:** Manages user sessions and authentication.
  - **python-dotenv:** Loads environment variables for configuration.
  - **Werkzeug:** Provides security features like password hashing.

---

## Project Structure

```
AI-Learning-Hub/
│
├── app.py                  # Main Flask application with routes, models, and logic.
├── config.py               # Configuration file with settings like SECRET_KEY, SQLALCHEMY_DATABASE_URI, and COURSES_CSV_PATH.
├── courses.csv             # CSV file containing course information.
├── requirements.txt        # List of required Python packages and their versions.
├── style.css               # Custom CSS file for additional styling.
│
├── templates/              # HTML templates for the web pages.
│   ├── base.html           # Base template containing the header, navigation bar, and footer.
│   ├── index.html          # Landing page for the website.
│   ├── login.html          # Login form.
│   ├── signup.html         # Signup form.
│   ├── user_dashboard.html # Dashboard for logged-in users.
│   ├── github_repos.html   # Displays GitHub repositories.
│   ├── research_papers.html# Displays AI research papers.
│   ├── courses.html        # Courses listing page with filtering.
│   ├── saved_content.html  # Saved content view for repositories, papers, and courses.
│   ├── peer_articles.html  # Public view for approved peer articles.
│   ├── submit_article.html # Form to submit new peer articles.
│   ├── admin_articles.html # Admin panel to review and manage peer articles.
│   └── chat.html           # Chat interface for interacting with the AI chatbot.
│
└── static/
    └── images/             # Contains background images and other static assets.
```

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/AI-Learning-Hub.git
   cd AI-Learning-Hub
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Variables

Create a `.env` file in the project root directory with the following content:

```env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
COURSES_CSV_PATH=path/to/courses.csv
```

- **SECRET_KEY:** Used for session management and security.
- **OPENAI_API_KEY:** Your API key for accessing OpenAI services.
- **COURSES_CSV_PATH:** (Optional) If not set, it defaults to `courses.csv` in the project directory.

---

## Running the Application

1. **Activate the Virtual Environment (if using one):**

   ```bash
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

2. **Run the Flask Application:**

   ```bash
   python app.py
   ```

3. **Access the Application:**

   Open your web browser and navigate to:  
   `http://localhost:5000`

---

## APIs & Web Scrapers

- **GitHub API:**  
  Fetches popular Python-based AI repositories based on user-defined search queries.

- **arXiv API:**  
  Retrieves AI research papers. The XML feeds are parsed using feedparser to extract details like title, authors, and summaries.

- **Papers With Code API:**  
  Provides additional research paper data with a focus on code implementation in AI projects.

- **Google Scholar (via scholarly):**  
  Scrapes academic papers related to AI and normalizes the data for display.

- **OpenAI API:**  
  Powers the AI chatbot that users can interact with, providing intelligent responses to queries.

- **BeautifulSoup:**  
  Used for web scraping, particularly for cleaning and processing data such as course details from a CSV file.

---

## Database Design

The project uses a single SQLite database (`app.db`) managed via SQLAlchemy.

- **Users Table:**  
  - **Purpose:** Stores user credentials (username, password hash) and roles (admin or user).

- **SavedItems Table:**  
  - **Purpose:** Saves various content types (repositories, papers, courses) along with metadata like title, URL, save date, and course status.

- **PeerArticles Table:**  
  - **Purpose:** Holds peer article submissions with details including title, description, keywords, URL, submission date, and status (waiting, approved, or rejected).

- **(Optional) Comments Table:**  
  - **Purpose:** Can be added to store user comments on saved items or peer articles.

Each table is defined as a Python class using SQLAlchemy, which abstracts database operations and lets you work with data as Python objects.

---

## Usage

- **User Authentication:**  
  - New users can sign up via the `/signup` route.
  - Existing users can log in via the `/login` route and access their dashboard.

- **Content Discovery:**  
  - **GitHub Repositories:** Visit `/github_repos` to search and view AI repositories.
  - **Research Papers:** Navigate to `/research_papers` to browse AI research papers from multiple sources.
  - **Courses:** Check out `/courses` to view and filter available AI courses.
  - **Peer Articles:** Public peer articles are available at `/peer_articles`, and users can submit their own articles via `/submit_article`.

- **Saved Content:**  
  Logged-in users can save repositories, papers, and courses. View saved items on the `/saved_content` page.

- **Admin Functionality:**  
  Admin users can review and manage submitted peer articles on the `/admin/articles` page.

- **AI Chatbot:**  
  Interact with our AI chatbot via the `/chat` page, which uses the OpenAI API to generate responses based on your input.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Happy Learning!*
