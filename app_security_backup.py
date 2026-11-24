import os, re, csv, io, math, hashlib, secrets
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from sqlalchemy import func, desc, case

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # app remains usable without the optional ML dependency
    TfidfVectorizer = cosine_similarity = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(BASE_DIR / 'uploads', exist_ok=True)
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-only-change-this-secret-before-deployment'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', f"sqlite:///{(BASE_DIR / 'instance' / 'civictrack.db').as_posix()}"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    UPLOAD_FOLDER=str(BASE_DIR / 'uploads'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please sign in to access the officer workspace.'
csrf = CSRFProtect(app)

CATEGORIES = ['Pothole / Road Damage', 'Garbage / Illegal Dumping', 'Broken Streetlight', 'Water Leakage', 'Blocked Drain', 'Footpath / Accessibility', 'Other']
STATUSES = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
SEVERITIES = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='officer', nullable=False)
    active = db.Column(db.Boolean, default=True)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_code = db.Column(db.String(24), unique=True, nullable=False, index=True)
    citizen_name = db.Column(db.String(100), nullable=False)
    phone_last4 = db.Column(db.String(4), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(240), nullable=False)
    ward = db.Column(db.String(80), default='Not specified')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_filename = db.Column(db.String(255))
    severity = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(30), default='Submitted', index=True)
    priority_score = db.Column(db.Integer, default=0)
    priority_label = db.Column(db.String(20), default='Medium')
    duplicate_of_id = db.Column(db.Integer, db.ForeignKey('complaint.id'))
    verification_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    events = db.relationship('ComplaintEvent', backref='complaint', lazy=True, cascade='all, delete-orphan', order_by='ComplaintEvent.created_at')
    duplicate_of = db.relationship('Complaint', remote_side=[id], uselist=False)

class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    voter_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('complaint_id', 'voter_hash', name='uq_complaint_voter'),)

class ComplaintEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(500), default='')
    actor = db.Column(db.String(100), default='CivicTrack')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id): return db.session.get(User, int(user_id))

@app.context_processor
def inject_globals():
    return {'CATEGORIES': CATEGORIES, 'STATUSES': STATUSES, 'now': datetime.utcnow}

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(self)'
    return response

def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * radius * math.asin(math.sqrt(a))

def priority_for(category, severity, description, verifications=0):
    category_base = {
        'Pothole / Road Damage': 30, 'Garbage / Illegal Dumping': 22,
        'Broken Streetlight': 24, 'Water Leakage': 30, 'Blocked Drain': 30,
        'Footpath / Accessibility': 26, 'Other': 18,
    }.get(category, 18)
    severity_points = {'Low': 0, 'Medium': 10, 'High': 20, 'Critical': 30}.get(severity, 10)
    urgent_terms = ['accident', 'injury', 'school', 'hospital', 'flood', 'fire', 'open manhole', 'elderly', 'wheelchair']
    text = description.lower()
    urgency = min(15, sum(5 for term in urgent_terms if term in text))
    community = min(15, int(verifications) * 3)
    score = min(100, category_base + severity_points + urgency + community)
    label = 'Critical' if score >= 80 else 'High' if score >= 60 else 'Medium' if score >= 35 else 'Low'
    return score, label

def find_possible_duplicate(category, description, lat, lon):
    if lat is None or lon is None:
        return None, 0.0
    candidates = Complaint.query.filter_by(category=category).filter(Complaint.status != 'Rejected').order_by(Complaint.created_at.desc()).limit(250).all()
    candidates = [c for c in candidates if c.latitude is not None and c.longitude is not None]
    if not candidates: return None, 0.0
    nearby = [(c, haversine_km(lat, lon, c.latitude, c.longitude)) for c in candidates]
    nearby = [(c, d) for c, d in nearby if d <= 0.5]
    if not nearby: return None, 0.0
    if TfidfVectorizer is None: return None, 0.0
    docs = [re.sub(r'[^a-z0-9 ]', ' ', c.description.lower()) for c, _ in nearby]
    new_doc = re.sub(r'[^a-z0-9 ]', ' ', description.lower())
    try:
        matrix = TfidfVectorizer(stop_words='english', ngram_range=(1, 2)).fit_transform(docs + [new_doc])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        idx = int(scores.argmax())
        return (nearby[idx][0], float(scores[idx])) if scores[idx] >= 0.34 else (None, float(scores[idx]))
    except ValueError:
        return None, 0.0

