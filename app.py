from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup  # Required for scraping courses
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # If a non-logged user tries to access a protected route, redirect to /login

# -------------------------
# MODELS
# -------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), default='user')  # can be 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SavedItem(db.Model):
    __tablename__ = 'saved_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(50))  # 'repo', 'paper', or 'course'
    title = db.Column(db.String(300))
    url = db.Column(db.String(300))
    date_saved = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    published = db.Column(db.String(100))  # used for papers or course description
    authors = db.Column(db.String(300))    # for papers
    journal_ref = db.Column(db.String(300))# for papers
    # New field for course progress; for courses only.
    course_status = db.Column(db.String(20), nullable=True)  # e.g., 'ongoing', 'completed'
    user = db.relationship('User', backref='saved_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------
# CREATE TABLES ON START
# -------------------------
with app.app_context():
    db.create_all()

# -------------------------
# ROUTES
# -------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ---- SIGNUP & LOGIN ----
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another.', 'danger')
            return redirect(url_for('signup'))
        
        # Create new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ---- USER DASHBOARD ----
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html', username=current_user.username)

# ---- GITHUB REPOS ----
def get_github_ai_repos(search_query="AI", order="desc", per_page=15, page=1):
    """
    Searches GitHub for popular Python-based AI repositories.
    Wrap search_query in quotes for exact match if it's not the default.
    """
    if search_query != "AI":
        search_query = f'"{search_query}"'
        
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{search_query}+language:Python",
        "sort": "stars",
        "order": order,
        "per_page": per_page,
        "page": page
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("items", []), data.get("total_count", 0)
    else:
        print("Error fetching GitHub repos:", response.status_code)
        return [], 0

@app.route('/github_repos')
def github_repos():
    search_query = request.args.get("search", "AI")
    order = request.args.get("order", "desc")
    page = int(request.args.get("page", 1))
    per_page = 15

    repos, total_count = get_github_ai_repos(search_query=search_query, order=order, per_page=per_page, page=page)
    return render_template('github_repos.html',
                           repos=repos,
                           search_query=search_query,
                           order=order,
                           page=page,
                           per_page=per_page,
                           total_count=total_count)

@app.route('/save_repo', methods=['POST'])
@login_required
def save_repo():
    """
    Saves the selected GitHub repository to the user's SavedItem table.
    """
    repo_title = request.form.get('repo_name')  # using repo name as title
    repo_url = request.form.get('repo_url')  # this must match your form name

    # Check if already saved (for type 'repo')
    existing_item = SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type='repo',
        url=repo_url
    ).first()
    if existing_item:
        flash('Repo already saved.', 'info')
        return redirect(request.referrer or url_for('github_repos'))

    new_item = SavedItem(
        user_id=current_user.id,
        item_type='repo',
        title=repo_title,
        url=repo_url
    )
    db.session.add(new_item)
    db.session.commit()
    flash('Repo saved successfully!', 'success')
    return redirect(request.referrer or url_for('github_repos'))

# ---- SAVED CONTENT ----

@app.route('/saved_content')
@login_required
def saved_content():
    tab = request.args.get('tab', 'repos')  # 'repos', 'papers', 'courses'
    sort_order = request.args.get('sort', 'recent')  # 'recent' or 'old'
    course_status_filter = request.args.get('course_status', 'all')  # 'all', 'ongoing', 'completed'

    # 1) Sort logic
    if sort_order == 'old':
        papers = SavedItem.query.filter_by(user_id=current_user.id, item_type='paper') \
                                .order_by(SavedItem.date_saved.asc()).all()
        repos = SavedItem.query.filter_by(user_id=current_user.id, item_type='repo') \
                                .order_by(SavedItem.date_saved.asc()).all()
        courses = SavedItem.query.filter_by(user_id=current_user.id, item_type='course') \
                                 .order_by(SavedItem.date_saved.asc()).all()
    else:
        papers = SavedItem.query.filter_by(user_id=current_user.id, item_type='paper') \
                                .order_by(SavedItem.date_saved.desc()).all()
        repos = SavedItem.query.filter_by(user_id=current_user.id, item_type='repo') \
                                .order_by(SavedItem.date_saved.desc()).all()
        courses = SavedItem.query.filter_by(user_id=current_user.id, item_type='course') \
                                 .order_by(SavedItem.date_saved.desc()).all()

    # 2) Filter courses by status
    if course_status_filter != 'all':
        courses = [c for c in courses if c.course_status == course_status_filter]

    return render_template(
        'saved_content.html',
        papers=papers,
        repos=repos,
        courses=courses,
        sort_order=sort_order,
        tab=tab,
        course_status_filter=course_status_filter
    )

