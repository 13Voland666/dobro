from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:a9p6bc36vyxxSuJs@127.0.0.1/kulig_bd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Определение моделей для таблиц базы данных
class Profile(db.Model):
    __tablename__ = 'profile'
    C_ID = db.Column(db.Integer, primary_key=True)
    C_Name = db.Column(db.String(30))
    C_Surname = db.Column(db.String(30))
    C_Email = db.Column(db.String(50))
    C_Phone = db.Column(db.String(15))
    C_Balance = db.Column(db.Integer)
    TG_ID = db.Column(db.Integer)

class HostingPlans(db.Model):
    __tablename__ = 'hostingplans'
    HP_ID = db.Column(db.Integer, primary_key=True)
    # ... other columns

class Orders(db.Model):
    __tablename__ = 'orders'
    HP_ID = db.Column(db.Integer, db.ForeignKey('hostingplans.HP_ID'), primary_key=True)
    C_ID = db.Column(db.Integer, db.ForeignKey('profile.C_ID'), primary_key=True)
    O_Status = db.Column(db.SmallInteger, default=None)
    P_Date = db.Column(db.Date, default=None)

# Создание всех таблиц в базе данных
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Пример использования данных из базы данных
    profiles = Profile.query.all()
    orders = Orders.query.all()
    return render_template('index.html', profiles=profiles, orders=orders)

@app.route('/edit_profile/<int:profile_id>', methods=['POST'])
def edit_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        profile.C_Name = request.form['name']
        profile.C_Surname = request.form['surname']
        profile.C_Email = request.form['email']
        profile.C_Phone = request.form['phone']
        profile.C_Balance = int(request.form['balance'])
        
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/edit_order/<int:hp_id>/<int:c_id>', methods=['POST'])
def edit_order(hp_id, c_id):
    order = Orders.query.get_or_404({'HP_ID': hp_id, 'C_ID': c_id})
    
    if request.method == 'POST':
        order.O_Status = int(request.form['status'])
        order.P_Date = request.form['date']
        
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/delete_order/<int:hp_id>/<int:c_id>')
def delete_order(hp_id, c_id):
    order = Orders.query.get_or_404({'HP_ID': hp_id, 'C_ID': c_id})
    
    db.session.delete(order)
    db.session.commit()
    
    return redirect(url_for('index'))
@app.route('/delete_profile/<int:profile_id>')
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    db.session.delete(profile)
    db.session.commit()
    
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)
