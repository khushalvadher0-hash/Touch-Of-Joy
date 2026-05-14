import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models.user_model import User

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'


def is_valid_email(email):
    return bool(re.match(EMAIL_REGEX, email))


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Email or password is incorrect. Please try again.', 'danger')
            return render_template('login.html')

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['is_admin'] = bool(user.is_admin)
        flash('Login successful. Welcome back!', 'success')
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.home'))

    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not name or not email or not password:
            flash('Please provide name, email, and password.', 'danger')
            return render_template('login.html', show_signup=True)

        if not is_valid_email(email):
            flash('Please provide a valid email address.', 'danger')
            return render_template('login.html', show_signup=True)

        if User.query.filter_by(email=email).first():
            flash('That email is already registered. Please use a different email.', 'danger')
            return render_template('login.html', show_signup=True)

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['is_admin'] = False
        flash('Signup successful. You are now logged in.', 'success')
        return redirect(url_for('main.home'))

    return render_template('login.html', show_signup=True)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