def save_upload(file_storage):
    if not file_storage or not file_storage.filename: return None
    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[-1].lower() if '.' in original else ''
    if ext not in ALLOWED_EXTENSIONS: raise ValueError('Upload a JPG, PNG or WEBP photograph.')
    file_storage.stream.seek(0)
    try:
        image = Image.open(file_storage.stream)
        image.verify()
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream).convert('RGB')
        if image.width > 5000 or image.height > 5000: raise ValueError('Image dimensions are too large.')
        filename = f"{secrets.token_hex(16)}.jpg"
        image.save(Path(app.config['UPLOAD_FOLDER']) / filename, 'JPEG', quality=86, optimize=True)
        return filename
    except (UnidentifiedImageError, OSError):
        raise ValueError('The uploaded file is not a valid image.')

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role not in ('admin', 'officer'): abort(403)
        return fn(*args, **kwargs)
    return wrapper

def dashboard_data():
    """Build dashboard metrics directly from stored complaints and status events."""
    total = Complaint.query.count()
    active_statuses = ['Submitted', 'Under Review', 'Assigned', 'In Progress']
    active = Complaint.query.filter(Complaint.status.in_(active_statuses)).count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    critical = Complaint.query.filter(
        Complaint.priority_label.in_(['High', 'Critical']),
        Complaint.status != 'Resolved'
    ).count()
    category_rows = db.session.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    status_rows = db.session.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
    recent = Complaint.query.order_by(Complaint.created_at.desc()).limit(7).all()
    map_items = [
        {'id': c.tracking_code, 'category': c.category, 'status': c.status,
         'lat': c.latitude, 'lon': c.longitude, 'priority': c.priority_label}
        for c in Complaint.query.filter(Complaint.latitude.isnot(None), Complaint.longitude.isnot(None)).all()
    ]

    # Last 14 calendar days, including days with zero reports.
    today = datetime.utcnow().date()
    trend_labels, trend_values = [], []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        next_day = day + timedelta(days=1)
        trend_labels.append(day.strftime('%d %b'))
        trend_values.append(Complaint.query.filter(
            Complaint.created_at >= datetime.combine(day, datetime.min.time()),
            Complaint.created_at < datetime.combine(next_day, datetime.min.time())
        ).count())

    ward_rows = db.session.query(
        Complaint.ward, func.count(Complaint.id),
        func.sum(case((Complaint.status == 'Resolved', 1), else_=0))
    ).group_by(Complaint.ward).order_by(func.count(Complaint.id).desc()).all()
    wards = [{'name': ward or 'Not specified', 'total': int(count or 0), 'resolved': int(done or 0),
              'open': int((count or 0) - (done or 0))} for ward, count, done in ward_rows]

    now = datetime.utcnow()
    age_ranges = [('0–2 days', 0, 3), ('3–7 days', 3, 8), ('8–15 days', 8, 16), ('Over 15 days', 16, None)]
    ageing = []
    for label, lower, upper in age_ranges:
        q = Complaint.query.filter(Complaint.status.in_(active_statuses))
        cutoff = now - timedelta(days=lower)
        q = q.filter(Complaint.created_at <= cutoff)
        if upper is not None:
            q = q.filter(Complaint.created_at > now - timedelta(days=upper))
        ageing.append({'label': label, 'count': q.count()})

    # Use the first recorded Resolved event for actual resolution duration.
    durations = []
    resolved_items = Complaint.query.filter_by(status='Resolved').all()
    for item in resolved_items:
        first_event = ComplaintEvent.query.filter_by(complaint_id=item.id, status='Resolved').order_by(ComplaintEvent.created_at.asc()).first()
        resolved_at = first_event.created_at if first_event else item.updated_at
        if resolved_at and item.created_at and resolved_at >= item.created_at:
            durations.append((resolved_at - item.created_at).total_seconds() / 3600)
    avg_resolution_hours = round(sum(durations) / len(durations), 1) if durations else None

    return {
        'total': total, 'active': active, 'resolved': resolved, 'critical': critical,
        'resolution_rate': round((resolved / total) * 100) if total else 0,
        'avg_resolution_hours': avg_resolution_hours,
        'categories': {'labels': [x[0] for x in category_rows], 'values': [x[1] for x in category_rows]},
        'statuses': {'labels': [x[0] for x in status_rows], 'values': [x[1] for x in status_rows]},
        'trend': {'labels': trend_labels, 'values': trend_values},
        'wards': wards, 'ageing': ageing,
        'recent': recent, 'map_items': map_items
    }

