"""
Couche d'accès à la base de données
"""
import types
import contextlib
import mysql.connector


@contextlib.contextmanager
def creer_connexion():
    """Crée une connexion à la BD"""
    conn = mysql.connector.connect(
        user="garneau",
        password="qwerty123",
        host="127.0.0.1",
        database="pokemon",
        raise_on_warnings=True
    )
    conn.get_curseur = types.MethodType(get_curseur, conn)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()


@contextlib.contextmanager
def get_curseur(self):
    """Retourne un curseur qui renvoie des dictionnaires"""
    curseur = self.cursor(dictionary=True, buffered=True)
    try:
        yield curseur
    finally:
        curseur.close()


def get_cartes_recentes(conn):
    """Retourne les 5 cartes les plus récentes"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            SELECT * FROM carte_pokemon
            ORDER BY date_sortie DESC LIMIT 5
        """)
        return curseur.fetchall()

def get_carte(conn, identifiant):
    """Retourne les informations d'une carte par son identifiant"""
    with conn.get_curseur() as curseur:
        curseur.execute("SELECT * FROM carte_pokemon WHERE id=%s", (identifiant,))
        return curseur.fetchone()

def rechercher_cartes(conn, nom):
    """Recherche des cartes par nom (partiel)"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            SELECT id, nom, supertype, rarete, types, illustrateur
            FROM carte_pokemon
            WHERE nom LIKE %s
            ORDER BY nom LIMIT 15
        """, (f"%{nom}%",))
        return curseur.fetchall()

def rechercher_cartes_collection(
    conn,
    nom,
    id_collectionneur=None
):
    """Recherche dans la collection"""

    with conn.get_curseur() as curseur:

        requete = """
            SELECT
                ec.id AS id_collection,
                cp.nom,
                cp.supertype,
                cp.rarete
            FROM elements_collection ec
            JOIN carte_pokemon cp
                ON cp.id = ec.id_carte
            WHERE cp.nom LIKE %s
        """

        parametres = [
            f"%{nom}%"
        ]

        if id_collectionneur is not None:

            requete += """
                AND ec.id_collectionneur = %s
            """

            parametres.append(
                id_collectionneur
            )

        requete += """
            ORDER BY cp.nom
            LIMIT 15
        """

        curseur.execute(
            requete,
            tuple(parametres)
        )

        return curseur.fetchall()

def get_carte_catalogue(conn, id_carte):
    """Retourne les informations d'une carte du catalogue"""
    with conn.get_curseur() as curseur:
        curseur.execute("SELECT * FROM carte_pokemon WHERE id = %s", (id_carte,))
        return curseur.fetchone()


# ---------- Collection ----------
# def get_cartes_collection(conn, id_collectionneur=None, statut=None):
#     """Liste les cartes de la collection (avec filtre optionnel)"""
#     with conn.get_curseur() as curseur:
#         requete = """
#             SELECT
#                 ec.id AS id_collection,
#                 ec.id_collectionneur,
#                 ec.date_ajout,
#                 ec.etat,
#                 ec.cout,
#                 ec.statut,
#                 ec.photo,
#                 cp.id AS id_carte,
#                 cp.nom,
#                 cp.supertype,
#                 cp.rarete
#             FROM elements_collection ec
#             JOIN carte_pokemon cp ON cp.id = ec.id_carte
#             WHERE 1=1
#         """
#         parametres = ()
#         if id_collectionneur is not None:
#             requete += " AND ec.id_collectionneur = %s"
#             parametres = (id_collectionneur,)
#         if statut is not None:
#             requete += " AND ec.statut = %s"
#             parametres = parametres + (statut,)
#         requete += " ORDER BY ec.date_ajout DESC"
#         curseur.execute(requete, parametres)
#         return curseur.fetchall()


def get_element_collection(conn, id_collection):
    """Retourne les informations d'un élément de collection par son identifiant"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            SELECT
                ec.*,
                cp.nom, cp.supertype, cp.rarete, cp.illustrateur,
                cp.extension, cp.serie, cp.editeur, cp.generation,
                cp.date_sortie, cp.numero_extension, cp.numero_pokedex, cp.types
            FROM elements_collection ec
            JOIN carte_pokemon cp ON cp.id = ec.id_carte
            WHERE ec.id = %s
        """, (id_collection,))
        return curseur.fetchone()


def ajouter_carte(conn, id_carte, id_collectionneur, date_ajout, etat, cout, statut, photo=None):
    """Ajoute une carte à la collection d'un utilisateur"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            INSERT INTO elements_collection
            (id_carte, id_collectionneur, date_ajout, etat, cout, statut, photo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_carte, id_collectionneur, date_ajout, etat, cout, statut, photo))


def modifier_carte(conn, id_collection, etat, cout, statut, photo=None):
    """Modifie les informations d'une carte dans la collection"""
    with conn.get_curseur() as curseur:
        if photo:
            curseur.execute("""
                UPDATE elements_collection
                SET etat=%s, cout=%s, statut=%s, photo=%s
                WHERE id=%s
            """, (etat, cout, statut, photo, id_collection))
        else:
            curseur.execute("""
                UPDATE elements_collection
                SET etat=%s, cout=%s, statut=%s
                WHERE id=%s
            """, (etat, cout, statut, id_collection))


