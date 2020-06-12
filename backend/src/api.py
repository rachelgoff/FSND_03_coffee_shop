import os
from flask import Flask, request, abort, jsonify
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resource={r"*/api/*": {"origins": "*"}})

'''
Use the after_request decorator to set Access-Control-Allow.
'''
@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add(
        'Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


'''
initialize the datbase
'''
db_drop_and_create_all()

# ROUTES
'''
GET /drinks
It should be a public endpoint and contain only the drink.short()
data representation
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        all_drinks = Drink.query.order_by('id').all()
        if all_drinks:
            drinks = [drink.short() for drink in all_drinks]
        else:
            drinks = []
    except Exception as e:
        print(e)
        abort(404)
    return jsonify({
        "success": True,
        "drinks": drinks
        })


'''
GET /drinks-detail
it requires the 'get:drinks-detail' permission and contains the drink.long()
data representation
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth("get:drinks-detail")
def get_drinks_detail(token):
    try:
        all_drinks = Drink.query.order_by('id').all()
        drinks = [drink.long() for drink in all_drinks]

        return jsonify({
            "success": True,
            "drinks": drinks
            })
    except IndexError:
        abort(404)


'''
POST /drinks
it requires the 'post:drinks' permission and it contains the drink.long()
data representation
'''


@app.route('/drinks', methods=['POST'])
@requires_auth("post:drinks")
def create_drink(token):
    try:
        body = request.get_json()
        title = body.get('title')
        recipe = body.get('recipe')

        if (title is None) or (recipe is None):
            abort(422)

        new_drink = Drink(title=title, recipe=json.dumps(recipe))
        new_drink.insert()
        print(new_drink.id)

        all_drinks = Drink.query.all()
        drinks = [drink.long() for drink in all_drinks]
        drink = Drink.query.get(1)
        print(drink.long())

        return jsonify({
            "success": True,
            "drinks": drinks
            })
    except IndexError:
        abort(422)


'''
PATCH /drinks/<id>
it requires the 'patch:drinks' permission and contains the drink.long()
data representation
# '''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth("patch:drinks")
def update_drink(token, id):
    body = request.get_json()
    new_title = body.get('title')
    new_recipe = json.dumps(body.get('recipe'))

    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    if new_title is not None:
        drink.title = new_title
    if new_recipe is not None:
        drink.recipe = new_recipe

    drink.update()

    return jsonify({
        "success": True,
        "drinks": drink.long()
    })


'''
DELETE /drinks/<id>
it deletes the corresponding row for <id> and requires
the 'delete:drinks' permission.
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth("delete:drinks")
def delete_drink(toke, id):
    try:
        delete_id = id
        drink = Drink.query.get(id)
        if drink is None:
            abort(404)
        drink.delete()

        return jsonify({
            "success": True,
            "delete": delete_id
        })
    except IndexError:
        abort(404)

# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
        }), 422


@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
        }), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "Internal server error"
      }), 500


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "Method not allowed"
      }), 405


@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized error"
        }), 401


'''
error handler for AuthError
'''


@app.errorhandler(AuthError)
def auth_error(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response
