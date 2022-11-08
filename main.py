#ALL IMPORTS
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import sqlite3
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

#Creating DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///product-details.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#TABLE Details
class Details(db.Model):
    product_name = db.Column(db.String(50), nullable=False, unique=True, primary_key=True)
    product_price = db.Column(db.String(50), nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)

#For Inititally Creating Database
#db.create_all()


#WTForm
class EditForm(FlaskForm):
    product = StringField('Product name: ', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    price = StringField("Price (e.g $8) ", validators=[DataRequired()])
    add = SubmitField('Save')


# all Flask routes below

@app.route('/', methods=["GET", "POST"])
def home():
    edit_form = EditForm()
    all_products = db.session.query(Details).all()
    if edit_form.validate_on_submit and not edit_form.price.data==None:
        prod=edit_form.product.data
        book_to_update = Details.query.filter_by(product_name=prod).first()
        if book_to_update == None:
            #NEW ENTRY
            req_name = edit_form.product.data
            req_price = edit_form.price.data
            req_quantity = edit_form.quantity.data
            new_product = Details(product_name = req_name, product_price=req_price, product_quantity=req_quantity)
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for("home"))
        else:
            #EDITING EXISTING ENTRY
            book_to_update.product_price = edit_form.price.data
            book_to_update.product_quantity = edit_form.quantity.data
            db.session.commit()
        return redirect(url_for("home"))

    return render_template('cafes.html', products=all_products, edit_form=edit_form)

@app.route('/search-results', methods=["POST"])
def search():
    # getting input with name = fname in HTML form
    req_name = request.form.get("searchname")
    book = Details.query.filter_by(product_name=req_name).first()
    if book == None:
        return '<h1>This Product doesnt exists</h1>'
    else:
        return render_template("search_result.html", product=book)

#--------------------REST API's for the code---------------------

#RETURNING ITEMS FROM DB AS DICTIONARY INSTEAD OF LIST FOR EASE DURING JSONIFYING
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

#RETURNING ALL DATA
@app.route('/api/organization/all', methods=['GET'])
def api_all():
    conn = sqlite3.connect('product-details.db') #CREATING CURSOR
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_organization = cur.execute('SELECT * FROM Details;').fetchall() #RETRIEVING ALL DATA

    return jsonify(all_organization) #RETURNING AS JSON


#FOR HANDLING ERRORS FOR WRONG QUERIES
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

#FOR HANDLING ERRORS FOR WRONG QUERIES
@app.errorhandler(400)
def bad_request(e):
    return "<h1>400</h1><p>Enter all required fields for posting new product </p>", 400

#To return based on search results
@app.route('/api/products', methods=['GET'])
def api_filter():
    query_parameters = request.args #GRABBING QUERY PARAMETERS

    product_name = query_parameters.get('product_name')
    product_price = query_parameters.get('product_price')
    product_quantity = query_parameters.get('product_quantity')

    query = "SELECT * FROM Details WHERE"
    to_filter = [] #STORING ALL PASSED PARAMETERS

    if product_price:
        query += ' product_price=? AND'
        to_filter.append(product_price)
    if product_name:
        query += ' product_name=? AND'
        to_filter.append(product_name)
    if product_quantity:
        query += ' product_quantity=? AND'
        to_filter.append(product_quantity)
    if not (product_price or product_name or product_quantity):
        return page_not_found(404)

    query = query[:-4] + ';' #Removing the trailing AND FROM OUR QUERY

    conn = sqlite3.connect('product-details.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()
    return jsonify(results)


#To save new additions
@app.route('/api/post', methods=["GET", "POST"])
def api_post():
    query_parameters = request.args #GRABBING QUERY PARAMETERS
    product_name = query_parameters.get('product_name')
    product_price = query_parameters.get('product_price')
    product_quantity = query_parameters.get('product_quantity')
    if not (product_price and product_name and product_quantity):
        return bad_request(400)
    else:
        new_product = Details(product_name = product_name, product_price=product_price, product_quantity=product_quantity)
        db.session.add(new_product)
        db.session.commit()
        conn = sqlite3.connect('product-details.db') #CREATING CURSOR
        conn.row_factory = dict_factory
        cur = conn.cursor()
        all_organization = cur.execute('SELECT * FROM Details;').fetchall() #RETRIEVING ALL DATA

        return jsonify(all_organization) #RETURNING AS JSON



# http://127.0.0.1:5000/api/products/all GETTING ALL INFO
# http://127.0.0.1:5000/api/products?product_name=Apple+watch PASSING PARAMETER Finding Product with name = Apple watch
# http://127.0.0.1:5000/api/products?product_quantity=30 PASSING PARAMETER Finding product with quantity = 30
# http://127.0.0.1:5000/api/products?product_price=$10 Finding product with price = 10$
# http://127.0.0.1:5000/api/products?product_price=$10&product_quantity=30 PASSING MULTIPLE PARAMETERS

# http://127.0.0.1:5000/api/products? ERROR PAGE IF RESOURCE NOT FOUND 404


# http://127.0.0.1:5000/api/post?product_price=$10&product_quantity=30 POSTING WITH INCOMPLETE DATA - Bad Request 400
# http://127.0.0.1:5000/api/post?product_price=$50&product_quantity=30&product_name=Nokia+Headset POSTING WITH Complete data



if __name__ == '__main__':
    app.run(debug=True)
