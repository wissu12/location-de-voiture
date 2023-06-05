

from bson import ObjectId
from pymongo import ReturnDocument # type: ignore
from flask import Flask, redirect, render_template, request
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from werkzeug.utils import secure_filename
from datetime import datetime  # type: ignore 
from flask import send_from_directory
import os

 
client = MongoClient('mongodb://localhost:27017/')
db = client['voitures']
collection = db['voiture']

app = Flask(__name__)


# Configuration du dossier d'uploads
app.config['UPLOAD_FOLDER'] = 'static'


#filtrage de date 
@app.route('/voitures/search', methods=['GET'])
def rechercher_voitures():
    date_debut_str = request.args.get('date_debut')
    date_fin_str = request.args.get('date_fin')

    voitures = db.voiture.find({
        'date_dispo_debut': {'$gte': date_debut_str},
        'date_dispo_fin': {'$lte': date_fin_str},
    })

    return render_template('table_voitures.html', voitures=voitures)


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/voitures/<voiture_id>/reserve', methods=['GET', 'POST'])
def afficher_formulaire_reservation(voiture_id):
    voiture_id = ObjectId(voiture_id)  # Convertir l'ID de la voiture en ObjectId
    reservation_effectuee = False  # Variable pour indiquer si la réservation a été effectuée avec succès

    if request.method == 'POST':
        # Récupérer les détails de la voiture
        voiture = db.voiture.find_one({'_id': voiture_id})
        if voiture:
            date_debut = datetime.strptime(request.form.get('date_debut_reservation'), '%Y-%m-%d')
            date_fin = datetime.strptime(request.form.get('date_fin_reservation'), '%Y-%m-%d')

            # Convertir la date de disponibilité de la voiture en datetime
            date_dispo_debut = datetime.strptime(voiture.get('date_dispo_debut'), '%Y-%m-%d')
            date_dispo_fin = datetime.strptime(voiture.get('date_dispo_fin'), '%Y-%m-%d')

            # Vérifier si la date de début est inférieure à la date de disponibilité de la voiture
            if date_debut < date_dispo_debut:
                error_message = "La date de début de réservation est antérieure à la date de disponibilité de la voiture."
                return render_template('formulaire_reservation.html', nom_voiture=voiture.get('Nom', ''), error_message=error_message)

            # Vérifier si la date de fin est supérieure à la date de disponibilité de la voiture
            if date_fin > date_dispo_fin:
                error_message = "La date de fin de réservation dépasse la date de disponibilité de la voiture."
                return render_template('formulaire_reservation.html', nom_voiture=voiture.get('Nom', ''), error_message=error_message)

            reservation = {
                'nom_voiture': voiture.get('Nom', ''),
                'matricule': voiture.get('Matricule', ''),
                'prix':voiture.get('prix',''),
                'cin_client': request.form.get('cin_client'),
                'date_debut_reserv': date_debut,
                'date_fin_reserv': date_fin,
                'statut': request.form.get('statut', 'en attente')
            }
            db.reservations.insert_one(reservation)
            reservation_effectuee = True  # Mettre la variable à True après l'enregistrement de la réservation

        return redirect('/voitures')

    voiture = db.voiture.find_one({'_id': voiture_id})
    if voiture:
        nom_voiture = voiture.get('Nom', '')
        matricule = voiture.get('Matricule', '')
        prix= voiture.get('prix','')
        return render_template('formulaire_reservation.html', nom_voiture=nom_voiture, matricule=matricule,prix=prix, voiture_id=voiture_id, reservation_effectuee=reservation_effectuee)
    else:
        return redirect('/voitures')


@app.route('/voitures', methods=['GET'])
def get_voitures():
    voitures = list(collection.find())
    return render_template('voitures.html', voitures=voitures)

@app.route('/voitures/add', methods=['GET', 'POST'])
def add_voiture():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.form['nom']
        marque = request.form['marque']
        matricule= request.form['matricule']
        date_debut = request.form['date_debut']
        date_fin = request.form['date_fin']
        statut = request.form['statut']
        prix = request.form['prix']

        # Créer un dictionnaire pour représenter la nouvelle voiture
        voiture = {
            'Nom': nom,
            'Matricule':matricule,
            'Marque': marque,
            'date_dispo_debut': date_debut,
            'date_dispo_fin': date_fin,
            'statut': statut,
            'prix': prix
        }

           # Gérer le téléchargement de la photo
        photo = request.files['photo']
        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            voiture['photo'] = filename


        
        # Insérer la nouvelle voiture dans la base de données
        voiture_id = collection.insert_one(voiture)

        return redirect('/voitures')

    return render_template('add_voiture.html', voiture={})  # Passer un dictionnaire vide pour éviter l'erreur



@app.route('/voitures/edit/<id>', methods=['GET', 'POST'])
def edit_voiture(id):
    voiture = collection.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        updated_voiture = {
            'Nom': request.form['nom'],
            'Marque': request.form['marque'],
            'date_dispo_debut': request.form['date_debut'],
            'date_dispo_fin': request.form['date_fin'],
            'statut': request.form['statut'],
            'prix': request.form['prix']
        }
        collection.update_one({'_id': ObjectId(id)}, {'$set': updated_voiture})
        return redirect('/voitures')
    return render_template('edit_voiture.html', voiture=voiture)

@app.route('/voitures/delete/<id>', methods=['POST', 'GET'])
def delete_voiture(id):
    collection.delete_one({'_id': ObjectId(id)})
    return redirect('/voitures')
