"""
Sentiment Analysis System - Flask Application (MySQL Version)
CP 212 System Analysis and Design
Supports English and Swahili text classification
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
import csv
from sentiment_engine import SentimentAnalyzer
from database import Database

app = Flask(__name__)
app.secret_key = 'cp212_sentiment_analysis_secret_key_2026'

# Initialize sentiment analyzer
analyzer = SentimentAnalyzer()

# Initialize database connection
db = Database()


# ═══════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Landing page - redirects to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validate input
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')

        # Check credentials against MySQL database
        user = db.get_user_by_username_or_email(username)

        if user and check_password_hash(user['password_hash'], password):
            # Successful login
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            # Update last login timestamp in DB
            db.update_last_login(user['user_id'])

            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        fullname         = request.form.get('fullname', '').strip()
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # --- Validation ---
        errors = []

        if not all([fullname, username, email, password, confirm_password]):
            errors.append('All fields are required')

        if len(username) < 3:
            errors.append('Username must be at least 3 characters')

        if '@' not in email or '.' not in email:
            errors.append('Invalid email format')

        if password != confirm_password:
            errors.append('Passwords do not match')

        if len(password) < 6:
            errors.append('Password must be at least 6 characters')

        # Check for duplicate username / email via database
        if not errors:
            if db.get_user_by_username_or_email(username):
                errors.append('Username already exists')
            elif db.get_user_by_username_or_email(email):
                errors.append('Email already registered')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')

        # Create user in MySQL database
        user_id = db.create_user(
            fullname=fullname,
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        if user_id:
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error creating account. Please try again.', 'danger')

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
def dashboard():
    """Main dashboard - text submission and stats overview"""
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Pull statistics from MySQL
    stats_data = db.get_user_statistics(user_id)

    # Normalise None values that MySQL SUM() returns when table is empty
    stats = {
        'today_count': stats_data['today_count'] or 0,
        'total_count': stats_data['total_analyses'] or 0,
        'sentiment_counts': {
            'Positive': stats_data['positive_count'] or 0,
            'Negative': stats_data['negative_count'] or 0,
            'Neutral':  stats_data['neutral_count']  or 0,
        }
    }

    return render_template('dashboard.html', stats=stats)


@app.route('/analyze', methods=['POST'])
def analyze():
    """Process text and return sentiment analysis result as JSON"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id  = session['user_id']

    # Get text from form
    text_content = request.form.get('text_content', '').strip()
    language     = request.form.get('language', 'Auto')

    # Handle optional file upload
    if 'text_file' in request.files:
        file = request.files['text_file']
        if file and file.filename.endswith('.txt'):
            text_content = file.read().decode('utf-8').strip()

    # Validate
    if not text_content:
        return jsonify({'error': 'Please enter some text before analyzing'}), 400

    if len(text_content) > 5000:
        return jsonify({'error': 'Text exceeds maximum length of 5000 characters'}), 400

    # Run sentiment analysis engine
    result = analyzer.analyze(text_content, language)

    # Persist result in MySQL
    analysis_id = db.create_analysis(
        user_id=user_id,
        text_content=text_content,
        language=result['language'],
        sentiment_result=result['sentiment'],
        confidence_score=result['confidence']
    )

    if not analysis_id:
        return jsonify({'error': 'Failed to save analysis. Please try again.'}), 500

    return jsonify({
        'success': True,
        'result': {
            'sentiment':    result['sentiment'],
            'confidence':   round(result['confidence'] * 100, 1),
            'language':     result['language'],
            'text_preview': text_content[:100] + '...' if len(text_content) > 100 else text_content
        }
    })


