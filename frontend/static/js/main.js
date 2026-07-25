// JavaScript vanilla partage par toutes les pages (AI_RULES.md : pas de framework JS).

document.addEventListener("DOMContentLoaded", function () {
    initialiserFermetureMessagesFlash();
    initialiserFormulaireDeclaration();
    initialiserHorlogeAgent();
    initialiserTotalMontant();
    initialiserFormulairePaiement();
    initialiserOngletsUtilisateurs();
    initialiserFormulaireNouvelAgent();
    initialiserMenuLegalPublic();
});

function initialiserFermetureMessagesFlash() {
    var boutons = document.querySelectorAll(".message__fermer");
    boutons.forEach(function (bouton) {
        bouton.addEventListener("click", function () {
            var message = bouton.closest(".message");
            if (message) {
                message.remove();
            }
        });
    });
}

// Formulaire de nouvelle declaration (Prompt 7) : section artistes affichee
// uniquement pour une manifestation de type Festival, champs de precision
// (qualite "Autre", diffusion "Autres") et lignes d'artiste dynamiques.
function initialiserFormulaireDeclaration() {
    var selectNature = document.getElementById("nature_manifestation");
    var sectionArtistes = document.getElementById("section-artistes");
    if (selectNature && sectionArtistes) {
        var basculerSectionArtistes = function () {
            sectionArtistes.style.display = selectNature.value === "Festival" ? "" : "none";
        };
        selectNature.addEventListener("change", basculerSectionArtistes);
        basculerSectionArtistes();
    }

    basculerPrecision("qualite_autre_radio", "qualite_autre", 'input[name="qualite"]');
    basculerPrecision("diffusion_autres_case", "nature_diffusion_autre", null);

    var listeArtistes = document.getElementById("artistes-liste");
    var boutonAjouter = document.getElementById("bouton-ajouter-artiste");
    if (listeArtistes && boutonAjouter) {
        boutonAjouter.addEventListener("click", function () {
            listeArtistes.appendChild(creerLigneArtiste());
        });
        listeArtistes.addEventListener("click", function (evenement) {
            if (evenement.target.classList.contains("bouton-supprimer-artiste")) {
                evenement.target.closest(".artiste-ligne").remove();
            }
        });
    }

    // Section Promotion (Prompt 19) : champs affiches uniquement si la case
    // "promouvoir" est cochee.
    var casePromouvoir = document.getElementById("promouvoir_case");
    var sectionPromotion = document.getElementById("section-promotion");
    if (casePromouvoir && sectionPromotion) {
        var basculerPromotion = function () {
            sectionPromotion.style.display = casePromouvoir.checked ? "" : "none";
        };
        casePromouvoir.addEventListener("change", basculerPromotion);
        basculerPromotion();
    }

    // Controle de taille de l'affiche (RM-023 : 2 Mo) avant envoi.
    var champAffiche = document.getElementById("affiche");
    var formulaire = document.querySelector('form[action*="nouvelle"]') || document.querySelector("form[enctype='multipart/form-data']");
    var tailleMaxOctets = 2 * 1024 * 1024;
    if (champAffiche) {
        champAffiche.addEventListener("change", function () {
            if (champAffiche.files && champAffiche.files[0] && champAffiche.files[0].size > tailleMaxOctets) {
                alert("Cette image dépasse 2 Mo. Choisissez un fichier plus léger ou compressez-la.");
                champAffiche.value = "";
            }
        });
    }
    if (formulaire && champAffiche) {
        formulaire.addEventListener("submit", function (evenement) {
            if (champAffiche.files && champAffiche.files[0] && champAffiche.files[0].size > tailleMaxOctets) {
                evenement.preventDefault();
                alert("L'affiche dépasse 2 Mo. Compressez l'image puis réessayez.");
            }
        });
    }
}

function creerLigneArtiste() {
    var ligne = document.createElement("div");
    ligne.className = "artiste-ligne";
    ligne.innerHTML =
        '<input type="text" name="artiste_nom" placeholder="Nom de l\'artiste">' +
        '<input type="text" name="artiste_discipline" placeholder="Discipline">' +
        '<button type="button" class="bouton-supprimer-artiste" aria-label="Supprimer cette ligne">&times;</button>';
    return ligne;
}

