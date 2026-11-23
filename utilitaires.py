from flask import abort
from flask import Flask
import bd

def get_utilisateur_or_die(conn, identifiant):

    utilisateur = bd.get_utilisateur(
        conn,
        identifiant
    )

    if utilisateur is None:
        abort(404)

    return utilisateur

def get_carte_or_die(conn, identifiant):

    carte = bd.get_carte(
        conn,
        identifiant
    )

    if carte is None:
        abort(404)

    return carte