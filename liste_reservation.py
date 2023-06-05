
from flask import Flask, redirect, render_template, url_for,make_response,session,request
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import send_from_directory
import os

from pymongo import MongoClient

app = Flask(__name__)

# Configuration du dossier d'uploads
app.config['UPLOAD_FOLDER'] = 'static'

app.secret_key = "location_voiture"
# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
database = client["location"]
reservations_collection = database["reservations"]
voitures_collection = database["voiture"]
utilisateur_collection = database["utilisateur"]
client_collection = database["clients"]


# Route pour accepter une réservation
@app.route('/accepter_reservation/<reservation_id>')
def accepter_reservation(reservation_id):
    # Mettre à jour l'état de la réservation
    
    reservations_collection.update_one(
    {"_id": ObjectId(reservation_id)},
    {"$set": {"statut": "acceptée"}}
)

    voiture_reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
    matricule = voiture_reservation['matricule']

    voitures_collection.update_one(
        {"matricule": matricule},
        {"$set": {"statut": "reserve"}}
    )


    # Rediriger vers la page des réservations
    return redirect('/liste_reservations')



    # Route pour refuser une réservation
@app.route('/refuser/<reservation_id>')
def refuser_reservation(reservation_id):
    # Mettre à jour l'état de la réservation
    reservations_collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"statut": "refusée"}}
    )

    # Rediriger vers la page des réservations
    return redirect('/liste_reservations')


# Route pour afficher les réservations dans un tableau

# Route pour afficher les réservations dans un tableau

#hajar 
    
# la list des clients 
@app.route('/clients', methods=['GET'])
def client_list():
    if 'user_id' in session:
        clients = client_collection.find()
        success_message = request.args.get('success')
        return render_template('client_list.html', clients=clients, success=success_message)
    else:
        return redirect('/login')

# Ajouter Client
@app.route('/add-client', methods=['GET', 'POST'])
def addClient():
    if 'user_id' in session:
        if request.method == 'POST':
            nom = request.form['nom']
            prenom = request.form['prenom']
            telephone= request.form['tel']
            cin = request.form['cin']
            email = request.form['email']


            if client_collection.find_one({'$or': [{'email': email}, {'cin': cin}]}):
                return render_template('add-client.html' , error='L\'email ou le cin existe déjà dans la base de données.')

            client = {
                'nom': nom,
                'prenom': prenom,
                'cin': cin,
                'email': email,
                'telephone':telephone
            }

            try:
                # Insérer le client dans la base de données
                client_collection.insert_one(client)
                return  redirect(url_for('client_list', success='Client ajouté avec succès !'))
            except DuplicateKeyError:
                return render_template('add-client.html' , error='L\'email ou le cin existe déjà dans la base de données.') 

        return render_template('add-client.html')
    else:
        return redirect('/login')


