"use strict";

const cartes =
    document.querySelectorAll(
        ".carte-item"
    );

let visibles = 6;

function gererDefilement()
{
    if (
        (
            window.innerHeight +
            window.scrollY
        )
        >=
        (
            document.body.offsetHeight *
            0.95
        )
    )
    {
        for (
            let i = visibles;
            i < visibles + 3 &&
            i < cartes.length;
            i++
        )
        {
            cartes[i].style.display =
                "block";
        }

        visibles += 3;

        if (
            visibles >= cartes.length
        )
        {
            window.removeEventListener(
                "scroll",
                gererDefilement
            );
        }
    }
}

window.addEventListener(
    "scroll",
    gererDefilement
);