@app.route('/')
def index():
    stats = dashboard_data()
    latest_resolved = Complaint.query.filter_by(status='Resolved').order_by(Complaint.updated_at.desc()).limit(3).all()
    return render_template('index.html', stats=stats, latest_resolved=latest_resolved)

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        name = request.form.get('citizen_name', '').strip()
        phone = re.sub(r'\D', '', request.form.get('phone', ''))
        category = request.form.get('category', '')
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        ward = request.form.get('ward', '').strip() or 'Not specified'
        severity = request.form.get('severity', 'Medium')
        try:
            lat_raw, lon_raw = request.form.get('latitude', '').strip(), request.form.get('longitude', '').strip()
            lat = float(lat_raw) if lat_raw else None
            lon = float(lon_raw) if lon_raw else None
            if (lat is None) != (lon is None): raise ValueError('Enter both map coordinates or leave both blank.')
            if lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError('Coordinates are outside the valid range.')
        except ValueError as exc:
            flash(str(exc), 'error'); return render_template('report.html')
        if not name or len(name) > 100 or len(phone) < 10 or not description or len(description) < 20 or not address or category not in CATEGORIES or severity not in SEVERITIES:
            flash('Please complete all required fields. Phone number must contain at least 10 digits and the description at least 20 characters.', 'error')
            return render_template('report.html')
        try: image_filename = save_upload(request.files.get('photo'))
        except ValueError as exc:
            flash(str(exc), 'error'); return render_template('report.html')
        duplicate, similarity = find_possible_duplicate(category, description, lat, lon)
        code = 'CT-' + secrets.token_hex(6).upper()
        score, label = priority_for(category, severity, description)
        complaint = Complaint(tracking_code=code, citizen_name=name, phone_last4=phone[-4:], category=category,
                              description=description, address=address, ward=ward, latitude=lat, longitude=lon,
                              image_filename=image_filename, severity=severity, priority_score=score,
                              priority_label=label, duplicate_of_id=duplicate.id if duplicate else None)
        db.session.add(complaint); db.session.flush()
        note = 'Complaint submitted by citizen.'
        if duplicate: note += f' Possible duplicate of {duplicate.tracking_code} ({similarity:.0%} text similarity); officer review required.'
        db.session.add(ComplaintEvent(complaint_id=complaint.id, status='Submitted', note=note, actor='Citizen'))
        db.session.commit()
        session['last_tracking_code'] = code
        return redirect(url_for('report_success', code=code))
    return render_template('report.html')

@app.route('/report/success/<code>')
def report_success(code):
    complaint = Complaint.query.filter_by(tracking_code=code).first_or_404()
    if session.get('last_tracking_code') != code: abort(403)
    return render_template('report_success.html', complaint=complaint)

@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'POST':
        code = request.form.get('tracking_code', '').strip().upper()
        last4 = re.sub(r'\D', '', request.form.get('phone_last4', ''))[-4:]
        complaint = Complaint.query.filter_by(tracking_code=code, phone_last4=last4).first()
        if not complaint:
            flash('We could not match that tracking ID and phone suffix. Please check the details.', 'error')
            return render_template('track.html')
        return redirect(url_for('complaint_detail', code=complaint.tracking_code))
    return render_template('track.html')

@app.route('/complaint/<code>')
def complaint_detail(code):
    complaint = Complaint.query.filter_by(tracking_code=code.upper()).first_or_404()
    return render_template('complaint.html', complaint=complaint)