def supprimer_carte(conn, id_collection):
    """Supprime une carte de la collection"""
    with conn.get_curseur() as curseur:
        curseur.execute("DELETE FROM elements_collection WHERE id=%s", (id_collection,))

def changer_collectionneur(conn, id_collection, nouveau_id_collectionneur):
    """Changer le collectionneur pour l'acceptation d'une offre """
    with conn.get_curseur() as curseur:
        curseur.execute("""
            UPDATE elements_collection
            SET id_collectionneur = %s
            WHERE id = %s
        """, (nouveau_id_collectionneur, id_collection))


def get_utilisateur(conn, identifiant):
    """Retourne les informations d'un utilisateur par son identifiant"""
    with conn.get_curseur() as curseur:
        curseur.execute("SELECT * FROM collectionneurs WHERE id=%s", (identifiant,))
        return curseur.fetchone()

def get_courriel_utilisateur(conn, identifiant):
    """Retourne le courriel d'un utilisateur par son identifiant"""
    with conn.get_curseur() as curseur:
        curseur.execute("SELECT courriel FROM collectionneurs WHERE id=%s", (identifiant,))
        result = curseur.fetchone()
        return result["courriel"] if result else None


def ajouter_utilisateur(conn, courriel, mot_de_passe, credit=0, role="collectionneur"):
    """Ajoute un nouvel utilisateur à la base de données"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            INSERT INTO collectionneurs (courriel, mot_de_passe, credit, role)
            VALUES (%s, %s, %s, %s)
        """, (courriel, mot_de_passe, credit, role))
        return curseur.lastrowid


def supprimer_utilisateur(conn, identifiant):
    """Supprime un utilisateur de la base de données"""
    with conn.get_curseur() as curseur:
        curseur.execute("DELETE FROM collectionneurs WHERE id=%s", (identifiant,))


def maj_credit(conn, id_utilisateur, nouveau_credit):
    """Met à jour le crédit d'un utilisateur"""
    with conn.get_curseur() as curseur:
        curseur.execute("UPDATE collectionneurs SET credit=%s WHERE id=%s",
                        (nouveau_credit, id_utilisateur))


# ---------- Offres ----------
def creer_offre(conn, id_elem_collection, id_collectionneur, prix_offert):
    """Cree une offre pour un élément de collection"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            INSERT INTO offres (id_elem_collection, id_collectionneur, prix_offert)
            VALUES (%s, %s, %s)
        """, (id_elem_collection, id_collectionneur, prix_offert))


def get_offres_pour_collectionneur(conn, id_proprietaire):
    """
    Offres en attente sur les cartes dont id_collectionneur
    (dans elements_collection) = id_proprietaire
    """
    with conn.get_curseur() as curseur:
        curseur.execute("""
            SELECT
                o.id AS id_offre,
                o.prix_offert AS montant,
                o.date AS date_offre,
                o.statut,
                o.id_collectionneur AS acheteur_id,
                o.id_elem_collection AS id_collection,
                ec.cout,
                cp.nom AS nom_carte,
                c.courriel AS acheteur
            FROM offres o
            JOIN elements_collection ec ON ec.id = o.id_elem_collection
            JOIN carte_pokemon cp ON cp.id = ec.id_carte
            JOIN collectionneurs c ON c.id = o.id_collectionneur
            WHERE ec.id_collectionneur = %s
              AND o.statut = 'en attente'
            ORDER BY o.date DESC
        """, (id_proprietaire,))
        return curseur.fetchall()


def get_offre(conn, id_offre):
    """Retourne les informations d'une offre par son identifiant"""
    with conn.get_curseur() as curseur:
        curseur.execute(
            "SELECT * FROM offres WHERE id = %s",
            (id_offre,)
        )
        return curseur.fetchone()


def maj_statut_offre(conn, id_offre, statut):
    """statut : 'en attente', 'acceptée' ou 'refusée'"""
    with conn.get_curseur() as curseur:
        curseur.execute(
            "UPDATE offres SET statut = %s WHERE id = %s",
            (statut, id_offre)
        )


def a_des_offres_en_attente(conn, id_elem_collection):
    """True si la carte a au moins une offre en attente"""
    with conn.get_curseur() as curseur:
        curseur.execute("""
            SELECT COUNT(*) AS nb
            FROM offres
            WHERE id_elem_collection = %s
              AND statut = 'en attente'
        """, (id_elem_collection,))
        row = curseur.fetchone()
        return row and row["nb"] > 0

# ---------- AJAX / API ----------

