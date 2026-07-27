CREATE TABLE `utilisateur` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `email` varchar(150) UNIQUE NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `role` enum(organisateur,agent,admin) NOT NULL,
  `statut` enum(actif,inactif) DEFAULT 'actif',
  `date_inscription` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE `organisateur` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `utilisateur_id` int UNIQUE NOT NULL,
  `qualite` varchar(100),
  `telephone` varchar(20) NOT NULL,
  `statut_compte` enum(actif,arriere,bloque,surveillance) DEFAULT 'actif'
);

CREATE TABLE `declaration` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `organisateur_id` int NOT NULL,
  `nom_demandeur` varchar(100),
  `prenom_demandeur` varchar(100),
  `qualite_demandeur` varchar(100),
  `telephone` varchar(20),
  `email` varchar(150),
  `nature_manifestation` varchar(100),
  `nom_artiste_evenement` varchar(200),
  `nom_salle` varchar(200),
  `adresse` varchar(200),
  `ville` varchar(100),
  `date_evenement` datetime,
  `duree_heures` float,
  `capacite_accueil` int,
  `entree_payante` boolean DEFAULT false,
  `nature_diffusion` varchar(200),
  `autres_details` text,
  `promouvoir` boolean DEFAULT false,
  `description_publique` text,
  `affiche_path` varchar(300),
  `contact_public` boolean DEFAULT false,
  `statut` enum(nouvelle,en_evaluation,montant_fixe,paiement_en_attente,payee,quittance_delivree,en_attente) DEFAULT 'nouvelle',
  `date_soumission` datetime DEFAULT (CURRENT_TIMESTAMP),
  `date_modification` datetime
);

CREATE TABLE `liste_artiste` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `declaration_id` int NOT NULL,
  `nom_artiste` varchar(200) NOT NULL,
  `discipline` varchar(100)
);

CREATE TABLE `evaluation_agent` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `declaration_id` int UNIQUE NOT NULL,
  `agent_id` int NOT NULL,
  `tarif` float,
  `redevance` float,
  `date_evaluation` datetime DEFAULT (CURRENT_TIMESTAMP),
  `commentaire` text
);

CREATE TABLE `paiement` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `declaration_id` int UNIQUE NOT NULL,
  `mode_paiement` enum(especes,cheque,orange_money) NOT NULL,
  `numero_cheque` varchar(50),
  `montant_chiffres` float,
  `montant_lettres` varchar(300),
  `type_paiement` enum(integral,partiel) DEFAULT 'integral',
  `reste_a_payer` float DEFAULT 0,
  `date_paiement` datetime DEFAULT (CURRENT_TIMESTAMP),
  `confirme_par` int NOT NULL
);

CREATE TABLE `quittance` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `declaration_id` int UNIQUE NOT NULL,
  `numero_quittance` varchar(20) UNIQUE NOT NULL,
  `droit_annuel` float DEFAULT 0,
  `droit_arriere` float DEFAULT 0,
  `droit_exigible` float DEFAULT 0,
  `droits_type` varchar(100),
  `droits_montant` float DEFAULT 0,
  `etiquettes_nombre` int DEFAULT 0,
  `etiquettes_montant` float DEFAULT 0,
  `penalites_type` varchar(100),
  `penalites_montant` float DEFAULT 0,
  `somme_totale_chiffres` float,
  `somme_totale_lettres` varchar(300),
  `date_delivrance` datetime DEFAULT (CURRENT_TIMESTAMP),
  `agent_id` int NOT NULL,
  `fichier_pdf_path` varchar(300)
);

CREATE TABLE `arriere` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `organisateur_id` int NOT NULL,
  `declaration_id` int,
  `montant_du` float NOT NULL,
  `date_echeance` datetime NOT NULL,
  `statut` enum(en_attente,regle) DEFAULT 'en_attente',
  `date_reglement` datetime,
  `derniere_notification` datetime
);

CREATE TABLE `notification` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `destinataire_id` int NOT NULL,
  `type_notification` varchar(50),
  `sujet` varchar(200),
  `message` text,
  `canal` varchar(20) DEFAULT 'email',
  `date_envoi` datetime DEFAULT (CURRENT_TIMESTAMP),
  `statut` enum(en_attente,envoyee,echouee) DEFAULT 'en_attente'
);

CREATE TABLE `alerte_surveillance` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `organisateur_id` int NOT NULL,
  `date_marquage` datetime DEFAULT (CURRENT_TIMESTAMP),
  `marque_par` int,
  `traitee` boolean DEFAULT false,
  `date_traitement` datetime,
  `traite_par` int,
  `commentaire` text
);

CREATE TABLE `message_contact` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `nom` varchar(100),
  `email` varchar(150),
  `sujet` varchar(200),
  `message` text,
  `date_envoi` datetime DEFAULT (CURRENT_TIMESTAMP),
  `traite` boolean DEFAULT false
);

