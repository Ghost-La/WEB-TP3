"use strict";

let offset = 6;
let chargement = false;

async function gererDefilement()
{
    if (chargement)
    {
        return;
    }

    if (
        window.innerHeight +
        window.scrollY >=
        document.body.offsetHeight - 100
    )
    {
        chargement = true;

        const reponse =
            await fetch(
                "/api/cartes?collection=1&offset="
                + offset
                + "&limit=3"
            );

        const donnees =
            await reponse.json();

        if (
            donnees.cartes.length === 0
        )
        {
            return;
        }

        offset +=
            donnees.cartes.length;

        // TEMPORAIRE POUR TEST

        console.log(
            donnees.cartes
        );

        chargement = false;
    }
}

window.addEventListener(
    "scroll",
    gererDefilement
);