"use strict";

let controleurRecherche = null;

function getRecherches() {
    try {
        return JSON.parse(localStorage.getItem("dernieres_recherches")) || [];
    } catch (e) {
        return [];
    }
}

function sauverRecherche(terme) {
    if (!terme || terme.length < 2) return;

    let liste = getRecherches().filter(r => r.toLowerCase() !== terme.toLowerCase());
    liste.unshift(terme);
    liste = liste.slice(0, 8);
    localStorage.setItem("dernieres_recherches", JSON.stringify(liste));
}


async function faireRecherche() {
    const input = document.getElementById("recherche-accueil");
    const boite = document.getElementById("suggestions-accueil");
    if (!input || !boite) return;

    const terme = input.value.trim();

    if (terme.length < 2) {
        boite.innerHTML = "";
        boite.classList.add("d-none");
        return;
    }

    if (controleurRecherche !== null) {
        controleurRecherche.abort();
    }
    controleurRecherche = new AbortController();

    try {
        const suggestions = await envoyerRequeteAjax(
            "/api/suggestions",
            "GET",
            { q: terme },
            controleurRecherche
        );

        boite.innerHTML = "";

        if (suggestions.length === 0) {
            boite.classList.add("d-none");
            return;
        }

        suggestions.forEach(function (nom) {
            const bouton = document.createElement("button");
            bouton.type = "button";
            bouton.className = "list-group-item list-group-item-action";
            bouton.textContent = nom;

            bouton.addEventListener("click", function () {
                input.value = nom;
                boite.innerHTML = "";
                boite.classList.add("d-none");
                sauverRecherche(nom);
            });

            boite.appendChild(bouton);
        });

        boite.classList.remove("d-none");
        controleurRecherche = null;

    } catch (err) {
        if (err.name !== "AbortError") {
            console.error("Erreur recherche :", err);
        }
    }
}

async function verifierCourriel() {
    const champ = document.getElementById("courriel");
    const msg = document.getElementById("feedback-courriel");
    const bouton = document.querySelector("form button[type=submit]");

    if (!champ) return;

    const valeur = champ.value.trim();
    if (valeur === "") {
        champ.classList.remove("is-invalid", "is-valid");
        if (msg) msg.textContent = "";
        if (bouton) bouton.disabled = false;
        return;
    }

    try {
        const data = await envoyerRequeteAjax(
            "/api/verifier-courriel",
            "GET",
            { courriel: valeur }
        );

        if (data.existe) {
            champ.classList.add("is-invalid");
            champ.classList.remove("is-valid");
            if (msg) {
                msg.textContent = "Ce courriel existe déjà.";
                msg.className = "invalid-feedback d-block";
            }
            if (bouton) bouton.disabled = true;
        } else {
            champ.classList.remove("is-invalid");
            champ.classList.add("is-valid");
            if (msg) msg.textContent = "";
            if (bouton) bouton.disabled = false;
        }
    } catch (err) {
        console.error("Erreur validation courriel :", err);
    }
}

async function supprimerUtilisateur(id, ligne) {
    if (!confirm("Voulez-vous vraiment supprimer cet utilisateur ?")) {
        return;
    }

    try {
        await envoyerRequeteAjax(
            "/api/utilisateurs/" + id,
            "DELETE"
        );

        // Disparition douce
        ligne.style.transition = "opacity 0.3s";
        ligne.style.opacity = "0";
        setTimeout(function () {
            ligne.remove();
        }, 300);

    } catch (err) {
        alert("Erreur lors de la suppression : " + err.message);
    }
}


let offset = 0;
let enCours = false;
let fini = false;
const LIMIT_INITIAL = 6;
const LIMIT_SUITE = 3;

async function chargerCartes(premiereFois) {
    if (enCours || fini) return;
    enCours = true;

    const loader = document.getElementById("loader-cartes");
    if (loader) loader.classList.remove("d-none");

    const limite = premiereFois ? LIMIT_INITIAL : LIMIT_SUITE;

    const filtre = document.body.dataset.filtre || "";
    const recherche = document.body.dataset.recherche || "";

    const params = {
        offset: offset,
        limit: limite
    };
    if (filtre) params.filtre = filtre;
    if (recherche) params.recherche = recherche;

    try {
        const data = await envoyerRequeteAjax("/api/cartes", "GET", params);

        const conteneur = document.getElementById("liste-cartes");
        if (premiereFois) {
            conteneur.innerHTML = "";
        }

        data.cartes.forEach(function (carte) {
            const photo = carte.photo
                ? "/static/images/ajouts/" + carte.photo
                : "/static/image/pikachu.jpg";

            const div = document.createElement("div");
            div.className = "col-12 col-md-6 col-lg-4";
            div.innerHTML = `
                <div class="poke-card">
                    <a href="/collection/detail/${carte.id_collection}">
                        <div class="card-img-wrap">
                            <img src="${photo}" alt="${carte.nom}">
                        </div>
                    </a>
                    <div class="card-body">
                        <h5 class="card-title">${carte.nom}</h5>
                        <p class="card-text">
                            ${carte.etat || ""} 
                            ${carte.cout != null ? " · " + carte.cout.toFixed(2) + " $" : ""}
                        </p>
                    </div>
                    <div>
                        <a
                            href="api/ajout-envie/${carte.id_carte}"
                            class="btn btn-success btn-sm">

                            Ajouter aux envies

                        </a>
                    </div>
                </div>`;
            conteneur.appendChild(div);
        });

        offset += data.cartes.length;
        fini = !data.has_more;
        enCours = false;
        if (loader) loader.classList.add("d-none");

    } catch (err) {
        console.error("Erreur chargement cartes :", err);
        enCours = false;
        if (loader) loader.classList.add("d-none");
    }
}

function gererDefilement() {
    if ((window.innerHeight + window.scrollY) >= 0.95 * document.body.offsetHeight) {
        chargerCartes(false);   // +3 cartes
    }
}


function initialisation() {
    // === Recherche ===
    const inputRecherche = document.getElementById("recherche-accueil");
    if (inputRecherche) {
        inputRecherche.addEventListener("input", faireRecherche);

        inputRecherche.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                sauverRecherche(inputRecherche.value.trim());
            }
        });
    }

    const champCourriel = document.getElementById("courriel");
    if (champCourriel) {
        champCourriel.addEventListener("blur", verifierCourriel);

        champCourriel.addEventListener("input", function () {
            if (champCourriel.classList.contains("is-invalid")) {
                verifierCourriel();
            }
        });
    }


    const listeCartes = document.getElementById("liste-cartes");
    if (listeCartes) {

        chargerCartes(true);

        window.addEventListener("scroll", gererDefilement);

        setInterval(function () {
            if (window.scrollY < 200) {
                offset = 0;
                fini = false;
                chargerCartes(true);
            }
        }, 5000);
    }
}

window.addEventListener("load", initialisation);