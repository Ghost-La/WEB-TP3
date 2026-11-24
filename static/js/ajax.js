// ---------- 1. Local Storage (se souvenir des recherches) ----------
const CLE = "dernieres_recherches";

function getRecherches() {
    try {
        return JSON.parse(localStorage.getItem(CLE)) || [];
    } catch (e) {
        return [];
    }
}

function sauverRecherche(terme) {
    if (!terme || terme.length < 2) return;

    let liste = getRecherches().filter(function (r) {
        return r.toLowerCase() !== terme.toLowerCase();
    });
    liste.unshift(terme);          // on met la nouvelle en premier
    liste = liste.slice(0, 8);     // on garde max 8
    localStorage.setItem(CLE, JSON.stringify(liste));
}


// ---------- 2. Suggestions de recherche (accueil) ----------
function initialiserRecherche(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const boite = document.getElementById(suggestionsId);

    if (!input || !boite) return;

    let timer = null;

    // Quand on tape
    input.addEventListener("input", function () {
        clearTimeout(timer);
        const texte = input.value.trim();

        // Moins de 2 caractères → on cache
        if (texte.length < 2) {
            boite.innerHTML = "";
            boite.classList.add("d-none");
            return;
        }

        // On attend 250 ms pour ne pas spammer le serveur
        timer = setTimeout(function () {
            fetch("/api/suggestions?q=" + encodeURIComponent(texte))
                .then(function (reponse) { return reponse.json(); })
                .then(function (suggestions) {
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
                            // On peut laisser l’utilisateur appuyer sur Entrée
                            // ou forcer le submit si tu veux :
                            // input.form.submit();
                        });

                        boite.appendChild(bouton);
                    });

                    boite.classList.remove("d-none");
                });
        }, 250);
    });

    // Quand on appuie sur Entrée → on sauvegarde
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            sauverRecherche(input.value.trim());
        }
    });

    // Cacher les suggestions si on clique ailleurs
    document.addEventListener("click", function (e) {
        if (!input.contains(e.target) && !boite.contains(e.target)) {
            boite.classList.add("d-none");
        }
    });
}


// ---------- 3. Validation du courriel (création de compte) ----------
function initialiserValidationCourriel() {
    const champ = document.getElementById("courriel");
    const message = document.getElementById("feedback-courriel");
    const bouton = document.querySelector("form button[type=submit]");

    if (!champ) return;

    function verifier() {
        const courriel = champ.value.trim();

        if (courriel === "") {
            champ.classList.remove("is-invalid", "is-valid");
            if (message) message.textContent = "";
            if (bouton) bouton.disabled = false;
            return;
        }

        // Appel AJAX
        fetch("/api/verifier-courriel?courriel=" + encodeURIComponent(courriel))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.existe) {
                    // Courriel déjà pris
                    champ.classList.add("is-invalid");
                    champ.classList.remove("is-valid");
                    if (message) {
                        message.textContent = "Ce courriel existe déjà.";
                        message.className = "invalid-feedback d-block";
                    }
                    if (bouton) bouton.disabled = true;
                } else {
                    // Courriel libre
                    champ.classList.remove("is-invalid");
                    champ.classList.add("is-valid");
                    if (message) message.textContent = "";
                    if (bouton) bouton.disabled = false;
                }
            });
    }

    // Quand on quitte le champ
    champ.addEventListener("blur", verifier);

    // Si le champ était invalide, on re-vérifie pendant qu’on tape
    champ.addEventListener("input", function () {
        if (champ.classList.contains("is-invalid")) {
            verifier();
        }
    });
}


// ---------- 4. Soft delete d’un utilisateur ----------
function supprimerUtilisateur(id, ligne) {
    if (!confirm("Voulez-vous vraiment supprimer cet utilisateur ?")) {
        return;
    }

    fetch("/api/utilisateurs/" + id, {
        method: "DELETE"
    })
    .then(function (reponse) {
        if (!reponse.ok) {
            throw new Error("Erreur " + reponse.status);
        }
        return reponse.json();
    })
    .then(function () {
        // On fait disparaître la ligne sans recharger la page
        ligne.style.transition = "opacity 0.3s";
        ligne.style.opacity = "0";
        setTimeout(function () {
            ligne.remove();
        }, 300);
    })
    .catch(function (err) {
        alert("Erreur lors de la suppression : " + err.message);
    });
}


// ---------- 5. Infinite scroll + polling (accueil) ----------
function demarrerAffichageCartes(options) {
    const conteneur = document.getElementById(options.conteneurId);
    const loader = document.getElementById(options.loaderId);

    let offset = 0;
    let enCours = false;
    let encoreDesCartes = true;

    function charger(premiereFois) {
        if (enCours || !encoreDesCartes) return;
        enCours = true;

        if (loader) loader.classList.remove("d-none");

        const limite = premiereFois ? 6 : 3;
        let url = "/api/cartes?offset=" + offset + "&limit=" + limite;

        if (options.filtre) {
            url += "&filtre=" + options.filtre;
        }
        if (options.recherche) {
            url += "&recherche=" + encodeURIComponent(options.recherche);
        }

        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (premiereFois) {
                    conteneur.innerHTML = "";
                }

                data.cartes.forEach(function (carte) {
                    const photo = carte.photo
                        ? "/static/images/ajouts/" + carte.photo
                        : "/static/image/pikachu.jpg";

                    const html = `
                        <div class="col-12 col-md-6 col-lg-4">
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
                            </div>
                        </div>`;
                    conteneur.insertAdjacentHTML("beforeend", html);
                });

                offset += data.cartes.length;
                encoreDesCartes = data.has_more;
                enCours = false;
                if (loader) loader.classList.add("d-none");
            })
            .catch(function () {
                enCours = false;
                if (loader) loader.classList.add("d-none");
            });
    }

    // Première charge : 6 cartes
    charger(true);

    // Infinite scroll
    window.addEventListener("scroll", function () {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 400) {
            charger(false);   // +3 cartes
        }
    });

    // Polling toutes les 5 secondes
    setInterval(function () {
        // On ne recharge que si on est près du haut de la page
        if (window.scrollY < 200) {
            offset = 0;
            encoreDesCartes = true;
            charger(true);
        }
    }, 5000);
}