#Update Client
@app.route('/edit-client/<client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    if 'user_id' in session:
        client = client_collection.find_one({'_id': ObjectId(client_id)})

        if request.method == 'POST':
            # Retrieve the updated information from the form
            nom = request.form['nom']
            prenom = request.form['prenom']
            telephone = request.form['telephone']
            email = request.form['email']

            # Update the client's information in the database
            client_collection.update_one(
                {'_id': ObjectId(client_id)},
                {'$set': {
                    'nom': nom,
                    'prenom': prenom,
                    'telephone': telephone,
                    'email': email
                }}
            )

            # Redirect to the client list or display a success message
            return redirect(url_for('client_list' ,success='Client a été modifier avec succès' ))

        # Handle GET request to display the edit form
        return render_template('edit_client.html', client=client)
    else:
        return redirect(url_for('login'))


# DELETE CLIENT
@app.route('/delete-client/<client_id>', methods=['GET', 'POST'])
def delete_client(client_id):

    if request.method == 'POST':
        client_collection.delete_one({'_id': ObjectId(client_id)})
        return redirect(url_for('client_list'))
    else:
        # Code pour afficher la page de liste des clients
        clients = client_collection.find()
        return render_template('list.html', clients=clients)


# list des managers 

@app.route('/managers', methods=['GET'])
def list_manager():
    if 'user_id' in session:
        managers = utilisateur_collection.find({"role": "manager"})
        success_message = request.args.get('success')
        return render_template('list_manager.html', managers=managers,success=success_message)
    else:
        return redirect(url_for('login'))

# Admin and Manager : AJOUTER
@app.route('/add-user',methods=['GET','POST'])
def addUser():
    if 'user_id' in session:
        if request.method == 'POST':
            nom = request.form['nom']
            prenom = request.form['prenom']
            telephone =request.form['telephone']
            email = request.form['email']
            cin = request.form['cin']
            role = request.form['role']
            password = request.form['password']

            if utilisateur_collection.find_one({'$or': [{'email': email}, {'cin': cin}]}):
                return render_template('add-user.html',error='L\'email ou le cin existe déjà dans la base de données.')

            user ={
                'nom': nom,
                'prenom': prenom,
                'cin': cin,
                'email': email,
                'telephone':telephone,
                'password':password,
                'role': role
            }
            try:
                # Insérer le client dans la base de données
                utilisateur_collection.insert_one(user)
                if role == 'admin':
                    return redirect(url_for('list_admin', success='Administrateur ajouté avec succès !'))
                elif role == 'manager':
                    return redirect(url_for('list_manager', success='Manager ajouté avec succès !'))
            except DuplicateKeyError:
                return render_template('add-user.html',error='L\'email ou le cin existe déjà dans la base de données.')
        return render_template('add-user.html')
    else:
        return redirect(url_for('login'))

#DELETE MANAGER 

@app.route('/delete-manager/<manager_id>', methods=['GET', 'POST'])
def delete_manager(manager_id):
    if 'user_id' in session:
        if request.method == 'POST':
            utilisateur_collection.delete_one({'_id': ObjectId(manager_id)})
            return redirect(url_for('list_manager'))
        else:
            # Code pour afficher la page de liste des clients
            managers = utilisateur_collection.find({"role": "manager"})
            return render_template('list_manager', managers=managers)
    else:
        return redirect(url_for('login'))

#MODIFIER MANAGER:
@app.route('/edit-manager/<manager_id>', methods=['GET', 'POST'])
def edit_manager(manager_id):
    if 'user_id' in session:
        if request.method == 'POST':
            nom = request.form['nom']
            prenom = request.form['prenom']
            telephone = request.form['telephone']
            email = request.form['email']
            cin = request.form['cin']
            role = request.form['role']


            user = {
                'nom': nom,
                'prenom': prenom,
                'cin': cin,
                'email': email,
                'telephone': telephone,
                'role': role
            }

            try:
                # Update the user in the database
                utilisateur_collection.update_one({'_id': ObjectId(manager_id)}, {'$set': user})
                return redirect(url_for('list_manager', success='Manager a été modifier avec succès '))
            except Exception as e:
                return 'An error occurred while updating the user.'

        else:
            # Retrieve the user from the database
            manager = utilisateur_collection.find_one({'_id': ObjectId(manager_id)})
            return render_template('edit_manager.html', manager=manager)
    else:
        return redirect(url_for('login'))


@app.route('/admins', methods=['GET'])
def list_admin():
    if 'user_id' in session:
        admins = utilisateur_collection.find({"role": "admin"})
        success_message = request.args.get('success')
        return render_template('list_admin.html', admins=admins,success=success_message)
    else:
        return redirect(url_for('login'))

@app.route('/update-password', methods=['POST','GET'])
def update_password():
    if 'user_id' in session:
        if request.method =='POST':
            user_id = session['user_id']
            old_password = request.form.get('current_password')
            new_password = request.form.get('password')
            confirm_password = request.form.get('password_confirmation')

            user = utilisateur_collection.find_one({'_id':ObjectId(user_id)})
            # print(user.password)
            if user and user['password'] == old_password:
                if new_password == confirm_password:
                    utilisateur_collection.update_one({'_id': user_id}, {'$set': {'password': new_password}})
                    return redirect('/')  # Redirect to the profile page
                else:
                    return render_template('update_password.html', error='Le mot de passe de confirmation ne correspond pas')
            else:
                return render_template('update_password.html', error='Mot de passe actuel incorrect')
        else:
            user_id = session['user_id']
            user = utilisateur_collection.find_one({'_id':ObjectId(user_id)})
            return render_template('update_password.html',utilisateur=user)
    else:
        return redirect('/login')

@app.route('/')
def home_page():
    return render_template('index.htm')



@app.route('/edit_mon_compte', methods=['GET','POST'])
def edit_mon_compte():
    if 'user_id'  in session:
        user_id = session['user_id']
        if request.method== 'POST':
                nouveau_nom = request.form.get('nom')
                nouveau_email = request.form.get('email')
                nouveau_prenom = request.form.get('prenom')
                nouveau_cin = request.form.get('cin')
                nouveau_telephone = request.form.get('telephone')

                user = {
                'nom': nouveau_nom,
                'prenom': nouveau_prenom,
                'cin': nouveau_cin,
                'email': nouveau_email,
                'telephone': nouveau_telephone,
                }
                utilisateur_collection.update_one({'_id': ObjectId(user_id)}, {'$set': user})
                return redirect(url_for('show_reservations'))
        else:
            user = utilisateur_collection.find_one({'_id': ObjectId(user_id)})
            return render_template('edit_mon_profile.html', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = utilisateur_collection.find_one({'email': email, 'password': password})
        
        if user:
            # session['user_id'] = user['_id']
            session['user_id'] = str(user['_id'])
            if user['role'] == 'admin':
                return redirect('/admin')
            else:
                return redirect('/Manager')
        else:
            return render_template('login.html', error='Identifiants incorrects')
    else:
        return render_template('login.html')
    

@app.route('/liste_reservations')
def liste_reservations():

    reservations = reservations_collection.aggregate([
        {
            "$match": {"statut": "en_attente"}
        },
        {
            "$lookup": {
                "from": "clients",
                "localField": "cin_client",
                "foreignField": "cin",
                "as": "clients"
            }
        },
        {
            "$lookup": {
                "from": "voiture",
                "localField": "matricule",
                "foreignField": "matricule",
                "as": "voiture"
            }
        },
        {
            "$unwind": "$clients"
        },
        {
            "$unwind": "$voiture"
        },
        {
            "$project": {

                "_id": 1,
                "matricule":1,
                "cin_client": 1,
                "date_debut_reserv": 1,
                "date_fin_reserv": 1,
                "statut": 1,
                "clients.nom": 1,
                 "clients.prenom": 1,
                "voiture.Nom": 1,
                  "voiture.prix": 1
            }
        }
    ])
    return render_template('liste_reservation.html', reservations=reservations)





@app.route('/historique')
def show_historique():
  


    historique = reservations_collection.aggregate([
        {
            "$match": {"statut": {"$ne": "en_attente"}}
        },
        {
            "$lookup": {
                "from": "clients",
                "localField": "cin_client",
                "foreignField": "cin",
                "as": "clients"
            }
        },
        {
            "$lookup": {
                "from": "voiture",
                "localField": "matricule",
                "foreignField": "matricule",
                "as": "voiture"
            }
        },
        {
            "$unwind": "$clients"
        },
        {
            "$unwind": "$voiture"
        },
        {
            "$project": {
                "_id": 1,
                "matricule": 1,
                "cin_client": 1,
                "date_debut_reserv": 1,
                "date_fin_reserv": 1,
                "statut": 1,
                "client_nom": "$clients.nom",
                "client_prenom": "$clients.prenom",
                "voiture_nom": "$voiture.Nom",
                "voiture_prix": "$voiture.prix"
            }
        }
    ])

    return render_template('Historique.html', historique=historique)

    

    # Route pour afficher le détail  d'une réservation
@app.route('/show_detail/<reservation_id>')
def show_detail_reservation(reservation_id):
    # Rechercher la réservation spécifique d/ans la base de données
 

    reservation = reservations_collection.aggregate([
            {
                "$match": {"_id": ObjectId(reservation_id)}
            },
            {
                "$lookup": {
                    "from": "clients",
                    "localField": "cin_client",
                    "foreignField": "cin",
                    "as": "clients"
                }
            },
            {
                "$lookup": {
                    "from": "voiture",
                    "localField": "matricule",
                    "foreignField": "matricule",
                    "as": "voiture"
                }
            },
            {
                "$unwind": "$clients"
            },
            {
                "$unwind": "$voiture"
            },
            {
                "$project": {
                    "_id": 1,
                    "matricule": 1,
                    "cin_client": 1,
                    "date_debut_reserv": 1,
                    "date_fin_reserv": 1,
                    "statut": 1,
                    "client_nom": "$clients.nom",
                    "client_prenom": "$clients.prenom",
                     "voiture_marque": "$voiture.Marque",
                    "voiture_nom": "$voiture.Nom",
                    "voiture_prix": "$voiture.prix",
                    "photo":"$voiture.photo"
                }
            }
            ])

    return render_template('show_detail_reservation.html', reservation=reservation)
@app.route('/voitures', methods=['GET'])
def get_voitures():
    voitures =  voitures_collection.find()
    return render_template('voitures.html', voitures=voitures)




@app.route('/voitures_encours_reservation', methods=['GET'])
def voitures_encours_reservation():
    voitures_non_disponibles = voitures_collection.find({"statut": {"$ne": "disponible"}})
    return render_template('fin-reserva.html', voitures=voitures_non_disponibles)



@app.route('/terminer_reservation/<id>', methods=['GET'])
def terminer_reservation(id):
    # Mettre à jour l'état de la réservation
    voitures_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"statut": "disponible"}}
    )

    # Rediriger vers la page des réservations
    return redirect('/voitures_encours_reservation')

