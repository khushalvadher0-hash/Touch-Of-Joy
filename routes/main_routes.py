from flask import Blueprint, render_template, session, redirect, url_for, current_app, send_from_directory, request, flash
from database import db
from models.service_model import Service
from models.schedule_model import Schedule
from models.contact_model import ContactMessage

main_bp = Blueprint('main', __name__)


@main_bp.route('/home')
def home():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    hair_services = Service.query.filter_by(category='hair').all()
    skin_services = Service.query.filter_by(category='skin').all()
    bridal_services = Service.query.filter_by(category='bridal').all()
    grooming_services = Service.query.filter_by(category='grooming').all()
    schedule_items = Schedule.query.order_by(Schedule.id).all()
    return render_template(
        'home.html',
        hair_services=hair_services,
        skin_services=skin_services,
        bridal_services=bridal_services,
        grooming_services=grooming_services,
        schedule_items=schedule_items,
    )


@main_bp.route('/contact', methods=['POST'])
def contact():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    message_text = request.form.get('message', '').strip()

    if not name or not email or not message_text:
        flash('Please fill in all fields before sending your message.', 'danger')
        return redirect(url_for('main.home') + '#contact')

    contact_message = ContactMessage(name=name, email=email, message=message_text)
    db.session.add(contact_message)
    db.session.commit()

    flash('Your message has been sent. The admin will review it soon.', 'success')
    return redirect(url_for('main.home') + '#contact')


@main_bp.route('/services/<category>')
def services(category):
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    category = category.lower()
    allowed = {
        'hair': 'Hair Service',
        'skin': 'Skin Service',
        'bridal': 'Bridal Makeup',
        'grooming': 'Grooming Services'
    }
    if category not in allowed:
        return redirect(url_for('main.home'))

    services = Service.query.filter_by(category=category).all()
    return render_template('services.html', services=services, category_label=allowed[category])


@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
