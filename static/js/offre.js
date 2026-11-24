const montant = document.getElementById("montant");

const bouton = document.getElementById("btn-offre");

const erreur = document.getElementById("erreur-offre");

montant.addEventListener("input",verifier);

async function verifier()
{
    const prix = parseFloat(montant.dataset.prix);

    const resultat =await fetch(
            "/api/valider-offre"
            + "?montant="
            + montant.value
            + "&prix="
            + prix
        );

    const json =
        await resultat.json();

    bouton.disabled = !json.valide;

    erreur.textContent = json.valide? "": "Le montant est trop faible.";
}