@app.route('/reserver')
def reserver():
    return render_template('formulaire_reservation.html')


@app.route('/new')
def new():
    return render_template('new_j.html')


@app.route('/liste_voitures', methods=['GET'])
def liste_voitures():
    voitures =  voitures_collection.find()
    return render_template('liste_voiture.html', voitures=voitures)
   

@app.route('/voitures/delete/<id>', methods=['POST', 'GET'])
def delete_voiture(id):
    voitures_collection.delete_one({'_id': ObjectId(id)})
    return redirect('/voitures')


@app.route('/voitures/edit/<id>', methods=['GET', 'POST'])
def edit_voiture(id):
    voiture = voitures_collection.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        updated_voiture = {
            'Nom': request.form['nom'],
            'Marque': request.form['marque'],
            'date_dispo_debut': request.form['date_debut'],
            'date_dispo_fin': request.form['date_fin'],
            'statut': request.form['statut'],
            'prix': request.form['prix']
        }
        voitures_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_voiture})
        return redirect('/voitures')
    return render_template('edit_voiture.html', voiture=voiture)


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
            'matricule':matricule,
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
        voiture_id = voitures_collection.insert_one(voiture)

        return redirect('/voitures')

    return render_template('add_voiture.html', voiture={})  # Passer un dictionnaire vide pour éviter l'erreur