@app.route('/unsave/<int:item_id>', methods=['POST'])
@login_required
def unsave_item(item_id):
    item = SavedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to remove this item.', 'danger')
        return redirect(url_for('saved_content'))
    
    # Determine which tab to show after removing
    tab_to_show = 'repos'
    if item.item_type == 'paper':
        tab_to_show = 'papers'
    elif item.item_type == 'course':
        tab_to_show = 'courses'
        
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from your saved content.', 'success')
    return redirect(url_for('saved_content', tab=tab_to_show))

# ---- RESEARCH PAPERS ----
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

def get_arxiv_papers(query="artificial intelligence", max_results=5, start=0):
    base_url = "http://export.arxiv.org/api/query?"
    safe_q = quote_plus(query)
    query_params = f"search_query=all:{safe_q}&start={start}&max_results={max_results}"
    url = base_url + query_params
    feed = feedparser.parse(url)
    papers = []
    total_results = int(feed.feed.get('opensearch_totalresults', 0))
    for entry in feed.entries:
        paper = {
            "title": entry.title,
            "published": entry.published,
            "authors": ", ".join(author.name for author in entry.authors),
            "summary": entry.summary,
            "link": entry.link,
            "journal_ref": entry.get("arxiv_journal_ref", "N/A")
        }
        papers.append(paper)
    return papers, total_results

def get_paperswithcode_papers(query="artificial intelligence", page_size=5):
    url = "https://paperswithcode.com/api/v1/papers/"
    params = {
        "q": query,
        "page_size": page_size
    }
    response = requests.get(url, params=params)
    papers = []
    total_results = 0
    if response.status_code == 200:
        data = response.json()
        total_results = data.get("count", 0)
        for result in data.get("results", []):
            paper = {
                "title": result.get("title", "No title"),
                "published": result.get("published", "N/A"),
                "authors": result.get("authors", "N/A"),
                "summary": result.get("abstract", "No abstract"),
                "link": result.get("paper_url", "#"),
                "journal_ref": result.get("journal_ref", "N/A")
            }
            papers.append(paper)
    else:
        print("Error fetching Papers With Code:", response.status_code)
    return papers, total_results

def get_google_scholar_papers(query="artificial intelligence", max_results=5):
    try:
        from scholarly import scholarly
    except ImportError:
        print("scholarly not installed. Please install it using pip install scholarly")
        return [], 0
    search_query = scholarly.search_pubs(query)
    papers = []
    for i in range(max_results):
        try:
            paper = next(search_query)
            papers.append({
                "title": paper.get("bib", {}).get("title", "No title"),
                "published": paper.get("bib", {}).get("pub_year", "N/A"),
                "authors": paper.get("bib", {}).get("author", "N/A"),
                "summary": paper.get("bib", {}).get("abstract", "No abstract"),
                "link": paper.get("pub_url", "#"),
                "journal_ref": paper.get("bib", {}).get("journal", "N/A")
            })
        except StopIteration:
            break
    total_results = len(papers)
    return papers, total_results

@app.route('/research_papers')
def research_papers():
    search_query = request.args.get("search", "AI")
    source = request.args.get("source", "gs")  # default "gs" for Google Scholar
    page = int(request.args.get("page", 1))
    max_results = 10

    papers = []
    total_count = None

    if source in ["arxiv", "all"]:
        start = (page - 1) * max_results
        arxiv_papers, arxiv_total = get_arxiv_papers(query=search_query, max_results=max_results, start=start)
        for paper in arxiv_papers:
            paper["source"] = "arxiv"
        papers.extend(arxiv_papers)
        if source == "arxiv":
            total_count = arxiv_total

    if source in ["pwc", "all"]:
        pwc_papers, pwc_total = get_paperswithcode_papers(query=search_query, page_size=max_results)
        for paper in pwc_papers:
            paper["source"] = "pwc"
        papers.extend(pwc_papers)
        if source == "pwc":
            total_count = pwc_total

    if source in ["gs", "google", "all"]:
        gs_papers, gs_total = get_google_scholar_papers(query=search_query, max_results=max_results)
        for paper in gs_papers:
            paper["source"] = "google"
        papers.extend(gs_papers)
        if source in ["gs", "google"]:
            total_count = gs_total

    if source == "all":
        total_count = len(papers)

    return render_template("research_papers.html",
                           papers=papers,
                           search_query=search_query,
                           source=source,
                           page=page,
                           max_results=max_results,
                           total_count=total_count)

