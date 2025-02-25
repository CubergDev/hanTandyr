from flask import Flask, request, render_template, redirect, url_for
from flask_babel import Babel, lazy_gettext as _
import asyncio

from models import db, FranchiseApplication

babel = Babel()

LANGUAGES = ['ru', 'en', 'kk', 'zh', 'ar']

def get_locale():
    lang = request.args.get('lang')
    if lang in LANGUAGES:
        return lang
    return 'ru'

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///franchise.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'some_secret_key'

    db.init_app(app)
    babel.init_app(app)
    babel.get_locale = get_locale

    with app.app_context():
        db.create_all()

    @app.before_first_request
    def start_bot_thread():
        # Запускаем бот в отдельном потоке, чтобы он был запущен даже при flask run
        import threading
        from bot import run_bot
        threading.Thread(target=run_bot, daemon=True).start()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/menu')
    def menu():
        return render_template('menu.html')

    @app.route('/apply', methods=['POST'])
    def apply():
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')

        phone_prefix = request.form.get('phone_prefix') or ''
        phone_main = request.form.get('phone_main') or ''
        phone_full = phone_prefix + phone_main

        email = request.form.get('email')
        comment = request.form.get('comment', '')
        privacy = True if request.form.get('privacy') else False
        telegram = request.form.get('telegram', '')

        chosen_lang = get_locale()

        application_obj = FranchiseApplication(
            firstname=firstname,
            lastname=lastname,
            phone=phone_full,
            email=email,
            comment=comment,
            privacy_accepted=privacy,
            telegram_handle=telegram,
            lang=chosen_lang
        )
        db.session.add(application_obj)
        db.session.commit()

        # Локальный импорт функции уведомления (чтобы избежать циклического импорта)
        from bot import notify_new_application
        asyncio.run(notify_new_application(application_obj.id))

        return redirect(url_for('index'))

    @app.context_processor
    def inject_get_locale():
        return dict(get_locale=get_locale)

    return app


if __name__ == '__main__':
    app = create_app()
    # Запускаем бота в отдельном потоке
    import threading
    from bot import run_bot
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(debug=True)