# Route pour afficher le détail d'une réservation


@app.route('/Manager')
def manager_dash():
    # Effectuer la requête pour récupérer les réservations en attente
    reservations_en_attente = reservations_collection.count_documents({"statut": "en_attente"})

    # Effectuer la requête pour récupérer les réservations acceptées
    reservations_acceptees = reservations_collection.count_documents({"statut": "acceptée"})
    reservations_refuses = reservations_collection.count_documents({"statut": "refusée"})
    nombre_clients = client_collection.count_documents({})
    nombre_admin = utilisateur_collection.count_documents({"role":"admin"})
    nombre_manager = utilisateur_collection.count_documents({"role":"manager"})
    nombre_voitures = voitures_collection.count_documents({"statut":"disponible"})
    nombre_voitures_total = voitures_collection.count_documents({})
    

    # Passer les nombres de réservations en attente et acceptées à la template 'index.html'
    return render_template('manager_dashboard.html',nombre_voitures=nombre_voitures,nombre_admin=nombre_admin,nombre_manager=nombre_manager, nombre_clients=nombre_clients,nombre_reservations_en_attente=reservations_en_attente, nombre_reservations_acceptees=reservations_acceptees
                          ,nombre_voitures_total=nombre_voitures_total , nombre_reservations_refuses=reservations_refuses)