@app.route('/save_paper', methods=['POST'])
@login_required
def save_paper():
    title = request.form.get('title')
    url = request.form.get('url')
    published = request.form.get('published')
    authors = request.form.get('authors')
    journal_ref = request.form.get('journal_ref')

    # Use title as uniqueness check for papers
    existing_item = SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type='paper',
        title=title
    ).first()
    if existing_item:
        flash('Paper already saved.', 'info')
        return redirect(request.referrer or url_for('research_papers'))

    new_item = SavedItem(
        user_id=current_user.id,
        item_type='paper',
        title=title,
        url=url,
        published=published,
        authors=authors,
        journal_ref=journal_ref
    )
    db.session.add(new_item)
    db.session.commit()
    flash('Paper saved successfully!', 'success')
    return redirect(request.referrer or url_for('research_papers'))

import csv
import os
from config import Config  # to use 'COURSES_CSV_PATH'

# ---- COURSES (CSV) ----

@app.route('/courses')
def courses():
    courses_list = []
    all_tags_set = set()  # collect all tags from the entire CSV
    path_to_csv = Config.COURSES_CSV_PATH
    tag_filter = request.args.get("tag", "all").lower()

    try:
        with open(path_to_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                row['index'] = idx
                courses_list.append(row)
                tag = row.get("Tag", "").strip()
                if tag:
                    all_tags_set.add(tag)
    except Exception as e:
        print("Error reading courses.csv:", e)

    all_tags = sorted(all_tags_set, key=str.lower)

    # Define user_course_titles so the template can reference it
    user_course_titles = set()
    if current_user.is_authenticated:
        user_courses = SavedItem.query.filter_by(
            user_id=current_user.id,
            item_type='course'
        ).all()
        user_course_titles = {c.title for c in user_courses}

    # Then apply the filter to courses_list
    if tag_filter != "all":
        courses_list = [c for c in courses_list if c.get("Tag", "").lower() == tag_filter]

    return render_template(
        "courses.html",
        courses=courses_list,
        user_course_titles=user_course_titles,  # pass it here
        all_tags=all_tags,
        current_tag=tag_filter
    )

@app.route('/start_course/<int:course_index>')
def start_course(course_index):
    try:
        path_to_csv = Config.COURSES_CSV_PATH  # Use the same config variable
        with open(path_to_csv, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                if idx == course_index:
                    course = row
                    break
            else:
                flash("Course not found.", "danger")
                return redirect(url_for('courses'))
    except Exception as e:
        print("Error in /start_course route:", e)
        flash("Error reading courses.", "danger")
        return redirect(url_for('courses'))
    
    # For non-logged-in users, you might skip saving the course or handle it differently.
    if current_user.is_authenticated:
        existing_item = SavedItem.query.filter_by(
            user_id=current_user.id,
            item_type='course',
            title=course['Title']
        ).first()
        if not existing_item:
            new_item = SavedItem(
                user_id=current_user.id,
                item_type='course',
                title=course['Title'],
                url=course['URL'],
                published=course['Description'],
                course_status='ongoing'
            )
            db.session.add(new_item)
            db.session.commit()
        else:
            # If it exists, update its status to "ongoing"
            existing_item.course_status = 'ongoing'
            db.session.commit()
    
    # Redirect the user to the actual course URL.
    return redirect(course['URL'])

@app.route('/mark_complete/<int:item_id>', methods=['POST'])
@login_required
def mark_complete(item_id):
    item = SavedItem.query.get_or_404(item_id)
    if item.user_id != current_user.id or item.item_type != 'course':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('saved_content'))
    item.course_status = 'completed'
    db.session.commit()
    flash("Course marked as complete.", 'success')
    return redirect(url_for('saved_content', tab='courses'))

@app.route('/chat')
def chat():
    return render_template('chat.html')

from flask import jsonify  # Ensure jsonify is imported

import os
from flask import request, jsonify
from openai import OpenAI

# Securely load your OpenAI API key from the environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is missing! Set the environment variable OPENAI_API_KEY.")

client = OpenAI(api_key=OPENAI_API_KEY)

static_system_prompt = (
    "You are a helpful assistant with deep expertise in Artificial Intelligence, Machine Learning, "
    "Computer Science, and Technology. When addressing technical questions, provide detailed, domain-specific "
    "information. For casual greetings or non-technical inquiries, respond in a friendly and conversational tone."
)

@app.route('/chat/api', methods=['POST'])
def chat_api():
    # Retrieve the user message from the JSON payload
    user_message = request.json.get('message', '')
    
    try:
        # Call the OpenAI API with the static system prompt and the user's message
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            store=True,  # Optional: if you want to store the conversation
            messages=[
                {"role": "system", "content": static_system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        # Extract the generated message from the API response
        bot_reply = completion.choices[0].message.content
    except Exception as e:
        bot_reply = "Sorry, an error occurred: " + str(e)
    
    # Return the bot's reply as a JSON response
    return jsonify({'reply': bot_reply})

# -------------------------
# PEER ARTICLES
# -------------------------
class PeerArticle(db.Model):
    __tablename__ = 'peer_articles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(100))
    email = db.Column(db.String(100))
    title = db.Column(db.String(300))
    description = db.Column(db.Text)
    keywords = db.Column(db.String(300))
    url = db.Column(db.String(300))
    date_submitted = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='waiting')  # waiting, approved, rejected
    admin_note = db.Column(db.Text, nullable=True)

User.articles = db.relationship('PeerArticle', backref='author', lazy=True)

with app.app_context():
    db.create_all()
    # Create default admin if not exists
    admin_user = User.query.filter_by(username='admin@123').first()
    if not admin_user:
        admin_user = User(username='admin@123', role='admin')
        admin_user.set_password('1234')
        db.session.add(admin_user)
        db.session.commit()

# Public view for approved peer articles
@app.route('/peer_articles')
def peer_articles():
    articles = PeerArticle.query.filter_by(status='approved').order_by(PeerArticle.date_submitted.desc()).all()
    return render_template('peer_articles.html', articles=articles)

# Route for users to submit a new article
@app.route('/submit_article', methods=['GET', 'POST'])
@login_required
def submit_article():
    if request.method == 'POST':
        new_article = PeerArticle(
            user_id=current_user.id,
            name=request.form.get('name'),
            contact=request.form.get('contact'),
            email=request.form.get('email'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            keywords=request.form.get('keywords'),
            url=request.form.get('url'),
            status='waiting'
        )
        db.session.add(new_article)
        db.session.commit()
        flash('Article submitted successfully and is waiting for approval.', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('submit_article.html')

# Admin view for pending articles
@app.route('/admin/articles')
@login_required
def admin_articles():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    pending_articles = PeerArticle.query.filter_by(status='waiting').order_by(PeerArticle.date_submitted.desc()).all()
    return render_template('admin_articles.html', articles=pending_articles)

# Admin route to approve an article
@app.route('/admin/articles/approve/<int:article_id>', methods=['POST'])
@login_required
def approve_article(article_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    article = PeerArticle.query.get_or_404(article_id)
    article.status = 'approved'
    db.session.commit()
    flash('Article approved.', 'success')
    return redirect(url_for('admin_articles'))

# Admin route to reject an article
@app.route('/admin/articles/reject/<int:article_id>', methods=['POST'])
@login_required
def reject_article(article_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    article = PeerArticle.query.get_or_404(article_id)
    article.status = 'rejected'
    article.admin_note = request.form.get('admin_note')
    db.session.commit()
    flash('Article rejected.', 'info')
    return redirect(url_for('admin_articles'))

# User view to see their submitted articles and statuses
@app.route('/my_articles')
@login_required
def my_articles():
    articles = PeerArticle.query.filter_by(user_id=current_user.id).order_by(PeerArticle.date_submitted.desc()).all()
    return render_template('my_articles.html', articles=articles)

# -------------------------
# MAIN
# -------------------------
if __name__ == '__main__':
    app.run()