def soft_delete_utilisateur(conn, identifiant):
    """Marque un utilisateur comme supprimé (soft delete)."""
    with conn.get_curseur() as curseur:
        curseur.execute(
            "UPDATE collectionneurs SET supprime = 1 WHERE id = %s",
            (identifiant,)
        )


def soft_delete_carte(conn, id_collection):
    """Marque une carte comme supprimée (soft delete)."""
    with conn.get_curseur() as curseur:
        curseur.execute(
            "UPDATE elements_collection SET supprime = 1 WHERE id = %s",
            (id_collection,)
        )


def get_utilisateur_par_courriel(conn, courriel):
    """Retourne un utilisateur par son courriel, en ignorant les utilisateurs supprimés."""
    with conn.get_curseur() as curseur:
        curseur.execute(
            """
            SELECT * FROM collectionneurs
            WHERE courriel = %s AND (supprime = 0 OR supprime IS NULL)
            """,
            (courriel,)
        )
        return curseur.fetchone()


def get_collectionneurs(conn):
    """Retourne tous les collectionneurs actifs (non supprimés)."""
    with conn.get_curseur() as curseur:
        curseur.execute(
            """
            SELECT id, courriel, credit, role
            FROM collectionneurs
            WHERE (supprime = 0 OR supprime IS NULL)
            ORDER BY courriel
            """
        )
        return curseur.fetchall()


def get_cartes_collection(conn, id_collectionneur=None, statut=None, offset=0, limit=None):
    """Liste les cartes de la collection (avec filtre optionnel)"""
    with conn.get_curseur() as curseur:
        requete = """
            SELECT
                ec.id AS id_collection, ec.id_collectionneur,
                ec.date_ajout, ec.etat, ec.cout, ec.statut, ec.photo,
                cp.id AS id_carte, cp.nom, cp.supertype, cp.rarete
            FROM elements_collection ec
            JOIN carte_pokemon cp ON cp.id = ec.id_carte
            WHERE (ec.supprime = 0 OR ec.supprime IS NULL)
        """
        params = []

        if id_collectionneur is not None:
            requete += " AND ec.id_collectionneur = %s"
            params.append(id_collectionneur)

        if statut is not None:
            requete += " AND ec.statut = %s"
            params.append(statut)

        requete += " ORDER BY ec.date_ajout DESC"

        if limit is not None:
            requete += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        curseur.execute(requete, tuple(params))
        return curseur.fetchall()


def rechercher_suggestions(conn, terme, limite=8):
    """Retourne des noms de cartes correspondants pour l'autocomplétion."""
    with conn.get_curseur() as curseur:
        curseur.execute(
            """
            SELECT DISTINCT nom
            FROM carte_pokemon
            WHERE nom LIKE %s
            ORDER BY nom
            LIMIT %s
            """,
            (f"%{terme}%", limite)
        )
        return [row["nom"] for row in curseur.fetchall()]


def get_cartes_pour_api(conn, filtre=None, id_collectionneur=None, offset=0, limit=6, recherche=None):
    """Récupère les cartes paginées (infinite scroll + polling)."""
    with conn.get_curseur() as curseur:
        requete = """
            SELECT
                ec.id AS id_collection, ec.id_collectionneur,
                ec.date_ajout, ec.etat, ec.cout, ec.statut, ec.photo,
                cp.id AS id_carte, cp.nom, cp.supertype, cp.rarete
            FROM elements_collection ec
            JOIN carte_pokemon cp ON cp.id = ec.id_carte
            WHERE (ec.supprime = 0 OR ec.supprime IS NULL)
        """
        params = []

        if id_collectionneur is not None:
            requete += " AND ec.id_collectionneur = %s"
            params.append(id_collectionneur)

        if filtre == "disponibles":
            requete += " AND ec.statut = 1"
        elif filtre == "recherchees":
            requete += " AND ec.statut = 0"

        if recherche and len(recherche) >= 2:
            requete += " AND cp.nom LIKE %s"
            params.append(f"%{recherche}%")

        requete += " ORDER BY ec.date_ajout DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        curseur.execute(requete, tuple(params))
        return curseur.fetchall()

def recherche_carte(
    conn,
    nom,
    id_collectionneur=None
):
    """Recherche carte"""

    with conn.get_curseur() as curseur:

        requete = """
            SELECT
                ec.id AS id_collection,
                cp.nom,
                cp.supertype,
                cp.rarete
            FROM elements_collection ec
            JOIN carte_pokemon cp
                ON cp.id = ec.id_carte
            WHERE cp.nom LIKE %s
        """

        parametres = [
            f"%{nom}%"
        ]

        if id_collectionneur is not None:

            requete += """
                AND ec.id_collectionneur = %s
            """

            parametres.append(
                id_collectionneur
            )

        requete += """
            ORDER BY cp.nom
            LIMIT 15
        """

        curseur.execute(
            requete,
            tuple(parametres)
        )

        return curseur.fetchall()