@app.route('/admin')
def admin():
    # Effectuer la requête pour récupérer les réservations en attente
    reservations_en_attente = reservations_collection.count_documents({"statut": "en_attente"})

    # Effectuer la requête pour récupérer les réservations acceptées
    reservations_acceptees = reservations_collection.count_documents({"statut": "acceptée"})
    reservations_refuses = reservations_collection.count_documents({"statut": "refusée"})
    nombre_clients = client_collection.count_documents({})
    nombre_admin = utilisateur_collection.count_documents({"role":"admin"})
    nombre_manager = utilisateur_collection.count_documents({"role":"manager"})
    nombre_voitures = voitures_collection.count_documents({"statut":"disponible"})
    nombre_voitures_total = voitures_collection.count_documents({})
    

    # Passer les nombres de réservations en attente et acceptées à la template 'index.html'
    return render_template('index.html',nombre_voitures=nombre_voitures,nombre_admin=nombre_admin,nombre_manager=nombre_manager, nombre_clients=nombre_clients,nombre_reservations_en_attente=reservations_en_attente, nombre_reservations_acceptees=reservations_acceptees
                          ,nombre_voitures_total=nombre_voitures_total , nombre_reservations_refuses=reservations_refuses)

#nada
#filtrage de date 


@app.route('/voitures/<voiture_id>/reserve', methods=['GET', 'POST'])
def afficher_formulaire_reservation(voiture_id):
    voiture_id = ObjectId(voiture_id)  # Convertir l'ID de la voiture en ObjectId
    reservation_effectuee = False  # Variable pour indiquer si la réservation a été effectuée avec succès
    clients = client_collection.find({})
    if request.method == 'POST':
            # Récupérer les détails de la voiture
            voiture = voitures_collection.find_one({'_id': voiture_id})
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
                'matricule': voiture.get('matricule', ''),
                'prix':voiture.get('prix',''),
                'cin_client': request.form.get('cin_client'),
                'date_debut_reserv': date_debut,
                'date_fin_reserv': date_fin,
                'statut': request.form.get('statut', 'en_attente')
            }
            reservations_collection.insert_one(reservation)
            reservation_effectuee = True  # Mettre la variable à True après l'enregistrement de la réservation

            return redirect('/voitures')

    voiture = voitures_collection.find_one({'_id': voiture_id})
    if voiture:
        nom_voiture = voiture.get('Nom', '')
        matricule = voiture.get('matricule', '')
        prix= voiture.get('prix','')
        return render_template('formulaire_reservation.html', clients=clients,nom_voiture=nom_voiture, matricule=matricule,prix=prix, voiture_id=voiture_id, reservation_effectuee=reservation_effectuee)
    else:
        return redirect('/voitures')
    
@app.route('/voitures/search', methods=['GET'])
def rechercher_voitures():
    date_debut_str = request.args.get('date_debut')
    date_fin_str = request.args.get('date_fin')

    voitures = voitures_collection.find({
        'date_dispo_debut': {'$gte': date_debut_str},
        'date_dispo_fin': {'$lte': date_fin_str},
    })

    return render_template('table_voitures.html', voitures=voitures)





if __name__ == '__main__':
    app.run(debug=True)