// Horloge du tableau de bord agent (Prompt 9) : date et heure mises a jour
// chaque seconde, cote client uniquement (aucune donnee metier).
function initialiserHorlogeAgent() {
    var horloge = document.getElementById("horloge-agent");
    if (!horloge) {
        return;
    }
    var mettreAJour = function () {
        horloge.textContent = new Date().toLocaleString("fr-FR", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    };
    mettreAJour();
    setInterval(mettreAJour, 1000);
}

// Page de traitement agent (Prompt 10) : total tarif + redevance recalcule
// en temps reel, sans recharger la page.
function initialiserTotalMontant() {
    var champTarif = document.getElementById("tarif");
    var champRedevance = document.getElementById("redevance");
    var champTotal = document.getElementById("total-montant-calcule");
    if (!champTarif || !champRedevance || !champTotal) {
        return;
    }
    var recalculer = function () {
        var total = (parseFloat(champTarif.value) || 0) + (parseFloat(champRedevance.value) || 0);
        champTotal.textContent = total.toLocaleString("fr-FR");
    };
    champTarif.addEventListener("input", recalculer);
    champRedevance.addEventListener("input", recalculer);
    recalculer();
}

// Page de confirmation de paiement agent (Prompt 11) : le N de cheque et
// le reste a payer n'apparaissent que si pertinents.
function initialiserFormulairePaiement() {
    basculerPrecision("mode-cheque-radio", "champ-numero-cheque", 'input[name="mode_paiement"]');
    basculerPrecision("type-partiel-radio", "champ-reste-a-payer", 'input[name="type_paiement"]');

    var champMontant = document.getElementById("montant_chiffres");
    var champReste = document.getElementById("reste_a_payer");
    if (champMontant && champReste) {
        var maxDu = parseFloat(champMontant.getAttribute("max")) || 0;
        var recalculerReste = function () {
            var percu = parseFloat(champMontant.value) || 0;
            var reste = Math.max(0, maxDu - percu);
            if (!document.getElementById("type-partiel-radio") || !document.getElementById("type-partiel-radio").checked) {
                return;
            }
            champReste.value = String(Math.round(reste));
        };
        champMontant.addEventListener("input", recalculerReste);
        document.querySelectorAll('input[name="type_paiement"]').forEach(function (radio) {
            radio.addEventListener("change", recalculerReste);
        });
    }

    // Anti double-clic : desactive le bouton des la premiere soumission.
    var formulaire = document.getElementById("formulaire-confirmation-paiement");
    var bouton = document.getElementById("bouton-confirmer-paiement");
    if (formulaire && bouton) {
        formulaire.addEventListener("submit", function () {
            bouton.disabled = true;
            bouton.textContent = "Traitement en cours...";
        });
    }
}

// Page utilisateurs de l'espace admin (Prompt 16) : bascule entre les
// onglets "Organisateurs" et "Agents".
function initialiserOngletsUtilisateurs() {
    var boutons = document.querySelectorAll(".onglet-bouton");
    if (boutons.length === 0) {
        return;
    }
    boutons.forEach(function (bouton) {
        bouton.addEventListener("click", function () {
            boutons.forEach(function (b) {
                b.classList.remove("actif");
            });
            document.querySelectorAll(".onglet-contenu").forEach(function (contenu) {
                contenu.style.display = "none";
            });
            bouton.classList.add("actif");
            var cible = document.getElementById(bouton.dataset.cible);
            if (cible) {
                cible.style.display = "";
            }
        });
    });
}

// Page utilisateurs de l'espace admin (Prompt 16) : affiche/masque le
// formulaire de creation d'un compte agent.
function initialiserFormulaireNouvelAgent() {
    var boutonAfficher = document.getElementById("bouton-afficher-formulaire-agent");
    var formulaire = document.getElementById("formulaire-nouvel-agent");
    if (!boutonAfficher || !formulaire) {
        return;
    }
    boutonAfficher.addEventListener("click", function () {
        var visible = formulaire.style.display !== "none";
        formulaire.style.display = visible ? "none" : "";
    });
}

function initialiserMenuLegalPublic() {
    var deroulant = document.querySelector(".nav-deroulant");
    if (!deroulant) {
        return;
    }
    var bouton = deroulant.querySelector(".nav-deroulant__bouton");
    bouton.addEventListener("click", function () {
        var ouvert = deroulant.classList.toggle("ouvert");
        bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
    });
    document.addEventListener("click", function (evenement) {
        if (!deroulant.contains(evenement.target)) {
            deroulant.classList.remove("ouvert");
            bouton.setAttribute("aria-expanded", "false");
        }
    });
}

// Affiche/active un champ de precision (ex. "qualite_autre") uniquement
// quand l'option correspondante ("Autre", "Autres"...) est selectionnee.
function basculerPrecision(idDeclencheur, idChampPrecision, selecteurGroupe) {
    var champPrecision = document.getElementById(idChampPrecision);
    var declencheur = document.getElementById(idDeclencheur);
    if (!champPrecision || !declencheur) {
        return;
    }
    var mettreAJour = function () {
        champPrecision.style.display = declencheur.checked ? "" : "none";
    };
    declencheur.addEventListener("change", mettreAJour);
    if (selecteurGroupe) {
        document.querySelectorAll(selecteurGroupe).forEach(function (bouton) {
            bouton.addEventListener("change", mettreAJour);
        });
    }
    mettreAJour();
}