@app.route('/history')
def history():
    """Display user's analysis history with filtering and pagination"""
    if 'user_id' not in session:
        flash('Please login to view history', 'warning')
        return redirect(url_for('login'))

    user_id          = session['user_id']
    filter_sentiment = request.args.get('filter', 'All')
    search_query     = request.args.get('search', '').strip()
    page             = int(request.args.get('page', 1))
    per_page         = 20

    # Paginated results from MySQL
    paginated_analyses = db.get_user_analyses(
        user_id=user_id,
        sentiment_filter=filter_sentiment,
        search_query=search_query,
        page=page,
        per_page=per_page
    )

    # Total count for pagination controls
    total_analyses = db.get_user_analyses_count(
        user_id=user_id,
        sentiment_filter=filter_sentiment,
        search_query=search_query
    )
    total_pages = max(1, (total_analyses + per_page - 1) // per_page)

    # Sidebar summary counts (always full dataset, ignoring active filter)
    stats_data = db.get_user_statistics(user_id)
    summary = {
        'positive': stats_data['positive_count'] or 0,
        'negative': stats_data['negative_count'] or 0,
        'neutral':  stats_data['neutral_count']  or 0,
    }

    return render_template('history.html',
                           analyses=paginated_analyses,
                           filter=filter_sentiment,
                           search=search_query,
                           page=page,
                           total_pages=total_pages,
                           summary=summary)


@app.route('/export_csv')
def export_csv():
    """Export analysis history to a downloadable CSV file"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id          = session['user_id']
    filter_sentiment = request.args.get('filter', 'All')

    # Fetch ALL matching records (no real pagination limit) from MySQL
    user_analyses = db.get_user_analyses(
        user_id=user_id,
        sentiment_filter=filter_sentiment,
        search_query='',
        page=1,
        per_page=999999
    )

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date/Time', 'Text Preview', 'Language', 'Sentiment', 'Confidence %'])

    for analysis in user_analyses:
        text_preview = (analysis['text_content'][:50] + '...'
                        if len(analysis['text_content']) > 50
                        else analysis['text_content'])

        ts = analysis['timestamp']
        if isinstance(ts, datetime):
            ts = ts.strftime('%Y-%m-%d %H:%M:%S')

        writer.writerow([
            ts,
            text_preview,
            analysis['language'],
            analysis['sentiment_result'],
            round(float(analysis['confidence_score']) * 100, 1)
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='sentiment_history.csv'
    )


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile - view info and update settings"""
    if 'user_id' not in session:
        flash('Please login to view profile', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        action = request.form.get('action')

        # Always fetch fresh user data from DB before acting on it
        user = db.get_user_by_id(user_id)

        if action == 'update_info':
            fullname = request.form.get('fullname', '').strip()
            email    = request.form.get('email', '').strip()

            if fullname and email and '@' in email:
                if db.update_user_profile(user_id, fullname, email):
                    flash('Profile updated successfully', 'success')
                else:
                    flash('Error updating profile. Please try again.', 'danger')
            else:
                flash('Please provide a valid name and email.', 'danger')

        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new  = request.form.get('confirm_new_password', '')

            if check_password_hash(user['password_hash'], old_password):
                if new_password == confirm_new and len(new_password) >= 6:
                    if db.update_password(user_id, generate_password_hash(new_password)):
                        flash('Password changed successfully', 'success')
                    else:
                        flash('Error changing password. Please try again.', 'danger')
                else:
                    flash('New passwords do not match or are too short (min 6 characters)', 'danger')
            else:
                flash('Incorrect old password', 'danger')

        return redirect(url_for('profile'))

    # GET - load fresh profile data from MySQL
    user       = db.get_user_by_id(user_id)
    stats_data = db.get_user_statistics(user_id)
    stats = {
        'total_analyses': stats_data['total_analyses'] or 0,
        'positive_count': stats_data['positive_count'] or 0,
        'negative_count': stats_data['negative_count'] or 0,
        'neutral_count':  stats_data['neutral_count']  or 0,
    }

    return render_template('profile.html', user=user, stats=stats)


# ═══════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Seed demo account on every startup
    # create_demo_data() skips creation automatically if the user already exists
    db.create_demo_data(generate_password_hash('demo123'))

    print("\n" + "=" * 60)
    print("  SENTIMENT ANALYSIS SYSTEM - MYSQL VERSION")
    print("  CP 212 System Analysis and Design")
    print("=" * 60)
    print("\n🚀 Server starting...")
    print("📍 URL: http://localhost:5000")
    print("💾 Database: MySQL (sentiment_analysis)")
    print("\n👤 Demo Account:")
    print("   Username: demo")
    print("   Password: demo123")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)