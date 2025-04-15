import streamlit as st
import requests
from datetime import date
from fpdf import FPDF
import io

# CONFIGURATION - À personnaliser
AIRTABLE_TOKEN = "patoGCf4Aqgb9gCoY.97a5c6d48ac222c39ae4827bf4f879631ba2798931dd59dc7c54f5e19ca8c042"
BASE_ID = "apppx3bDNs72QXBEk/tblGGZwdi8mOOInIi/viwHnSkC9iCncTxpa?blocks=hide"
TABLE_NAME = "Backlog"

headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

# Fonctions API

def ajouter_tache(user_story, responsable, date_prevue, etat, projet, sprint, priorite):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    data = {
        "records": [
            {
                "fields": {
                    "User Story": user_story,
                    "Responsable": responsable,
                    "Date prévue": date_prevue,
                    "État": etat,
                    "Projet": projet,
                    "Sprint": sprint,
                    "Priorité": priorite
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200

def lister_taches():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("records", [])
    return []

def mettre_a_jour_etat(record_id, nouvel_etat):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    data = {
        "fields": {
            "État": nouvel_etat
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    return response.status_code == 200

# Génération de PDF

def generer_pdf(taches_filtrees):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Rapport des Tâches - MBA Capital", ln=True, align='C')
    pdf.ln(10)
    for t in taches_filtrees:
        f = t.get("fields", {})
        pdf.multi_cell(0, 10, txt=f"• {f.get('User Story', '')} | {f.get('Projet', '')} | {f.get('Sprint', '')} | {f.get('État', '')} | {f.get('Responsable', '')}")
    return pdf.output(dest='S').encode('latin1')

# Interface Streamlit
st.set_page_config(page_title="MBA Capital Pilotage", page_icon="📊", layout="wide")
st.title("📊 MBA Capital - Pilotage Airtable")
st.markdown("Ajoute, filtre, exporte tes tâches dans Airtable")

# Authentification légère
with st.sidebar:
    st.header("🔐 Accès")
    user = st.text_input("Nom d'utilisateur", value="Stéphane")
    show_completed = st.checkbox("Afficher les tâches terminées", value=True)
    st.markdown("---")
    filtre_projet = st.text_input("🔍 Filtrer par Projet")
    filtre_sprint = st.text_input("🗂️ Sprint")
    filtre_priorite = st.selectbox("⚡ Priorité", ["Toutes", "Haute", "Moyenne", "Basse"])
    search = st.text_input("🔎 Rechercher une tâche")

# Ajout d'une tâche
st.subheader("➕ Ajouter une tâche")
with st.form("form_tache"):
    user_story = st.text_input("User Story")
    responsable = st.text_input("Responsable", value=user)
    date_prevue = st.date_input("Date prévue", date.today())
    etat = st.selectbox("État", ["À faire", "En cours", "✅ Terminé"])
    projet = st.text_input("Projet")
    sprint = st.text_input("Sprint")
    priorite = st.selectbox("Priorité", ["Haute", "Moyenne", "Basse"])
    submitted = st.form_submit_button("Ajouter")
    if submitted:
        success = ajouter_tache(user_story, responsable, date_prevue.isoformat(), etat, projet, sprint, priorite)
        if success:
            st.success("Tâche ajoutée avec succès !")
        else:
            st.error("Erreur lors de l'ajout.")

# Liste filtrée
st.subheader("📋 Liste des tâches")
taches = lister_taches()
taches_filtrees = []

for t in taches:
    champs = t.get("fields", {})
    if not show_completed and champs.get("État") == "✅ Terminé":
        continue
    if filtre_projet and filtre_projet.lower() not in champs.get("Projet", "").lower():
        continue
    if filtre_sprint and filtre_sprint.lower() not in champs.get("Sprint", "").lower():
        continue
    if filtre_priorite != "Toutes" and filtre_priorite != champs.get("Priorité", ""):
        continue
    if search and search.lower() not in champs.get("User Story", "").lower():
        continue
    taches_filtrees.append(t)

if taches_filtrees:
    for t in taches_filtrees:
        record_id = t.get("id")
        champs = t.get("fields", {})
        with st.expander(f"🔹 {champs.get('User Story', 'Sans titre')} [{champs.get('Projet', '')}]", expanded=False):
            st.write(f"👤 Responsable : {champs.get('Responsable', '')}")
            st.write(f"📅 Date prévue : {champs.get('Date prévue', '')}")
            st.write(f"🚀 Sprint : {champs.get('Sprint', '')}")
            st.write(f"⚡ Priorité : {champs.get('Priorité', '')}")
            nouvel_etat = st.selectbox(
                "Modifier l'état",
                ["À faire", "En cours", "✅ Terminé"],
                index=["À faire", "En cours", "✅ Terminé"].index(champs.get("État", "À faire")),
                key=record_id
            )
            if st.button("💾 Enregistrer", key=f"save_{record_id}"):
                if mettre_a_jour_etat(record_id, nouvel_etat):
                    st.success("État mis à jour.")
                else:
                    st.error("Erreur de mise à jour.")

    # Génération du rapport
    if st.button("📄 Exporter en PDF"):
        pdf_bytes = generer_pdf(taches_filtrees)
        st.download_button("📥 Télécharger le PDF", data=pdf_bytes, file_name="rapport_mba_capital.pdf", mime="application/pdf")
else:
    st.info("Aucune tâche trouvée.")
