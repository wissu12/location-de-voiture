from flask import Flask, redirect, render_template, url_for
from pymongo import MongoClient

app = Flask(__name__)

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
database = client["location"]
reservations_collection = database["reservations"]
voitures_collection = database["voiture"]

# Route pour accepter une réservation
@app.route('/accepter/<reservation_id>')
def accepter_reservation(reservation_id):
    # Mettre à jour l'état de la réservation
    reservations_collection.update_one(
        {"_id": reservation_id},
        {"$set": {"etat": "acceptée"}}
    )

    # Rediriger vers la page des réservations
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
