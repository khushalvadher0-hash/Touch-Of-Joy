import os
from flask import Flask, redirect, url_for
from database import db
from models.user_model import User
from models.service_model import Service
from models.schedule_model import Schedule
from models.contact_model import ContactMessage


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Secret key from environment or use default for development
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key')
    
    # Database configuration - support both SQLite and PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # For Render or other production environments
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local SQLite database
        db_path = os.path.join(app.root_path, 'touch_of_joy.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_default_admin()
        ensure_default_schedule()
        ensure_sample_services()

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/')
    def root():
        return redirect(url_for('auth.login'))

    return app


def ensure_default_admin():
    admin_email = 'admin123@gmail.com'
    admin_password = 'admin@123'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(name='Admin', email=admin_email, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


def ensure_default_schedule():
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
        schedule = Schedule.query.filter_by(day=day).first()
        if not schedule:
            schedule = Schedule(day=day, hours=hours)
            db.session.add(schedule)
    db.session.commit()


def ensure_sample_services():
    # Only add sample services if none exist
    if Service.query.count() == 0:
        samples = [
            # Hair Services
            ('Haircut', 'hair', '₹599', 'Professional haircut tailored to your style and face shape.', 'Hair Cutting.png'),
            ('Hairstyling', 'hair', '₹1,299', 'Expert styling for any occasion - casual, formal, or wedding.', 'Hairstyle.jpg'),
            ('Braids', 'hair', '₹1,599', 'Beautiful braid styles for a fresh, trendy look.', 'Braids.png'),
            
            # Skin Services
            ('Skin Care', 'skin', '₹899', 'Personalized skincare routine tailored to your skin type.', 'Facial.webp'),
            ('Facials', 'skin', '₹1,199', 'Deep cleansing and rejuvenating facial treatments for radiant skin.', 'Facial.webp'),
            ('Acne Treatments', 'skin', '₹1,499', 'Targeted acne treatment to clear and prevent breakouts.', 'Acne treatments.jpg'),
            ('Waxing', 'skin', '₹499', 'Smooth and hair-free skin with our professional waxing service.', 'Waxing.jpeg'),
            
            # Grooming Services
            ('Eyebrow Threading', 'grooming', '₹299', 'Precise eyebrow shaping with traditional threading technique.', 'eyebrow-threading.jpeg'),
            
            # Bridal Services
            ('Bridal Makeup', 'bridal', '₹8,999', 'Complete bridal makeup with premium products and personalized design.', 'Bride.png'),
        ]
        for name, category, price, description, photo in samples:
            service = Service(name=name, category=category, price=price, description=description, photo=photo)
            db.session.add(service)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
