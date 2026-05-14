import os
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from database import db
from models.user_model import User
from models.service_model import Service
from models.schedule_model import Schedule
from models.contact_model import ContactMessage

admin_bp = Blueprint('admin', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def admin_required():
    if not session.get('user_id') or not session.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('auth.login'))
    return None


def save_photo(photo):
    if not photo or not photo.filename:
        return ''
    if '.' not in photo.filename:
        return ''

    extension = photo.filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return None

    filename = secure_filename(photo.filename)
    photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return filename


@admin_bp.route('/')
def dashboard():
    denied = admin_required()
    if denied:
        return denied
    return redirect(url_for('admin.users'))


@admin_bp.route('/users')
def users():
    denied = admin_required()
    if denied:
        return denied

    query = request.args.get('q', '').strip().lower()
    users = User.query.filter(User.is_admin == False)
    if query:
        users = users.filter(
            (User.name.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%'))
        )
    users = users.all()
    return render_template('admin_users.html', users=users, query=query, active='users')


@admin_bp.route('/services')
def services():
    denied = admin_required()
    if denied:
        return denied

    services = Service.query.order_by(Service.category, Service.name).all()
    return render_template('admin_services.html', services=services, active='services')


@admin_bp.route('/messages')
def messages():
    denied = admin_required()
    if denied:
        return denied

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages, active='messages')


@admin_bp.route('/services/add', methods=['GET', 'POST'])
def add_service():
    denied = admin_required()
    if denied:
        return denied

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip().lower()
        description = request.form.get('description', '').strip()
        photo = request.files.get('photo')

        if not name or not category or not description:
            flash('Please fill all required fields.', 'danger')
            return render_template('admin_edit_service.html', service=None, active='services')

        photo_filename = None
        if photo and photo.filename:
            photo_filename = save_photo(photo)
            if photo_filename is None:
                flash('Only images are allowed for service photos.', 'danger')
                return render_template('admin_edit_service.html', service=None, active='services')

        service = Service(name=name, category=category, description=description, photo=photo_filename)
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully.', 'success')
        return redirect(url_for('admin.services'))

    return render_template('admin_edit_service.html', service=None, active='services')


@admin_bp.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    denied = admin_required()
    if denied:
        return denied

    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        service.name = request.form.get('name', '').strip()
        service.category = request.form.get('category', '').strip().lower()

        service.description = request.form.get('description', '').strip()
        photo = request.files.get('photo')

        if photo and photo.filename:
            filename = save_photo(photo)
            if filename is None:
                flash('Only images are allowed for service photos.', 'danger')
                return render_template('admin_edit_service.html', service=service, active='services')
            service.photo = filename

        db.session.commit()
        flash('Service updated successfully.', 'success')
        return redirect(url_for('admin.services'))

    return render_template('admin_edit_service.html', service=service, active='services')


@admin_bp.route('/services/delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    denied = admin_required()
    if denied:
        return denied

    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully.', 'success')
    return redirect(url_for('admin.services'))


@admin_bp.route('/schedule', methods=['GET', 'POST'])
def schedule():
    denied = admin_required()
    if denied:
        return denied

    schedule_items = Schedule.query.order_by(Schedule.id).all()
    if request.method == 'POST':
        for item in schedule_items:
            hours = request.form.get(item.day, '').strip() or 'Closed'
            item.hours = hours
        db.session.commit()
        flash('Schedule has been updated.', 'success')
        return redirect(url_for('admin.schedule'))

    return render_template('admin_schedule.html', schedule_items=schedule_items, active='schedule')


@admin_bp.route('/database', methods=['GET'])
def database():
    denied = admin_required()
    if denied:
        return denied
    
    return render_template('admin_database.html', active='database')


@admin_bp.route('/database/reset', methods=['POST'])
def database_reset():
    denied = admin_required()
    if denied:
        return denied
    
    try:
        db.drop_all()
        db.create_all()
        
        # Recreate default admin user
        admin_email = 'admin123@gmail.com'
        admin_password = 'admin@123'
        admin = User(name='Admin', email=admin_email, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        
        # Recreate default schedule
        days = [
            ('Monday', '09:00 AM - 07:00 PM'),
            ('Tuesday', '09:00 AM - 07:00 PM'),
            ('Wednesday', '09:00 AM - 07:00 PM'),
            ('Thursday', '09:00 AM - 07:00 PM'),
            ('Friday', '09:00 AM - 07:00 PM'),
            ('Saturday', '10:00 AM - 08:00 PM'),
            ('Sunday', '10:00 AM - 05:00 PM'),
        ]
        for day, hours in days:
            schedule = Schedule(day=day, hours=hours)
            db.session.add(schedule)
        
        # Recreate sample services
        samples = [
            ('Haircut', 'hair', 'Professional haircut tailored to your style and face shape.', 'Hair Cutting.png'),
            ('Hairstyling', 'hair', 'Expert styling for any occasion - casual, formal, or wedding.', 'Hairstyle.jpg'),
            ('Braids', 'hair', 'Beautiful braid styles for a fresh, trendy look.', 'Braids.png'),
            ('Skin Care', 'skin', 'Personalized skincare routine tailored to your skin type.', 'Facial.webp'),
            ('Facials', 'skin', 'Deep cleansing and rejuvenating facial treatments for radiant skin.', 'Facial.webp'),
            ('Acne Treatments', 'skin', 'Targeted acne treatment to clear and prevent breakouts.', 'Acne treatments.jpg'),
            ('Waxing', 'skin', 'Smooth and hair-free skin with our professional waxing service.', 'Waxing.jpeg'),
            ('Eyebrow Threading', 'grooming', 'Precise eyebrow shaping with traditional threading technique.', 'eyebrow-threading.jpeg'),
            ('Bridal Makeup', 'bridal', 'Complete bridal makeup with premium products and personalized design.', 'Bride.png'),
        ]
        for name, category, description, photo in samples:
            service = Service(name=name, category=category, description=description, photo=photo)
            db.session.add(service)
        
        db.session.commit()
        flash('Database reset successfully! All tables recreated with default data.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting database: {str(e)}', 'danger')
    
    return redirect(url_for('admin.database'))