CREATE INDEX `utilisateur_index_0` ON `utilisateur` (`email`);

CREATE INDEX `utilisateur_index_1` ON `utilisateur` (`statut`);

CREATE INDEX `organisateur_index_2` ON `organisateur` (`utilisateur_id`);

CREATE INDEX `organisateur_index_3` ON `organisateur` (`statut_compte`);

CREATE INDEX `declaration_index_4` ON `declaration` (`organisateur_id`);

CREATE INDEX `declaration_index_5` ON `declaration` (`statut`);

CREATE INDEX `declaration_index_6` ON `declaration` (`date_evenement`);

CREATE INDEX `declaration_index_7` ON `declaration` (`email`);

CREATE INDEX `liste_artiste_index_8` ON `liste_artiste` (`declaration_id`);

CREATE INDEX `evaluation_agent_index_9` ON `evaluation_agent` (`declaration_id`);

CREATE INDEX `evaluation_agent_index_10` ON `evaluation_agent` (`agent_id`);

CREATE INDEX `paiement_index_11` ON `paiement` (`declaration_id`);

CREATE INDEX `paiement_index_12` ON `paiement` (`confirme_par`);

CREATE INDEX `paiement_index_13` ON `paiement` (`date_paiement`);

CREATE INDEX `quittance_index_14` ON `quittance` (`declaration_id`);

CREATE INDEX `quittance_index_15` ON `quittance` (`numero_quittance`);

CREATE INDEX `quittance_index_16` ON `quittance` (`agent_id`);

CREATE INDEX `arriere_index_17` ON `arriere` (`organisateur_id`);

CREATE INDEX `arriere_index_18` ON `arriere` (`declaration_id`);

CREATE INDEX `arriere_index_19` ON `arriere` (`statut`);

CREATE INDEX `notification_index_20` ON `notification` (`destinataire_id`);

CREATE INDEX `notification_index_21` ON `notification` (`statut`);

CREATE INDEX `notification_index_22` ON `notification` (`date_envoi`);

CREATE INDEX `alerte_surveillance_index_23` ON `alerte_surveillance` (`organisateur_id`);

CREATE INDEX `alerte_surveillance_index_24` ON `alerte_surveillance` (`marque_par`);

CREATE INDEX `alerte_surveillance_index_25` ON `alerte_surveillance` (`traite_par`);

CREATE INDEX `alerte_surveillance_index_26` ON `alerte_surveillance` (`traitee`);

CREATE INDEX `message_contact_index_27` ON `message_contact` (`email`);

CREATE INDEX `message_contact_index_28` ON `message_contact` (`traite`);

CREATE INDEX `message_contact_index_29` ON `message_contact` (`date_envoi`);

ALTER TABLE `utilisateur` ADD FOREIGN KEY (`id`) REFERENCES `organisateur` (`utilisateur_id`);

ALTER TABLE `declaration` ADD FOREIGN KEY (`organisateur_id`) REFERENCES `organisateur` (`id`);

ALTER TABLE `liste_artiste` ADD FOREIGN KEY (`declaration_id`) REFERENCES `declaration` (`id`);

ALTER TABLE `declaration` ADD FOREIGN KEY (`id`) REFERENCES `evaluation_agent` (`declaration_id`);

ALTER TABLE `evaluation_agent` ADD FOREIGN KEY (`agent_id`) REFERENCES `utilisateur` (`id`);

ALTER TABLE `declaration` ADD FOREIGN KEY (`id`) REFERENCES `paiement` (`declaration_id`);

ALTER TABLE `paiement` ADD FOREIGN KEY (`confirme_par`) REFERENCES `utilisateur` (`id`);

ALTER TABLE `declaration` ADD FOREIGN KEY (`id`) REFERENCES `quittance` (`declaration_id`);

ALTER TABLE `quittance` ADD FOREIGN KEY (`agent_id`) REFERENCES `utilisateur` (`id`);

ALTER TABLE `arriere` ADD FOREIGN KEY (`organisateur_id`) REFERENCES `organisateur` (`id`);

ALTER TABLE `arriere` ADD FOREIGN KEY (`declaration_id`) REFERENCES `declaration` (`id`);

ALTER TABLE `notification` ADD FOREIGN KEY (`destinataire_id`) REFERENCES `utilisateur` (`id`);

ALTER TABLE `alerte_surveillance` ADD FOREIGN KEY (`organisateur_id`) REFERENCES `organisateur` (`id`);

ALTER TABLE `alerte_surveillance` ADD FOREIGN KEY (`marque_par`) REFERENCES `utilisateur` (`id`);

ALTER TABLE `alerte_surveillance` ADD FOREIGN KEY (`traite_par`) REFERENCES `utilisateur` (`id`);
