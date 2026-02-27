import os
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

from document_processing import ocr_extract, summarize_text, extract_tags, embed_text

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["UPLOAD_FOLDER"] = "uploads"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# =====================================================
# MODELS
# =====================================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    parent_id = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, default=1)

    text = db.Column(db.Text)
    summary = db.Column(db.Text)
    tags = db.Column(db.String(255))
    embedding = db.Column(db.JSON)

    status = db.Column(db.String(20), default="pending")
    approved_by = db.Column(db.Integer, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)
    user_email = db.Column(db.String(120))
    user_role = db.Column(db.String(20), nullable=False)

    document_id = db.Column(db.Integer)
    document_name = db.Column(db.String(255))

    action = db.Column(db.String(50), nullable=False)

    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    version = db.Column(db.Integer)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================================================
# AUDIT HELPER
# =====================================================

def log_action(action, document=None, old_status=None, new_status=None, details=None):
    if not current_user.is_authenticated:
        return

    log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        document_id=document.id if document else None,
        document_name=document.filename if document else None,
        action=action,
        old_status=old_status,
        new_status=new_status,
        version=document.version if document else None,
        details=details
    )

    db.session.add(log)


# =====================================================
# SMART SEARCH (COSINE)
# =====================================================

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0

    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# =====================================================
# AUTH
# =====================================================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        role = request.form.get("role")

        hashed = bcrypt.generate_password_hash(pw).decode("utf-8")
        user = User(email=email, password=hashed, role=role)

        db.session.add(user)
        db.session.commit()

        flash("Account created!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, pw):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# =====================================================
# DASHBOARD (SMART SEARCH)
# =====================================================

@app.route("/dashboard")
@login_required
def dashboard():

    status_filter = request.args.get("status")
    search_query = request.args.get("q", "").strip()

    if current_user.role == "admin":
        query = Document.query

    elif current_user.role in ["professor", "assistant"]:
        query = Document.query
        if not status_filter:
            query = query.filter_by(status="approved")

    else:
        query = Document.query.filter_by(status="approved")

    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)

    docs = query.order_by(Document.uploaded_at.desc()).all()

    # SMART SEARCH
    if search_query and len(search_query) >= 2:

        query_embedding = embed_text(search_query)
        scored = []

        for doc in docs:

            keyword_score = 0

            if search_query.lower() in (doc.filename or "").lower():
                keyword_score += 3

            if search_query.lower() in (doc.summary or "").lower():
                keyword_score += 2

            if search_query.lower() in (doc.tags or "").lower():
                keyword_score += 2

            semantic_score = 0
            if doc.embedding:
                semantic_score = cosine_similarity(query_embedding, doc.embedding)

            total_score = keyword_score + (semantic_score * 5)

            if total_score > 0:
                scored.append((doc, total_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        docs = [x[0] for x in scored]

    return render_template(
    "dashboard.html",
    docs=docs,
    q=search_query,
    current_view="dashboard"
)

# =====================================================
# MY UPLOADS
# =====================================================

@app.route("/my_uploads")
@login_required
def my_uploads():

    docs = Document.query.filter_by(
        owner_id=current_user.id
    ).order_by(Document.uploaded_at.desc()).all()

    return render_template(
        "my_uploads.html",
        documents=docs
    )

# =====================================================
# UPLOAD + VERSIONING
# =====================================================

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if current_user.role not in ["admin", "professor", "assistant"]:
        flash("Students cannot upload.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        files = request.files.getlist("file")

        for file in files:
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            text = ocr_extract(save_path)
            summary = summarize_text(text)
            tags = extract_tags(text)
            embedding = embed_text(summary)

            existing_doc = Document.query.filter_by(
                filename=filename,
                owner_id=current_user.id
            ).order_by(Document.version.desc()).first()

            if existing_doc:
                new_version = existing_doc.version + 1
                parent_id = existing_doc.parent_id or existing_doc.id
            else:
                new_version = 1
                parent_id = None

            doc = Document(
                filename=filename,
                owner_id=current_user.id,
                parent_id=parent_id,
                version=new_version,
                text=text,
                summary=summary,
                tags=",".join(tags) if tags else None,
                embedding=embedding,
                status="approved" if current_user.role == "admin" else "pending"
            )

            db.session.add(doc)

            if new_version == 1:
                log_action("UPLOAD", document=doc)
            else:
                log_action("NEW_VERSION", document=doc, details="New version uploaded")

        db.session.commit()
        flash("Uploaded successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# =====================================================
# APPROVE / REJECT
# =====================================================

@app.route("/approve/<int:doc_id>")
@login_required
def approve(doc_id):

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    doc = Document.query.get_or_404(doc_id)

    old_status = doc.status
    doc.status = "approved"
    doc.approved_by = current_user.id
    doc.approved_at = datetime.utcnow()
    doc.rejection_reason = None

    log_action("APPROVE", document=doc, old_status=old_status, new_status="approved")

    db.session.commit()
    flash("Approved!", "success")
    return redirect(url_for("dashboard"))


@app.route("/reject/<int:doc_id>", methods=["GET", "POST"])
@login_required
def reject(doc_id):

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    doc = Document.query.get_or_404(doc_id)

    if request.method == "POST":
        reason = request.form.get("reason")

        old_status = doc.status
        doc.status = "rejected"
        doc.rejection_reason = reason
        doc.approved_by = current_user.id
        doc.approved_at = datetime.utcnow()

        log_action("REJECT", document=doc, old_status=old_status, new_status="rejected", details=reason)

        db.session.commit()
        flash("Rejected!", "danger")
        return redirect(url_for("dashboard"))

    return render_template("reject_reason.html", doc=doc)


# =====================================================
# DELETE
# =====================================================

@app.route("/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete_document(doc_id):

    doc = Document.query.get_or_404(doc_id)

    if current_user.role != "admin" and doc.owner_id != current_user.id:
        return redirect(url_for("dashboard"))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    log_action("DELETE", document=doc)

    db.session.delete(doc)
    db.session.commit()

    flash("Deleted successfully.", "success")
    return redirect(url_for("dashboard"))


# =====================================================
# OPEN / DOWNLOAD
# =====================================================

@app.route("/document/<int:doc_id>")
@login_required
def open_document(doc_id):

    doc = Document.query.get_or_404(doc_id)

    if current_user.role == "student" and doc.status != "approved":
        return redirect(url_for("dashboard"))

    log_action("OPEN", document=doc)
    db.session.commit()

    return send_from_directory(app.config["UPLOAD_FOLDER"], doc.filename)


@app.route("/file/<filename>")
@login_required
def file_view(filename):

    doc = Document.query.filter_by(filename=filename).first()

    if doc:
        log_action("DOWNLOAD", document=doc)
        db.session.commit()

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# =====================================================
# ADMIN AUDIT
# =====================================================

@app.route("/admin/audit")
@login_required
def admin_audit():

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template("admin_audit.html", logs=logs)


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    with app.app_context():
        db.create_all()

    app.run(debug=True)