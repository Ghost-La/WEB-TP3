"use strict";

/**
 * @param {string} url 
 * @param {string} methode
 * @param {object} parametres 
 * @param {AbortController}
 */
async function envoyerRequeteAjax(url, methode = "GET", parametres = null, controleur = null) {
    const options = {
        method: methode
    };

    if (controleur) {
        options.signal = controleur.signal;
    }

    if (parametres) {
        const query = new URLSearchParams(parametres).toString();
        url = url + "?" + query;
    }

    const reponse = await fetch(url, options);

    if (!reponse.ok) {
        throw new Error(`${reponse.status} ${reponse.statusText}`);
    }

    return await reponse.json();
}