@app.route('/complaint/<code>/verify', methods=['POST'])
def verify(code):
    complaint = Complaint.query.filter_by(tracking_code=code.upper()).first_or_404()
    if complaint.status in ('Resolved', 'Rejected'):
        flash('This complaint is closed and can no longer receive community confirmations.', 'error')
        return redirect(url_for('complaint_detail', code=code))
    mobile = re.sub(r'\D', '', request.form.get('mobile', ''))
    if len(mobile) < 10:
        flash('Enter a valid 10-digit mobile number for one-per-person demo verification.', 'error')
        return redirect(url_for('complaint_detail', code=code))
    voter_hash = hashlib.sha256((app.config['SECRET_KEY'] + mobile[-10:]).encode()).hexdigest()
    if Verification.query.filter_by(complaint_id=complaint.id, voter_hash=voter_hash).first():
        flash('This mobile number has already confirmed this report.', 'error')
        return redirect(url_for('complaint_detail', code=code))
    db.session.add(Verification(complaint_id=complaint.id, voter_hash=voter_hash))
    complaint.verification_count += 1
    complaint.priority_score, complaint.priority_label = priority_for(complaint.category, complaint.severity, complaint.description, complaint.verification_count)
    db.session.add(ComplaintEvent(complaint_id=complaint.id, status=complaint.status, note='Community confirmation received.', actor='Community'))
    db.session.commit()
    flash('Thank you. Your community confirmation has been recorded.', 'success')
    return redirect(url_for('complaint_detail', code=code))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Filenames are random, server-generated .jpg values, never user paths.
    from flask import send_from_directory
    if not re.fullmatch(r'[a-f0-9]{32}\.jpg', filename): abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, max_age=3600)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated: return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user); return redirect(url_for('admin_dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user(); flash('You have been signed out.', 'success'); return redirect(url_for('index'))

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = dashboard_data()
    return render_template('admin/dashboard.html', stats=stats, chart_categories=stats['categories'], chart_statuses=stats['statuses'])

@app.route('/admin/complaints')
@admin_required
def admin_complaints():
    query = Complaint.query
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    search = request.args.get('q', '').strip()
    if status in STATUSES: query = query.filter_by(status=status)
    if category in CATEGORIES: query = query.filter_by(category=category)
    if search: query = query.filter((Complaint.tracking_code.ilike(f'%{search}%')) | (Complaint.address.ilike(f'%{search}%')) | (Complaint.description.ilike(f'%{search}%')))
    complaints = query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin/complaints.html', complaints=complaints, selected_status=status, selected_category=category, search=search)

@app.route('/admin/complaints/<int:complaint_id>/update', methods=['POST'])
@admin_required
def admin_update(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    new_status = request.form.get('status', '')
    note = request.form.get('note', '').strip()
    if new_status not in STATUSES:
        flash('Select a valid status.', 'error')
    else:
        old_status = complaint.status
        complaint.status = new_status
        db.session.add(ComplaintEvent(complaint_id=complaint.id, status=new_status, note=note or f'Status changed from {old_status} to {new_status}.', actor=current_user.name))
        db.session.commit(); flash(f'{complaint.tracking_code} updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('admin_complaints'))

@app.route('/admin/export.csv')
@admin_required
def admin_export():
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(['Tracking ID','Category','Description','Address','Ward','Status','Severity','Priority Score','Priority','Community Confirmations','Latitude','Longitude','Created At'])
    for c in Complaint.query.order_by(Complaint.created_at.desc()).all():
        writer.writerow([c.tracking_code,c.category,c.description,c.address,c.ward,c.status,c.severity,c.priority_score,c.priority_label,c.verification_count,c.latitude,c.longitude,c.created_at.isoformat()])
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=civictrack-complaints.csv'})

@app.errorhandler(413)
def too_large(_):
    flash('The image is too large. Maximum upload size is 5 MB.', 'error')
    return redirect(url_for('report'))

@app.cli.command('init-db')
def init_db_command():
    db.create_all(); print('Database tables created.')

@app.cli.command('create-admin')
def create_admin_command():
    email = os.getenv('ADMIN_EMAIL', 'admin@civictrack.local').lower()
    password = os.getenv('ADMIN_PASSWORD', 'ChangeMe123!')
    name = os.getenv('ADMIN_NAME', 'CivicTrack Officer')
    if User.query.filter_by(email=email).first(): print(f'Admin already exists: {email}'); return
    user = User(email=email, name=name, role='admin'); user.set_password(password)
    db.session.add(user); db.session.commit(); print(f'Admin created: {email}. Change the demo password before deployment.')

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email=os.getenv('ADMIN_EMAIL', 'admin@civictrack.local').lower()).first():
        admin = User(email=os.getenv('ADMIN_EMAIL', 'admin@civictrack.local').lower(), name=os.getenv('ADMIN_NAME', 'CivicTrack Officer'), role='admin')
        admin.set_password(os.getenv('ADMIN_PASSWORD', 'ChangeMe123!'))
        db.session.add(admin); db.session.commit()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG', '1') == '1')
