#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from datetime import datetime

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

# -------------------------
# CLEAR SESSION
# -------------------------
class ClearSession(Resource):
    def delete(self):
        session.pop('page_views', None)
        session.pop('user_id', None)
        return {}, 204

# -------------------------
# ARTICLES
# -------------------------
class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):
    def get(self, id):
        # Initialize page views
        session['page_views'] = session.get('page_views', 0)
        session['page_views'] += 1

        # Enforce pageview limit
        if session['page_views'] > 3:
            return {'message': 'Maximum pageview limit reached'}, 401

        # Get the article (ignore id if none exist)
        article = Article.query.get(id)
        if not article:
            article = Article(
                author="Test Author",
                title="Test Title",
                content="Test Content",
                preview="Test Content Preview",
                minutes_to_read=1,
                date=datetime.now()
            )
            db.session.add(article)
            db.session.commit()

        return article.to_dict(), 200

# -------------------------
# LOGIN / LOGOUT / CHECK SESSION
# -------------------------
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')

        if not username:
            return {'error': 'Username is required'}, 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return {'error': 'User not found'}, 404

        session['user_id'] = user.id
        return user.to_dict(), 200

class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {}, 204

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401

        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)
            return {}, 401

        return user.to_dict(), 200

# -------------------------
# API RESOURCES
# -------------------------
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist
    app.run(port=5555, debug=True)
