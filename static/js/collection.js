"use strict";

const txtRecherche =
    document.getElementById(
        "recherche"
    );

const divSuggestions =
    document.getElementById(
        "suggestions"
    );

let recherches =
    JSON.parse(
        localStorage.getItem(
            "recherches"
        )
    ) || [];

txtRecherche.addEventListener(
    "input",
    rechercher
);

async function rechercher()
{
   if(txtRecherche.value.length < 3)
{
    afficherDernieresRecherches();
    return;
}
   if (
       txtRecherche.value.trim() !== ""
       &&
       !recherches.includes(
           txtRecherche.value
       )
   )
   {
       recherches.push(
           txtRecherche.value
       );

       localStorage.setItem(
           "recherches",
           JSON.stringify(
               recherches
           )
       );
   }

   const reponse =
       await fetch(
           "/api/recherche-collection?mots-cles="
           + encodeURIComponent(
               txtRecherche.value
           )
       );

   const cartes =
       await reponse.json();

   if (cartes.length === 0)
   {
      divSuggestions.innerHTML =
         "<div class='list-group-item'>Aucun résultat</div>";

      return;
   }

   divSuggestions.innerHTML = "";

   for (const carte of cartes)
   {
      const lien =
          document.createElement(
              "a"
          );

      lien.href =
          "/collection/detail/"
          + carte.id_collection;

      lien.className =
          "list-group-item list-group-item-action";

      lien.textContent =
          carte.nom;

      divSuggestions.appendChild(
          lien
      );
   }
}
window.addEventListener(
    "load",
    initialiser
);

function initialiser()
{
    if (recherches.length > 0)
    {
        txtRecherche.value =
            recherches[
                recherches.length - 1
            ];
    }
}

window.addEventListener(
    "load",
    afficherDernieresRecherches
);

function afficherDernieresRecherches()
{
    divSuggestions.innerHTML = "";

    for (const recherche of recherches)
    {
        const lien =
            document.createElement(
                "a"
            );

        lien.href = "#";

        lien.className =
            "list-group-item list-group-item-action";

        lien.textContent =
            recherche;

        lien.addEventListener(
            "click",
            (e) =>
            {
                e.preventDefault();

                txtRecherche.value =
                    recherche;

                rechercher();
            }
        );

        divSuggestions.appendChild(
            lien
        );
    }
}
document.addEventListener(
    "click",
    fermerSuggestions
);

function fermerSuggestions(e)
{
    if (
        e.target !== txtRecherche &&
        !divSuggestions.contains(
            e.target
        )
    )
    {
        divSuggestions.innerHTML = "";
    }
}
txtRecherche.addEventListener(
    "focus",
    () =>
    {
        if (
            txtRecherche.value.length >= 3
        )
        {
            rechercher();
        }
    }
);

txtRecherche.addEventListener(
    "focus",
    afficherDernieresRecherches
);
