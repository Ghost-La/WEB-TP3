from flask import session
from flask import abort


def utilisateur_connecte():
    """Verifie qu'un utilisateur est connecte, sinon 401"""
    if "id" not in session:
        abort(401)


def administrateur():
    """Verifie que l'utilisateur est admin, sinon 401 ou 403"""
    if "id" not in session:
        abort(401)

    if session.get("role") != "admin":
        abort(403)


def est_connecte():
    """Retourne True si un utilisateur est connecte"""
    return "id" in session


def est_admin():
    """Retourne True si l'utilisateur connecte est admin"""
    return session.get("role") == "admin"