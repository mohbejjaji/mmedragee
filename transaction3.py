import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from supabase_adapter import SupabaseAdapter

# -------- CONFIG --------
DB_PATH = "gestion4.db"
SUPPORTED_DEVISES = ["MAD", "USD", "TRY"]

def parse_date_safe(date_val):
    """
    Convertit une date (string ou date object) en string formatée dd/mm/yyyy
    """
    if not date_val:
        return ""
    if isinstance(date_val, (date, datetime)):
        return date_val.strftime('%d/%m/%Y')
    try:
        # Tenter le format standard ISO
        return datetime.strptime(str(date_val), '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return str(date_val)
TYPES_PRESTATION = ["Location de matériel", "Décoration", "Autre"]
STATUTS_PRESTATION = ["Devis", "Confirmé", "En cours", "Terminé", "Facturé", "Payé", "Annulé"]

# -------- STYLE CSS PROFESSIONNEL PREMIUM --------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 1. GLOBAL RESET & TYPOGRAPHY */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .view-header h1 {
        font-family: 'Outfit', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        background-attachment: fixed;
    }

    /* 2. SIDEBAR PREMIUM (GLASSMORPHISM EFFECT) */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        background-image: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stImage"] {
        padding: 1rem;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
    }

    /* Active Menu Item Highlight */
    [data-testid="stSidebar"] .st-emotion-cache-1pxm631 {
        background-color: rgba(99, 102, 241, 0.1) !important;
        border-radius: 8px;
    }

    /* 3. EN-TÊTE DE VUE (PREMIUM GRADIENT) */
    .view-header {
        background: white;
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.05);
        border: 1px solid rgba(226, 232, 240, 0.6);
        position: relative;
        overflow: hidden;
    }
    
    .view-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        background: linear-gradient(to bottom, #6366f1, #10b981);
    }

    .view-header h1 {
        color: #0f172a !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    
    .view-header .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* 4. CARTES ET MÉTRIQUES (FINANCIAL DASHBOARD STYLE) */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
        min-height: 120px;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -5px rgba(0,0,0,0.1) !important;
        border-color: #6366f1 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        font-family: 'Outfit', sans-serif !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
        margin-bottom: 0.25rem !important;
    }

    /* 5. BOUTONS (INTERACTIFS) */
    .stButton button {
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2) !important;
    }

    .stButton button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3) !important;
        background: linear-gradient(90deg, #4f46e5 0%, #4338ca 100%) !important;
        border: none !important;
        color: white !important;
    }
    
    /* Secondary Button Style */
    .stButton button[kind="secondary"] {
        background: white !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: none !important;
    }

    /* 6. CONTAINERS ET CARTES CUSTOM */
    .custom-card {
        background: white;
        padding: 1.25rem;
        border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.6);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        margin-bottom: 1.25rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        box-shadow: 0 8px 12px -3px rgba(0,0,0,0.06);
        border-color: rgba(99, 102, 241, 0.3);
    }

    .section-header {
        font-family: 'Outfit', sans-serif;
        color: #0f172a;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 1.25rem;
        margin-top: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f1f5f9;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .subsection-header {
        color: #334155;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 7. NOTIFICATIONS / ALERTS (LOOK NOTION) */
    .success-card, .warning-card, .info-card {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        border: 1px solid transparent;
        font-weight: 500;
    }

    .success-card {
        background-color: #ecfdf5;
        color: #065f46;
        border-color: #a7f3d0;
    }

    .warning-card {
        background-color: #fffbeb;
        color: #92400e;
        border-color: #fde68a;
    }

    .info-card {
        background-color: #eff6ff;
        color: #1e40af;
        border-color: #bfdbfe;
    }

    /* 8. TABLEAUX ET DATAFRAME */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border-radius: 10px 10px 0 0;
        font-weight: 600 !important;
        color: #64748b !important;
    }

    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom: 3px solid #6366f1 !important;
    }

    /* 9. FORM INPUTS */
    .stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    </style>
    """, unsafe_allow_html=True)

# -------- FONCTIONS UTILITAIRES D'AFFICHAGE --------
def afficher_details_achat(achat_data):
    """Affiche les détails d'un achat de manière formatée premium"""
    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;'>
            <div>
                <div style='color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; margin-bottom: 0.25rem;'>📦 Produit / Source</div>
                <div style='color: #0f172a; font-weight: 600;'>{achat_data['produit']} (ID #{achat_data['achat_item_id']})</div>
            </div>
            <div>
                <div style='color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; margin-bottom: 0.25rem;'>👤 Fournisseur</div>
                <div style='color: #0f172a; font-weight: 600;'>{achat_data['fournisseur']}</div>
            </div>
            <div>
                <div style='color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; margin-bottom: 0.25rem;'>📅 Date Achat</div>
                <div style='color: #0f172a; font-weight: 600;'>{achat_data['date_achat']}</div>
            </div>
            <div>
                <div style='color: #64748b; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; margin-bottom: 0.25rem;'>📉 Stock Restant</div>
                <div style='color: #10b981; font-weight: 700; font-size: 1.1rem;'>{achat_data['quantite_restante']} unités</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_metric_with_icon(icon, label, value, delta=None, delta_color="normal"):
    """Affiche une métrique avec une icône stylisée"""
    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);'>
        <div style='display: flex; align-items: center; gap: 15px;'>
            <div style='background: #f1f5f9; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;'>
                {icon}
            </div>
            <div>
                <div style='color: #64748b; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;'>{label}</div>
                <div style='color: #0f172a; font-size: 1.6rem; font-weight: 700; font-family: Outfit, sans-serif;'>{value}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_status_badge(status):
    """Affiche un badge de statut coloré premium"""
    # Map status to colors
    colors = {
        "paye": ("#ecfdf5", "#065f46", "#a7f3d0"),
        "termine": ("#ecfdf5", "#065f46", "#a7f3d0"),
        "encours": ("#eff6ff", "#1e40af", "#bfdbfe"),
        "confirme": ("#f5f3ff", "#5b21b6", "#ddd6fe"),
        "devis": ("#f1f5f9", "#334155", "#e2e8f0"),
        "annule": ("#fef2f2", "#991b1b", "#fecaca"),
        "facture": ("#fffbeb", "#92400e", "#fde68a"),
    }
    
    key = status.lower().replace(' ', '').replace('é', 'e')
    bg, fg, border = colors.get(key, ("#f1f5f9", "#334155", "#e2e8f0"))
    
    st.markdown(f"""
    <span style='background-color: {bg}; color: {fg}; border: 1px solid {border}; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;'>
        {status}
    </span>
    """, unsafe_allow_html=True)

def display_success_message(message):
    """Affiche un message de succès stylisé premium"""
    st.markdown(f"<div class='success-card'><span style='margin-right: 12px; font-size: 1.2rem;'>✅</span> {message}</div>", unsafe_allow_html=True)

def display_warning_message(message):
    """Affiche un message d'avertissement stylisé premium"""
    st.markdown(f"<div class='warning-card'><span style='margin-right: 12px; font-size: 1.2rem;'>⚠️</span> {message}</div>", unsafe_allow_html=True)

def display_info_message(message):
    """Affiche un message d'information stylisé premium"""
    st.markdown(f"<div class='info-card'><span style='margin-right: 12px; font-size: 1.2rem;'>ℹ️</span> {message}</div>", unsafe_allow_html=True)

def display_view_header(title, subtitle=None, icon="🏢"):
    """Affiche un en-tête de vue stylisé premium"""
    st.markdown(f"""
    <div class='view-header'>
        <div style='display: flex; align-items: center; gap: 25px;'>
            <div style='background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); width: 70px; height: 70px; border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4);'>
                {icon}
            </div>
            <div>
                <h1>{title}</h1>
                {f"<div class='subtitle'>{subtitle}</div>" if subtitle else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Ajoutez cette fonction avant la fonction generer_apercu_ticket_avance
def generer_ticket_pdf(conn, vente_header_id):
    """
    Génère un ticket au format HTML téléchargeable
    """
    # Récupérer les informations
    vente_info = pd.read_sql("""
        SELECT 
            vh.*,
            COUNT(v.id) as nb_articles,
            SUM(v.quantite) as total_quantite
        FROM ventes_headers vh
        LEFT JOIN ventes v ON vh.id = v.vente_header_id
        WHERE vh.id = ?
        GROUP BY vh.id
    """, conn, params=(vente_header_id,)).iloc[0]
    
    articles = pd.read_sql("""
        SELECT 
            v.produit,
            v.quantite,
            v.prix_origine,
            v.devise_origine,
            v.prix_mad,
            (v.quantite * v.prix_mad) as total_mad
        FROM ventes v
        WHERE v.vente_header_id = ?
        ORDER BY v.produit
    """, conn, params=(vente_header_id,))
    
    date_vente = parse_date_safe(vente_info['date'])
    
    # Générer le HTML du ticket
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Ticket #{vente_info['id']}</title>
        <style>
            body {{
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 20px;
                background: white;
                display: flex;
                justify-content: center;
            }}
            .ticket {{
                max-width: 350px;
                width: 100%;
                background: white;
                border: 1px solid #e0e0e0;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 2px dashed #333;
                padding-bottom: 15px;
                margin-bottom: 15px;
            }}
            .header h2 {{
                margin: 0 0 10px 0;
                color: #333;
                font-size: 20px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .header p {{
                margin: 5px 0;
                color: #666;
                font-size: 14px;
            }}
            .items {{
                margin: 20px 0;
            }}
            .item-header {{
                display: grid;
                grid-template-columns: 2fr 0.8fr 1.2fr;
                font-weight: bold;
                border-bottom: 2px solid #333;
                padding-bottom: 8px;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            .item-header span:first-child {{ text-align: left; }}
            .item-header span:nth-child(2) {{ text-align: center; }}
            .item-header span:last-child {{ text-align: right; }}
            
            .item {{
                display: grid;
                grid-template-columns: 2fr 0.8fr 1.2fr;
                font-size: 13px;
                padding: 6px 0;
                border-bottom: 1px dotted #ccc;
            }}
            .item span:first-child {{ text-align: left; }}
            .item span:nth-child(2) {{ text-align: center; }}
            .item span:last-child {{ 
                text-align: right; 
                font-weight: 600;
                color: #27ae60;
            }}
            .total {{
                border-top: 3px double #333;
                margin-top: 15px;
                padding-top: 15px;
                display: flex;
                justify-content: space-between;
                font-weight: bold;
                font-size: 18px;
            }}
            .total span:last-child {{
                color: #27ae60;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 2px dashed #95a5a6;
                color: #7f8c8d;
                font-size: 12px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            .footer p:first-child {{
                font-weight: 600;
                color: #34495e;
            }}
        </style>
    </head>
    <body>
        <div class="ticket">
            <div class="header">
                <h2>🧾 TICKET DE CAISSE</h2>
                <p>N° {vente_info['id']:06d} | {date_vente}</p>
                <p><strong>{vente_info['client']}</strong> | {vente_info.get('ville') or ''}</p>
                <p>{vente_info['telephone_client'] or ''}</p>
            </div>
            
            <div class="items">
                <div class="item-header">
                    <span>Article</span>
                    <span>Qté</span>
                    <span>Prix</span>
                </div>
    """
    
    # Ajouter les articles
    total_general = 0
    for _, article in articles.iterrows():
        html_content += f"""
                <div class="item">
                    <span>{article['produit'][:30]}</span>
                    <span>{int(article['quantite'])}</span>
                    <span>{article['prix_origine']:.2f} {article['devise_origine']}</span>
                </div>
        """
        total_general += article['total_mad']
    
    # Ajouter le total
    html_content += f"""
            </div>
            
            <div class="total">
                <span>TOTAL:</span>
                <span>{total_general:.2f} MAD</span>
            </div>
            
            <div class="footer">
                <p>Articles: {int(vente_info['nb_articles'])} | Unités: {int(vente_info['total_quantite'])}</p>
                <p>Merci de votre visite !</p>
                <p>{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generer_ticket_pdf_weasy(conn, vente_header_id):
    """
    Génère un vrai PDF en utilisant xhtml2pdf (alternative Windows-friendly)
    """
    try:
        from xhtml2pdf import pisa
        import io
        
        # Générer le HTML du ticket
        html_content = generer_ticket_pdf(conn, vente_header_id)  # Utilise la fonction HTML existante
        
        # Convertir en PDF
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        
        if pisa_status.err:
            st.error(f"❌ Erreur xhtml2pdf : {pisa_status.err}")
            return None
            
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
        
    except ImportError:
        st.error("❌ Module xhtml2pdf non installé. Installation : pip install xhtml2pdf")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du PDF : {e}")
        return None

# Version améliorée de l'aperçu avec plus d'options
# Remplacer la fonction generer_apercu_ticket_avance par cette version

# Version ultra-simplifiée qui fonctionne à coup sûr

def generer_apercu_ticket_avance(conn, vente_header_id):
    """
    Génère un aperçu avancé du ticket avec options d'export
    """
    # Clé unique pour cette instance
    instance_key = f"ticket_{vente_header_id}"
    
    # Initialiser l'état dans session_state
    if instance_key not in st.session_state:
        st.session_state[instance_key] = {
            "show_preview": True,
            "format_export": "HTML",
            "generated_html": None,
            "show_download": False
        }
    
    # Récupérer les informations UNE SEULE FOIS et les stocker dans session_state
    if f"vente_info_{vente_header_id}" not in st.session_state:
        vente_info = pd.read_sql("""
            SELECT 
                vh.*,
                COUNT(v.id) as nb_articles,
                SUM(v.quantite) as total_quantite
            FROM ventes_headers vh
            LEFT JOIN ventes v ON vh.id = v.vente_header_id
            WHERE vh.id = ?
            GROUP BY vh.id
        """, conn, params=(vente_header_id,)).iloc[0]
        
        articles = pd.read_sql("""
            SELECT 
                v.produit,
                v.quantite,
                v.prix_origine,
                v.devise_origine,
                v.prix_mad,
                (v.quantite * v.prix_mad) as total_mad
            FROM ventes v
            WHERE v.vente_header_id = ?
            ORDER BY v.produit
        """, conn, params=(vente_header_id,))
        
        st.session_state[f"vente_info_{vente_header_id}"] = vente_info.to_dict()
        st.session_state[f"articles_{vente_header_id}"] = articles.to_dict('records')
    
    # Récupérer les données depuis session_state
    vente_info = st.session_state[f"vente_info_{vente_header_id}"]
    articles = st.session_state[f"articles_{vente_header_id}"]
    
    # Convertir en DataFrame pour faciliter l'utilisation
    articles_df = pd.DataFrame(articles)
    
    # Interface utilisateur
    st.markdown("### 🧾 Ticket de caisse")
    
    # Options en haut
    col1, col2 = st.columns(2)
    with col1:
        st.session_state[instance_key]["format_export"] = st.radio(
            "Format d'affichage",
            ["Standard", "Compact", "Détaillé"],
            horizontal=True,
            key=f"format_{vente_header_id}"
        )
    with col2:
        inclure_tva = st.checkbox("Inclure TVA", key=f"tva_{vente_header_id}")
    
    # Afficher le ticket
    date_vente = parse_date_safe(vente_info['date'])
    afficher_ticket(vente_info, articles_df, date_vente)
    
    # Boutons d'action
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🖨️ Imprimer", use_container_width=True, key=f"print_{vente_header_id}"):
            html_content = generer_html_complet(vente_info, articles_df, date_vente)
            st.components.v1.html(html_content, height=700)
    
    with col2:
        # Générer le HTML pour le téléchargement
        html_content = generer_html_export(vente_info, articles_df, date_vente)
        
        st.download_button(
            label="💾 Télécharger HTML",
            data=html_content,
            file_name=f"ticket_{vente_info['id']}_{date_vente}.html",
            mime="text/html",
            use_container_width=True,
            key=f"download_{vente_header_id}"
        )
    
    with col3:
        if st.button("📧 Email", use_container_width=True, key=f"email_btn_{vente_header_id}"):
            st.session_state[f"show_email_{vente_header_id}"] = True
        
        if st.session_state.get(f"show_email_{vente_header_id}", False):
            email = st.text_input("Adresse email", key=f"email_input_{vente_header_id}")
            if st.button("Envoyer", key=f"send_{vente_header_id}"):
                st.success(f"✅ Ticket envoyé à {email}")
                st.session_state[f"show_email_{vente_header_id}"] = False
                st.rerun()
    
    with col4:
        if st.button("📱 WhatsApp", use_container_width=True, key=f"whatsapp_btn_{vente_header_id}"):
            telephone = vente_info.get('telephone_client', '')
            if telephone:
                telephone = str(telephone).replace(' ', '').replace('+', '').replace('-', '')
                message = f"Ticket%20de%20vente%20%23{vente_info['id']}%20-%20{date_vente}%20-%20Total%3A%20{vente_info['total_mad']:.2f}%20MAD"
                url = f"https://wa.me/{telephone}?text={message}"
                st.markdown(f"[📱 Ouvrir WhatsApp]({url})")
            else:
                st.warning("⚠️ Numéro non disponible")

def afficher_ticket(vente_info, articles, date_vente):
    """Affiche un ticket de caisse au design moderne et épuré"""
    items_html = ""
    for _, article in articles.iterrows():
        items_html += f"""
        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
            <div style="flex: 2;">
                <div style="font-weight: 600; color: #334155;">{article['produit']}</div>
                <div style="font-size: 0.8rem; color: #64748b;">Qté: {int(article['quantite'])}</div>
            </div>
            <div style="flex: 1; text-align: right; font-weight: 600; color: #0f172a;">
                {article['prix_origine']:.2f} {article['devise_origine']}
            </div>
        </div>
        """

    ticket_modern = f"""
    <div style="background: white; padding: 30px; border-radius: 20px; border: 1px solid #e2e8f0; max-width: 450px; margin: auto; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 25px;">
            <h2 style="margin: 0; color: #0f172a; font-size: 1.5rem;">Mme Dragée</h2>
            <p style="color: #64748b; font-size: 0.9rem;">Reçu de vente #{int(vente_info['id']):06d}</p>
        </div>
        
        <div style="background: #f8fafc; border-radius: 12px; padding: 15px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #475569;">
                <span>Client: <strong>{vente_info['client']}</strong></span>
                <span>Ville: <strong>{vente_info.get('ville') or '—'}</strong></span>
                <span>Date: {date_vente}</span>
            </div>
        </div>

        <div style="margin-bottom: 25px;">
            {items_html}
        </div>

        <div style="border-top: 2px solid #0f172a; padding-top: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.1rem; font-weight: 700; color: #0f172a;">Total payé</span>
                <span style="font-size: 1.5rem; font-weight: 800; color: #10b981;">{vente_info['total_mad']:.2f} MAD</span>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #94a3b8; font-size: 0.8rem;">
            <p>Merci de votre confiance !<br>Suivez-nous sur les réseaux sociaux.</p>
        </div>
    </div>
    """
    st.markdown(ticket_modern, unsafe_allow_html=True)

def generer_html_export(vente_info, articles, date_vente):
    """Génère le HTML pour l'export avec le logo Mme Dragée"""
    import base64
    
    try:
        with open("logo.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        logo_html = f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='data:image/png;base64,{encoded_string}' 
                 style='max-width: 150px; max-height: 80px; object-fit: contain; margin-bottom: 5px;'>
            <div style='font-weight: bold; font-size: 1.2em; color: #2c3e50;'>Mme Dragée</div>
        </div>
        """
    except FileNotFoundError:
        # Fallback si l'image n'est pas trouvée
        logo_html = """
        <div style='text-align: center; margin-bottom: 20px;'>
            <div style='font-size: 2em; margin-bottom: 5px;'>🍽️</div>
            <strong style='font-size: 1.2em; color: #2c3e50;'>Mme Dragée</strong>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ticket Mme Dragée #{vente_info['id']}</title>
    <style>
        body {{ 
            font-family: 'Courier New', monospace; 
            margin: 20px; 
            background: #f5f5f5;
        }}
        .ticket {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            margin: 0 auto;
            border: 1px solid #ddd;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        th {{ 
            text-align: left; 
            border-bottom: 2px solid #2c3e50;
            background-color: #f8f9fa;
            padding: 10px 0;
        }}
        td {{ 
            padding: 8px 0;
            border-bottom: 1px dotted #ccc;
        }}
        .total {{ 
            border-top: 3px double #2c3e50; 
            margin-top: 20px; 
            padding-top: 15px;
            font-size: 1.2em;
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 25px; 
            padding-top: 15px;
            border-top: 2px dashed #95a5a6;
            color: #7f8c8d;
        }}
        .price {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="ticket">
        {logo_html}
        
        <div style="text-align: center; border-bottom: 2px dashed #2c3e50; padding-bottom: 15px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">TICKET DE CAISSE</h3>
            <p style="margin: 5px 0;"><strong>N° {int(vente_info['id']):06d}</strong> | {date_vente}</p>
            <p style="margin: 5px 0;"><strong>{vente_info['client']}</strong> | {vente_info.get('ville') or ''}</p>
            <p style="margin: 5px 0; color: #7f8c8d;">{vente_info.get('telephone_client', '') or ''}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Article</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, article in articles.iterrows():
        produit = article['produit'][:25] + "..." if len(article['produit']) > 25 else article['produit']
        html += f"""
                <tr>
                    <td>{produit}</td>
                    <td style="text-align: center;">{int(article['quantite'])}</td>
                    <td style="text-align: right;" class="price">{article['prix_origine']:.2f} {article['devise_origine']}</td>
                </tr>
        """
    
    html += f"""
            </tbody>
        </table>
        
        <div class="total">
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>TOTAL:</span>
                <span class="price">{vente_info['total_mad']:.2f} MAD</span>
            </div>
        </div>
        
        <div class="footer">
            <p style="margin: 5px 0;"><strong>Articles: {int(vente_info['nb_articles'])} | Unités: {int(vente_info['total_quantite'])}</strong></p>
            <p style="margin: 5px 0;">Merci de votre visite !</p>
            <p style="margin: 5px 0;">À très bientôt chez Mme Dragée</p>
            <p style="margin: 5px 0;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
    """
    return html

def generer_html_complet(vente_info, articles, date_vente):
    """Génère le HTML complet pour l'impression"""
    ticket_html = generer_html_export(vente_info, articles, date_vente)
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Ticket Mme Dragée #{vente_info['id']}</title>
    <style>
        body {{ font-family: 'Courier New', monospace; margin: 0; padding: 20px; background: white; }}
        .no-print {{ text-align: center; margin-top: 20px; }}
        @media print {{ 
            .no-print {{ display: none; }}
            body {{ padding: 0; }}
        }}
        button {{
            padding: 12px 24px;
            margin: 5px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}
        button:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    {ticket_html}
    <div class="no-print">
        <button onclick="window.print()">🖨️ Imprimer</button>
        <button onclick="window.close()" style="background: #e74c3c;">❌ Fermer</button>
    </div>
</body>
</html>
    """

def afficher_panier_vente_avec_sources_multiples(conn, vente_header_id):
    """Affiche le panier d'une vente avec les différentes sources d'achat"""
    try:
        items_vente = pd.read_sql("""
            SELECT 
                v.*,
                a.id as achat_id,
                a.prix_mad as prix_achat_mad,
                ah.fournisseur as fournisseur_source,
                ah.date as date_achat_source,
                (v.prix_mad - a.prix_mad) as marge_unitaire,
                ((v.prix_mad - a.prix_mad) / a.prix_mad * 100) as marge_pourcentage
            FROM ventes v
            JOIN achats a ON v.achat_source_id = a.id
            JOIN achats_headers ah ON a.achat_header_id = ah.id
            WHERE v.vente_header_id = ?
            ORDER BY v.id
        """, conn, params=(vente_header_id,))
        
        if not items_vente.empty:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='subsection-header'>📋 Panier en Cours - Sources Multiples</div>", unsafe_allow_html=True)
                
                # Préparer l'affichage
                items_display = items_vente.copy()
                items_display['Total Vente MAD'] = items_display['quantite'] * items_display['prix_mad']
                items_display['Total Achat MAD'] = items_display['quantite'] * items_display['prix_achat_mad']
                items_display['Marge Totale MAD'] = items_display['Total Vente MAD'] - items_display['Total Achat MAD']
                
                display_cols = [
                    'produit', 'quantite', 'prix_mad', 'Total Vente MAD',
                    'prix_achat_mad', 'Total Achat MAD', 'Marge Totale MAD', 'marge_pourcentage',
                    'fournisseur_source', 'date_achat_source'
                ]
                
                items_display = items_display[display_cols]
                items_display.columns = [
                    'Produit', 'Quantité', 'Prix Vente MAD', 'Total Vente MAD',
                    'Prix Achat MAD', 'Total Achat MAD', 'Marge Totale MAD', 'Marge %',
                    'Fournisseur Source', 'Date Achat Source'
                ]
                
                st.dataframe(
                    items_display,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Résumé financier par source
                st.markdown("**📊 Analyse par Source d'Achat**")
                
                analyse_sources = items_vente.groupby('fournisseur_source').agg({
                    'quantite': 'sum',
                    'prix_mad': 'sum',
                    'prix_achat_mad': 'sum',
                    'marge_unitaire': 'sum'
                }).reset_index()
                
                analyse_sources['marge_pourcentage'] = (analyse_sources['marge_unitaire'] / analyse_sources['prix_achat_mad'] * 100)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📦 Quantités par fournisseur**")
                    for _, source in analyse_sources.iterrows():
                        st.write(f"• **{source['fournisseur_source']}**: {source['quantite']} unités")
                
                with col2:
                    st.markdown("**💰 Marges par fournisseur**")
                    for _, source in analyse_sources.iterrows():
                        st.write(f"• **{source['fournisseur_source']}**: {source['marge_unitaire']:.2f} MAD ({source['marge_pourcentage']:.1f}%)")
                
                # Totaux généraux
                total_vente = items_display['Total Vente MAD'].sum()
                total_achat = items_display['Total Achat MAD'].sum()
                total_marge = items_display['Marge Totale MAD'].sum()
                marge_moyenne = items_display['Marge %'].mean()
                
                # --- Interface de suppression d'article ---
                st.markdown("---")
                st.markdown("### 🗑️ Gérer les articles")
                col_del1, col_del2 = st.columns([3, 1])
                with col_del1:
                    options_suppr = {row['id']: f"{row['produit']} ({row['quantite']} unités) - {float(row['prix_mad']):.2f} MAD" for _, row in items_vente.iterrows()}
                    item_to_delete = st.selectbox("Sélectionner un article à supprimer", options=list(options_suppr.keys()), format_func=lambda x: options_suppr.get(x, ""), key=f"sel_del_multi_{vente_header_id}")
                with col_del2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌ Supprimer l'article", key=f"btn_del_multi_{vente_header_id}", use_container_width=True):
                        if item_to_delete:
                            try:
                                supprimer_vente_item(conn, item_to_delete)
                                display_success_message("Article supprimé avec succès!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la suppression: {e}")

                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💰 Total Vente", f"{total_vente:.2f} MAD")
                with col2:
                    st.metric("📦 Coût Total Achats", f"{total_achat:.2f} MAD")
                with col3:
                    st.metric("✅ Marge Totale", f"{total_marge:.2f} MAD")
                with col4:
                    st.metric("📊 Marge Moyenne", f"{marge_moyenne:.1f}%")
                
                # Bouton de finalisation
                if st.button("✅ Finaliser la vente", type="primary", use_container_width=True):
                    del st.session_state.current_vente_id
                    display_success_message("Vente finalisée avec succès!")
                    st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("🛒 Aucun article ajouté à cette vente")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du panier: {e}")

# -------- FONCTIONS POUR LE STOCK --------
def get_stock_actuel(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calcule le stock actuel pour tous les produits avec prix de vente calculé"""
    try:
        achats_items = pd.read_sql("SELECT * FROM achats", conn)
        ventes_items = pd.read_sql("SELECT * FROM ventes", conn)
        
        if achats_items.empty and ventes_items.empty:
            return pd.DataFrame()
        
        if not achats_items.empty:
            achats_par_produit = achats_items.groupby("produit")["quantite"].sum()
        else:
            achats_par_produit = pd.Series(dtype=int)
        
        if not ventes_items.empty:
            ventes_par_produit = ventes_items.groupby("produit")["quantite"].sum()
        else:
            ventes_par_produit = pd.Series(dtype=int)
        
        stock = achats_par_produit.sub(ventes_par_produit, fill_value=0).reset_index()
        stock.columns = ["Produit", "Quantité en stock"]
        stock = stock[stock["Quantité en stock"] > 0]
        
        if not stock.empty and not achats_items.empty:
            # Prix moyen d'achat
            prix_moyen = achats_items.groupby("produit")["prix_mad"].mean()
            stock = stock.merge(prix_moyen, left_on="Produit", right_index=True, how="left")
            
            # Récupérer les frais de transport totaux
            try:
                depenses_transport = pd.read_sql(
                    "SELECT SUM(montant_mad) as total_transport FROM depenses WHERE categorie LIKE '%transport%' OR description LIKE '%transport%'", 
                    conn
                )
                if not depenses_transport.empty and depenses_transport.iloc[0]['total_transport'] is not None:
                    total_transport = float(depenses_transport.iloc[0]['total_transport'])
                else:
                    total_transport = 0
            except Exception:
                total_transport = 0
            
            # Calcul du coût total des marchandises
            cout_total_marchandises = achats_items['quantite'].dot(achats_items['prix_mad'])
            
            # Coefficient de répartition des frais de transport
            if cout_total_marchandises > 0:
                coefficient_transport = total_transport / cout_total_marchandises
            else:
                coefficient_transport = 0
            
            # Calcul du coût de revient unitaire avec transport
            stock['Coût Revient MAD'] = stock['prix_mad'] * (1 + coefficient_transport)
            
            # Calcul du prix de vente avec marge de 50% sur le coût de revient
            stock['Prix Vente MAD'] = stock['Coût Revient MAD'] / 0.5  # PV = CU / (1 - 0.50)
            
            # Arrondir les prix
            stock['Prix Vente MAD'] = stock['Prix Vente MAD'].round(2)
            stock['Coût Revient MAD'] = stock['Coût Revient MAD'].round(2)
            
            # Valeur du stock au prix d'achat
            stock["Valeur MAD"] = stock["Quantité en stock"] * stock["prix_mad"]
            stock["Valeur MAD"] = stock["Valeur MAD"].round(2)
            
            # Valeur du stock au prix de vente
            stock["Valeur Vente MAD"] = stock["Quantité en stock"] * stock["Prix Vente MAD"]
            stock["Valeur Vente MAD"] = stock["Valeur Vente MAD"].round(2)
            
            # Renommer la colonne prix_mad
            stock = stock.rename(columns={"prix_mad": "Prix Achat MAD"})
            
            # Sélection et ordre des colonnes
            stock = stock[["Produit", "Quantité en stock", "Prix Achat MAD", "Coût Revient MAD", "Prix Vente MAD", "Valeur MAD", "Valeur Vente MAD"]]
            
        else:
            # Retourner un DataFrame avec les colonnes attendues même si vide
            stock = pd.DataFrame(columns=["Produit", "Quantité en stock", "Prix Achat MAD", "Coût Revient MAD", "Prix Vente MAD", "Valeur MAD", "Valeur Vente MAD"])
        
        return stock.sort_values("Quantité en stock", ascending=False)
        
    except Exception as e:
        st.error(f"Erreur lors du calcul du stock: {e}")
        return pd.DataFrame(columns=["Produit", "Quantité en stock", "Prix Achat MAD", "Coût Revient MAD", "Prix Vente MAD", "Valeur MAD", "Valeur Vente MAD"])

def get_ventes_par_produit(conn: sqlite3.Connection, produit: str = None, 
                          date_debut: str = None, date_fin: str = None) -> pd.DataFrame:
    """
    Récupère toutes les ventes détaillées pour un produit spécifique ou tous les produits
    """
    query = """
    SELECT 
        v.id as vente_item_id,
        vh.id as vente_header_id,
        vh.date as date_vente,
        vh.client,
        vh.telephone_client,
        v.produit,
        v.quantite,
        v.prix_origine,
        v.devise_origine,
        v.prix_mad as prix_vente_mad,
        (v.quantite * v.prix_mad) as total_vente_mad,
        v.achat_source_id,
        CASE 
            WHEN v.achat_source_id IS NOT NULL THEN a.prix_mad
            ELSE NULL
        END as prix_achat_mad,
        CASE 
            WHEN v.achat_source_id IS NOT NULL THEN (a.prix_mad * v.quantite)
            ELSE NULL
        END as total_achat_mad,
        CASE 
            WHEN v.achat_source_id IS NOT NULL THEN ((v.prix_mad - a.prix_mad) * v.quantite)
            ELSE NULL
        END as marge_mad,
        CASE 
            WHEN v.achat_source_id IS NOT NULL AND a.prix_mad > 0 
            THEN ((v.prix_mad - a.prix_mad) / a.prix_mad * 100)
            ELSE NULL
        END as marge_pourcentage,
        a2.fournisseur,
        a2.date as date_achat_source,
        v.type_attribution
    FROM ventes v
    JOIN ventes_headers vh ON v.vente_header_id = vh.id
    LEFT JOIN achats a ON v.achat_source_id = a.id
    LEFT JOIN achats_headers a2 ON a.achat_header_id = a2.id
    WHERE 1=1
    """
    
    params = []
    
    if produit:
        query += " AND v.produit = ?"
        params.append(produit)
    
    if date_debut:
        query += " AND vh.date >= ?"
        params.append(date_debut)
    
    if date_fin:
        query += " AND vh.date <= ?"
        params.append(date_fin)
    
    query += " ORDER BY vh.date DESC, vh.id DESC"
    
    return pd.read_sql(query, conn, params=params)

def get_produits_vendus(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Récupère la liste des produits qui ont été vendus avec des statistiques
    """
    query = """
    SELECT 
        v.produit,
        COUNT(DISTINCT v.vente_header_id) as nb_ventes,
        COUNT(v.id) as nb_lignes_vente,
        SUM(v.quantite) as quantite_totale_vendue,
        SUM(v.quantite * v.prix_mad) as chiffre_affaires_mad,
        AVG(v.prix_mad) as prix_vente_moyen,
        MIN(vh.date) as premiere_vente,
        MAX(vh.date) as derniere_vente
    FROM ventes v
    JOIN ventes_headers vh ON v.vente_header_id = vh.id
    GROUP BY v.produit
    ORDER BY chiffre_affaires_mad DESC
    """
    
    return pd.read_sql(query, conn)

def get_produits_achetes(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Récupère la liste des produits qui ont été achetés avec des statistiques
    """
    query = """
    SELECT 
        a.produit,
        COUNT(DISTINCT a.achat_header_id) as nb_factures,
        COUNT(a.id) as nb_lignes_achat,
        SUM(a.quantite) as quantite_totale_achetee,
        SUM(a.quantite * a.prix_mad) as cout_total_mad,
        AVG(a.prix_mad) as prix_achat_moyen,
        MIN(ah.date) as premier_achat,
        MAX(ah.date) as dernier_achat
    FROM achats a
    JOIN achats_headers ah ON a.achat_header_id = ah.id
    GROUP BY a.produit
    ORDER BY cout_total_mad DESC
    """
    
    return pd.read_sql(query, conn)

def gerer_quantites_multi_sources(conn, vente_header_id, produit, quantite_totale):
    """Gère l'attribution d'une quantité totale sur plusieurs achats sources"""
    st.markdown(f"**🔀 Répartition de {quantite_totale} '{produit}' sur plusieurs achats**")
    
    # Récupérer les achats disponibles pour ce produit
    achats_disponibles = pd.read_sql("""
        SELECT 
            a.id as achat_item_id,
            a.produit,
            ah.fournisseur,
            ah.date as date_achat,
            a.prix_mad as prix_achat_mad,
            (a.quantite - COALESCE((
                SELECT SUM(v2.quantite) 
                FROM ventes v2 
                WHERE v2.achat_source_id = a.id
            ), 0)) as quantite_restante
        FROM achats a
        JOIN achats_headers ah ON a.achat_header_id = ah.id
        WHERE a.produit = ? AND (a.quantite - COALESCE((
            SELECT SUM(v2.quantite) 
            FROM ventes v2 
            WHERE v2.achat_source_id = a.id
        ), 0)) > 0
        ORDER BY ah.date ASC
    """, conn, params=(produit,))
    
    if achats_disponibles.empty:
        st.error(f"❌ Aucun stock disponible pour '{produit}'")
        return
    
    quantite_restante = quantite_totale
    repartition = {}
    
    with st.form(f"form_repartition_{produit}"):
        st.markdown("**📊 Répartition des quantités:**")
        
        for _, achat in achats_disponibles.iterrows():
            max_quantite = min(achat['quantite_restante'], quantite_restante)
            if max_quantite > 0:
                quantite_achat = st.number_input(
                    f"Quantité depuis {achat['fournisseur']} (max: {max_quantite})",
                    min_value=0,
                    max_value=max_quantite,
                    value=0,
                    key=f"qte_{achat['achat_item_id']}"
                )
                repartition[achat['achat_item_id']] = quantite_achat
                quantite_restante -= quantite_achat
        
        st.write(f"**Quantité restante à attribuer: {quantite_restante}**")
        
        if st.form_submit_button("💾 Appliquer la répartition", use_container_width=True):
            if quantite_restante == 0:
                # Créer les articles de vente pour chaque source
                prix_vente = st.session_state.get(f'prix_{produit}', 0)
                devise = st.session_state.get(f'devise_{produit}', 'MAD')
                prix_mad = convertir_en_mad(prix_vente, devise, conn)
                
                for achat_id, qte in repartition.items():
                    if qte > 0:
                        insert_vente_item_avec_liaison_obligatoire(
                            conn, vente_header_id, produit, qte, 
                            prix_vente, devise, prix_mad, achat_id
                        )
                
                display_success_message(f"✅ Produit '{produit}' réparti sur {len(repartition)} sources d'achat")
                st.rerun()
            else:
                st.error(f"❌ Vous devez attribuer toute la quantité ({quantite_totale} unités)")

# -------- BASE DE DONNÉES --------
def get_conn(path: str = DB_PATH):
    conn = SupabaseAdapter()
    return conn

def create_tables(conn):
    pass

def update_database_structure(conn):
    try:
        # Vérification si la colonne existe déjà pour PostgreSQL
        check_col_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='ventes_headers' AND column_name='ville';
        """
        # Exécuter la vérification
        res = pd.read_sql(check_col_sql, conn)
        
        if res.empty:
            # La colonne n'existe pas, on l'ajoute
            conn.execute("ALTER TABLE ventes_headers ADD COLUMN ville TEXT;")
            if hasattr(conn, 'commit'):
                conn.commit()
    except Exception as e:
        # Fallback silencieux en cas d'erreur de schéma
        pass

def update_database_structure_v2(conn):
    pass

def update_database_structure_v3(conn):
    pass

def update_database_structure_v4(conn):
    try:
        # PostgreSQL check for table existence
        check_table_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name='hebdo';
        """
        res = pd.read_sql(check_table_sql, conn)
        
        if res.empty:
            conn.execute("""
                CREATE TABLE hebdo (
                    id SERIAL PRIMARY KEY,
                    date_debut DATE,
                    fond_de_caisse FLOAT DEFAULT 0,
                    salaire_1 FLOAT DEFAULT 0,
                    salaire_2 FLOAT DEFAULT 0,
                    notes TEXT
                );
            """)
            if hasattr(conn, 'commit'):
                conn.commit()
    except Exception as e:
        pass

def lier_depense_achat(conn: sqlite3.Connection, depense_id: int, achat_header_id: int) -> None:
    """Lie une dépense à un achat spécifique"""
    with conn:
        conn.execute(
            "UPDATE depenses SET achat_header_id = ?, type_depense = 'import' WHERE id = ?",
            (achat_header_id, depense_id)
        )

def dissocier_depense_achat(conn: sqlite3.Connection, depense_id: int) -> None:
    """Dissocie une dépense d'un achat"""
    with conn:
        conn.execute(
            "UPDATE depenses SET achat_header_id = NULL, type_depense = 'generale' WHERE id = ?",
            (depense_id,)
        )

def calculer_gains_par_achat_attribution(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calcule les gains BASÉ SUR LES ATTRIBUTIONS RÉELLES des ventes aux achats"""
    try:
        st.info("🔍 Calcul des gains basé sur les attributions réelles...")
        
        achats_headers = pd.read_sql("SELECT id, date, fournisseur, total_mad FROM achats_headers ORDER BY date", conn)
        achats_items = pd.read_sql("SELECT * FROM achats", conn)
        
        ventes_attribuees = pd.read_sql("""
            SELECT v.*, vh.date as date_vente, vh.client,
                   a.achat_header_id, a2.date as date_achat, a2.fournisseur
            FROM ventes v
            JOIN ventes_headers vh ON v.vente_header_id = vh.id
            LEFT JOIN achats a ON v.achat_source_id = a.id
            LEFT JOIN achats_headers a2 ON a.achat_header_id = a2.id
            WHERE v.achat_source_id IS NOT NULL
        """, conn)
        
        depenses = pd.read_sql("SELECT * FROM depenses WHERE type_depense = 'import'", conn)
        
        st.write(f"📦 Achats analysés: {len(achats_headers)}")
        st.write(f"💰 Ventes attribuées: {len(ventes_attribuees)}")
        
        if achats_headers.empty:
            return pd.DataFrame()
        
        # Normaliser les types pour éviter les mismatches int/float
        if not achats_items.empty and 'id' in achats_items.columns:
            achats_items['id'] = achats_items['id'].astype(int)
        if not achats_items.empty and 'achat_header_id' in achats_items.columns:
            achats_items['achat_header_id'] = achats_items['achat_header_id'].astype(int)
        if not ventes_attribuees.empty and 'achat_source_id' in ventes_attribuees.columns:
            ventes_attribuees['achat_source_id'] = ventes_attribuees['achat_source_id'].astype(int)
        if not achats_headers.empty and 'id' in achats_headers.columns:
            achats_headers['id'] = achats_headers['id'].astype(int)
        
        results = []
        total_revenus_debug = 0.0
        
        for _, achat in achats_headers.iterrows():
            achat_id = int(achat['id'])
            articles_achat = achats_items[achats_items['achat_header_id'] == achat_id]
            
            if articles_achat.empty:
                continue
            
            cout_achat = achat['total_mad']
            depenses_liees = depenses[depenses['achat_header_id'] == achat_id]
            cout_depenses = depenses_liees['montant_mad'].sum() if not depenses_liees.empty else 0
            cout_total = cout_achat + cout_depenses
            
            revenus = 0.0
            quantite_vendue_totale = 0
            
            for _, article in articles_achat.iterrows():
                achat_item_id = int(article['id'])
                produit = article['produit']
                
                ventes_attribuees_article = ventes_attribuees[ventes_attribuees['achat_source_id'] == achat_item_id]
                
                if not ventes_attribuees_article.empty:
                    revenus_article = (ventes_attribuees_article['prix_mad'] * ventes_attribuees_article['quantite']).sum()
                    quantite_article = ventes_attribuees_article['quantite'].sum()
                    
                    revenus += revenus_article
                    quantite_vendue_totale += quantite_article
            
            total_revenus_debug += revenus
            
            gain_net = revenus - cout_total
            marge = (gain_net / cout_total * 100) if cout_total > 0 else 0.0
            
            results.append({
                'achat_id': achat_id,
                'date_achat': achat['date'],
                'fournisseur': achat['fournisseur'],
                'cout_achat_mad': float(cout_achat),
                'cout_depenses_liees_mad': float(cout_depenses),
                'cout_total_mad': float(cout_total),
                'revenus_ventes_mad': float(revenus),
                'gain_net_mad': float(gain_net),
                'marge_percentage': float(marge),
                'nb_produits': len(articles_achat),
                'nb_depenses_liees': len(depenses_liees),
                'quantite_vendue': int(quantite_vendue_totale),
                'type_calcul': 'attribution_reelle'
            })
        
        df_result = pd.DataFrame(results)
        
        total_revenus_calcule = df_result['revenus_ventes_mad'].sum() if not df_result.empty else 0
        total_ventes_attribuees = (ventes_attribuees['prix_mad'] * ventes_attribuees['quantite']).sum() if not ventes_attribuees.empty else 0
        
        st.write(f"💰 Total revenus calculé: {total_revenus_calcule:.2f} MAD")
        st.write(f"💰 Total ventes attribuées: {total_ventes_attribuees:.2f} MAD")
        
        if abs(total_revenus_calcule - total_ventes_attribuees) > 0.01:
            ecart = total_ventes_attribuees - total_revenus_calcule
            st.warning(f"⚠️ Écart: {ecart:.2f} MAD")
            
            # Identifier les ventes orphelines (attribuées à un achat_source_id 
            # dont le achat_header_id n'est pas dans les headers analysés)
            ids_headers_analyses = set(achats_headers['id'].tolist())
            ids_items_analyses = set(achats_items[achats_items['achat_header_id'].isin(ids_headers_analyses)]['id'].tolist())
            
            ventes_orphelines = ventes_attribuees[~ventes_attribuees['achat_source_id'].isin(ids_items_analyses)]
            
            if not ventes_orphelines.empty:
                st.warning(f"🔍 {len(ventes_orphelines)} vente(s) orpheline(s) détectée(s) — attribuées à des achats introuvables:")
                for _, v in ventes_orphelines.iterrows():
                    montant_v = v['prix_mad'] * v['quantite']
                    st.write(f"  • Vente ID {v.get('id', '?')}, produit: {v.get('produit', '?')}, "
                             f"qté: {v.get('quantite', '?')}, montant: {montant_v:.2f} MAD, "
                             f"achat_source_id: {v.get('achat_source_id', '?')}")
        
        st.success(f"✅ Calcul basé sur attributions réelles terminé: {len(df_result)} achats analysés")
        return df_result
        
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return pd.DataFrame()

# -------- FONCTIONS DE GESTION (SUPPRESSION/MODIFICATION) --------
def supprimer_vente_header(conn: sqlite3.Connection, vente_header_id: int) -> None:
    """Supprime une vente complète (header + tous les articles)"""
    with conn:
        conn.execute("DELETE FROM ventes WHERE vente_header_id = ?", (vente_header_id,))
        conn.execute("DELETE FROM ventes_headers WHERE id = ?", (vente_header_id,))

def supprimer_vente_item(conn: sqlite3.Connection, vente_item_id: int) -> None:
    """Supprime un article d'une vente et met à jour le total"""
    with conn:
        vente_header_id = conn.execute(
            "SELECT vente_header_id FROM ventes WHERE id = ?", 
            (vente_item_id,)
        ).fetchone()[0]
        
        conn.execute("DELETE FROM ventes WHERE id = ?", (vente_item_id,))
        
        total_vente = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM ventes WHERE vente_header_id = ?",
            (vente_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE ventes_headers SET total_mad = ? WHERE id = ?",
            (float(total_vente), vente_header_id)
        )

def supprimer_achat_header(conn: sqlite3.Connection, achat_header_id: int) -> None:
    """Supprime un achat complète (header + tous les articles)"""
    with conn:
        conn.execute("DELETE FROM achats WHERE achat_header_id = ?", (achat_header_id,))
        conn.execute("DELETE FROM achats_headers WHERE id = ?", (achat_header_id,))

def supprimer_achat_item(conn: sqlite3.Connection, achat_item_id: int) -> None:
    """Supprime un article d'un achat et met à jour le total"""
    with conn:
        achat_header_id = conn.execute(
            "SELECT achat_header_id FROM achats WHERE id = ?", 
            (achat_item_id,)
        ).fetchone()[0]
        
        conn.execute("DELETE FROM achats WHERE id = ?", (achat_item_id,))
        
        total_achat = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM achats WHERE achat_header_id = ?",
            (achat_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE achats_headers SET total_mad = ? WHERE id = ?",
            (float(total_achat), achat_header_id)
        )
def ajouter_article_achat_existant(conn: sqlite3.Connection, achat_header_id: int, produit: str, 
                                 quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Ajoute un article à un achat existant"""
    with conn:
        conn.execute(
            """INSERT INTO achats (achat_header_id, produit, quantite, prix_mad, devise_origine, prix_origine) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (achat_header_id, produit, int(quantite), float(prix_mad), devise, float(prix_origine))
        )
        
        total_achat = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM achats WHERE achat_header_id = ?",
            (achat_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE achats_headers SET total_mad = ? WHERE id = ?",
            (float(total_achat), achat_header_id)
        )

def supprimer_depense(conn: sqlite3.Connection, depense_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM depenses WHERE id = ?", (depense_id,))

def supprimer_prestation(conn: sqlite3.Connection, prestation_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM paiements_prestations WHERE prestation_id = ?", (prestation_id,))
        conn.execute("DELETE FROM prestations WHERE id = ?", (prestation_id,))

def supprimer_paiement(conn: sqlite3.Connection, paiement_id: int) -> None:
    with conn:
        prestation_id = conn.execute(
            "SELECT prestation_id FROM paiements_prestations WHERE id = ?", 
            (paiement_id,)
        ).fetchone()[0]
        
        conn.execute("DELETE FROM paiements_prestations WHERE id = ?", (paiement_id,))
        
        paiements_totaux = conn.execute(
            "SELECT SUM(montant_mad) FROM paiements_prestations WHERE prestation_id = ?",
            (prestation_id,)
        ).fetchone()[0] or 0
        
        montant_total = conn.execute(
            "SELECT montant_mad FROM prestations WHERE id = ?",
            (prestation_id,)
        ).fetchone()[0]
        
        reste_a_payer = montant_total - paiements_totaux
        
        conn.execute(
            "UPDATE prestations SET avance_mad = ?, reste_a_payer_mad = ? WHERE id = ?",
            (float(paiements_totaux), float(reste_a_payer), prestation_id)
        )
        
        nouveau_statut = 'Payé' if reste_a_payer <= 0 else 'Confirmé'
        conn.execute(
            "UPDATE prestations SET statut = ? WHERE id = ?",
            (nouveau_statut, prestation_id)
        )

# -------- NOUVELLES FONCTIONS DE MODIFICATION --------
def modifier_vente_header(conn: sqlite3.Connection, vente_id: int, date_op: str, client: str, telephone_client: str, ville: str = "") -> None:
    """Modifie l'en-tête d'une vente"""
    with conn:
        conn.execute(
            "UPDATE ventes_headers SET date = ?, client = ?, telephone_client = ?, ville = ? WHERE id = ?",
            (date_op, client, telephone_client, ville, vente_id)
        )

def modifier_vente_item(conn: sqlite3.Connection, vente_item_id: int, produit: str, quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Modifie un article de vente"""
    with conn:
        conn.execute(
            """UPDATE ventes SET produit = ?, quantite = ?, prix_origine = ?, devise_origine = ?, prix_mad = ? 
               WHERE id = ?""",
            (produit, quantite, prix_origine, devise, prix_mad, vente_item_id)
        )
        
        vente_header_id = conn.execute(
            "SELECT vente_header_id FROM ventes WHERE id = ?", 
            (vente_item_id,)
        ).fetchone()[0]
        
        total_vente = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM ventes WHERE vente_header_id = ?",
            (vente_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE ventes_headers SET total_mad = ? WHERE id = ?",
            (float(total_vente), vente_header_id)
        )

def modifier_achat_header(conn: sqlite3.Connection, achat_id: int, date_op: str, fournisseur: str, type_achat: str) -> None:
    """Modifie l'en-tête d'un achat"""
    with conn:
        conn.execute(
            "UPDATE achats_headers SET date = ?, fournisseur = ?, type = ? WHERE id = ?",
            (date_op, fournisseur, type_achat, achat_id)
        )

def modifier_achat_item(conn: sqlite3.Connection, achat_item_id: int, produit: str, quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Modifie un article d'achat"""
    with conn:
        conn.execute(
            """UPDATE achats SET produit = ?, quantite = ?, prix_origine = ?, devise_origine = ?, prix_mad = ? 
               WHERE id = ?""",
            (produit, quantite, prix_origine, devise, prix_mad, achat_item_id)
        )
        
        achat_header_id = conn.execute(
            "SELECT achat_header_id FROM achats WHERE id = ?", 
            (achat_item_id,)
        ).fetchone()[0]
        
        total_achat = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM achats WHERE achat_header_id = ?",
            (achat_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE achats_headers SET total_mad = ? WHERE id = ?",
            (float(total_achat), achat_header_id)
        )

def modifier_depense(conn: sqlite3.Connection, depense_id: int, date_op: str, categorie: str, montant_origine: float, devise: str, montant_mad: float, description: str, source_fonds: str = "argent_disponible", achat_header_id: int = None) -> None:
    """Modifie une dépense"""
    type_depense = 'import' if achat_header_id is not None else 'generale'
    
    with conn:
        conn.execute(
            """UPDATE depenses SET date = ?, categorie = ?, montant_origine = ?, devise_origine = ?, 
               montant_mad = ?, description = ?, source_fonds = ?, achat_header_id = ?, type_depense = ? WHERE id = ?""",
            (date_op, categorie, montant_origine, devise, montant_mad, description, source_fonds, achat_header_id, type_depense, depense_id)
        )

def modifier_prestation(conn: sqlite3.Connection, prestation_id: int, date_op: str, client: str, telephone_client: str, 
                       type_prestation: str, description: str, montant_mad: float, devise: str, 
                       montant_origine: float, avance_mad: float) -> None:
    """Modifie une prestation"""
    reste_a_payer = montant_mad - avance_mad
    statut = 'Payé' if reste_a_payer <= 0 else 'Devis'
    
    with conn:
        conn.execute(
            """UPDATE prestations SET date = ?, client = ?, telephone_client = ?, type_prestation = ?, 
               description = ?, montant_mad = ?, devise_origine = ?, montant_origine = ?, 
               avance_mad = ?, reste_a_payer_mad = ?, statut = ? WHERE id = ?""",
            (date_op, client, telephone_client, type_prestation, description, 
             float(montant_mad), devise, float(montant_origine),
             float(avance_mad), float(reste_a_payer), statut, prestation_id)
        )

# -------- NOUVELLES FONCTIONS POUR AJOUTER DES ARTICLES --------
def ajouter_article_vente_existante(conn: sqlite3.Connection, vente_header_id: int, produit: str, 
                                  quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Ajoute un article à une vente existante"""
    insert_vente_item(conn, vente_header_id, produit, quantite, prix_origine, devise, prix_mad)

def ajouter_articles_vente_simplifie(conn, vente_header_id):
    """Interface simplifiée pour ajouter des articles à une vente (avec option hors stock)"""

    st.markdown("<div class='section-header'>🛒 Ajouter des Articles à la Vente</div>", unsafe_allow_html=True)

    # --- Charger les produits disponibles ---
    achats_disponibles = pd.read_sql("""
        SELECT 
            a.id AS achat_item_id,
            a.produit,
            a.quantite AS quantite_achetee,
            ah.date AS date_achat,
            ah.fournisseur,
            a.prix_mad AS prix_achat_mad,
            (a.quantite - COALESCE((
                SELECT SUM(v2.quantite) 
                FROM ventes v2 
                WHERE v2.achat_source_id = a.id
            ), 0)) AS quantite_restante
        FROM achats a
        JOIN achats_headers ah ON a.achat_header_id = ah.id
        WHERE (a.quantite - COALESCE((
            SELECT SUM(v2.quantite) 
            FROM ventes v2 
            WHERE v2.achat_source_id = a.id
        ), 0)) > 0
        ORDER BY a.produit, ah.date ASC
    """, conn)

    # --- Choix du mode de vente ---
    mode = st.radio(
        "🛍️ Choisir le type d'article à vendre :",
        ["Depuis le stock (achat existant)", "Produit hors stock / libre"],
        horizontal=True,
        key="mode_vente"
    )

    # --- Cas 1 : Vente depuis le stock ---
    if mode == "Depuis le stock (achat existant)":
        if achats_disponibles.empty:
            st.warning("📦 Aucun stock disponible. Vous pouvez vendre un produit hors stock.")
            return

        st.info(f"📊 **{len(achats_disponibles)} produits disponibles en stock**")

        def format_option(achat_id):
            achat = achats_disponibles.loc[achats_disponibles['achat_item_id'] == achat_id].iloc[0]
            return f"{achat['produit']} | {achat['fournisseur']} | 📅 {achat['date_achat']} | 📦 {achat['quantite_restante']} unités | 💰 {achat['prix_achat_mad']:.2f} MAD"

        achat_selectionne_id = st.selectbox(
            "📦 Sélectionner le produit à vendre :",
            options=achats_disponibles['achat_item_id'].tolist(),
            format_func=format_option,
            key="achat_selectionne"
        )

        achat_selectionne_data = achats_disponibles.loc[
            achats_disponibles['achat_item_id'] == achat_selectionne_id
        ].iloc[0]

        st.markdown("### 📋 Produit sélectionné :")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Produit :** {achat_selectionne_data['produit']}")
            st.write(f"**Fournisseur :** {achat_selectionne_data['fournisseur']}")
            st.write(f"**Date d'achat :** {achat_selectionne_data['date_achat']}")
        with col2:
            st.write(f"**Stock disponible :** {achat_selectionne_data['quantite_restante']} unités")
            st.write(f"**Prix d'achat :** {achat_selectionne_data['prix_achat_mad']:.2f} MAD")
            st.write(f"**ID Achat :** #{achat_selectionne_id}")

        # --- Formulaire vente ---
        with st.form("form_vente_stock", clear_on_submit=True):
            st.markdown("### 💵 Informations de la vente")
            col1, col2, col3 = st.columns(3)
            with col1:
                quantite = st.number_input(
                    "🔢 Quantité à vendre",
                    min_value=1,
                    max_value=int(achat_selectionne_data['quantite_restante']),
                    value=1
                )
            with col2:
                prix_vente = st.number_input("💰 Prix de vente unitaire", min_value=0.0, value=0.0, step=0.01)
            with col3:
                devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES)

            # --- Marge prévisionnelle ---
            if prix_vente > 0:
                prix_mad_vente = convertir_en_mad(prix_vente, devise, conn)
                marge_unitaire = prix_mad_vente - achat_selectionne_data['prix_achat_mad']
                marge_totale = marge_unitaire * quantite
                marge_pourcentage = (
                    marge_unitaire / achat_selectionne_data['prix_achat_mad'] * 100
                    if achat_selectionne_data['prix_achat_mad'] > 0 else 0
                )
                st.info(f"**💰 Marge prévisionnelle :** {marge_totale:.2f} MAD ({marge_pourcentage:.1f}%)")

            submitted = st.form_submit_button("➕ Ajouter à la vente")

        # --- Traitement ---
        if submitted:
            try:
                if prix_vente <= 0:
                    st.error("❌ Le prix de vente doit être supérieur à 0.")
                    return

                prix_mad_vente = convertir_en_mad(prix_vente, devise, conn)
                stock_actuel = conn.execute("""
                    SELECT (a.quantite - COALESCE((
                        SELECT SUM(v2.quantite) FROM ventes v2 WHERE v2.achat_source_id = a.id
                    ), 0)) AS quantite_restante
                    FROM achats a
                    WHERE a.id = ?
                """, (achat_selectionne_id,)).fetchone()

                if not stock_actuel or stock_actuel['quantite_restante'] < quantite:
                    st.error("❌ Stock insuffisant ou mis à jour entre-temps.")
                    st.rerun()

                insert_vente_item_avec_liaison_obligatoire(
                    conn, vente_header_id, achat_selectionne_data['produit'], quantite,
                    prix_vente, devise, prix_mad_vente, achat_selectionne_id
                )

                st.success(f"✅ {quantite} × {achat_selectionne_data['produit']} ajouté(s) à la vente.")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    # --- Cas 2 : Vente hors stock ---
    else:
        st.markdown("### 🆕 Vente d’un produit hors stock")

        with st.form("form_vente_libre", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                produit = st.text_input("🏷️ Nom du produit", "")
                quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
            with col2:
                prix_vente = st.number_input("💰 Prix unitaire", min_value=0.0, value=0.0, step=0.01)
                devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES)

            st.info("💡 Ces produits ne sont pas liés à un achat, donc pas de calcul de marge automatique.")
            submitted_libre = st.form_submit_button("➕ Ajouter cet article libre")

        if submitted_libre:
            if not produit or prix_vente <= 0:
                st.error("❌ Veuillez saisir un nom de produit et un prix valide.")
                return

            try:
                prix_mad = convertir_en_mad(prix_vente, devise, conn)
                insert_vente_item_avec_liaison_obligatoire(
                    conn, vente_header_id, produit, quantite,
                    prix_vente, devise, prix_mad, achat_source_id=None
                )
                st.success(f"✅ {quantite} × {produit} ajouté(s) à la vente (hors stock).")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de l’ajout : {e}")

    # --- Afficher le panier ---
    afficher_panier_actuel(conn, vente_header_id)

def afficher_panier_actuel(conn, vente_header_id):
    """Affiche le panier actuel avec option de finalisation (compatible ventes hors stock)."""
    
    # --- Récupérer les articles de la vente ---
    articles_vente = pd.read_sql("""
        SELECT 
            v.*,
            a.prix_mad AS prix_achat_mad,
            ah.fournisseur,
            a.produit AS produit_achat
        FROM ventes v
        LEFT JOIN achats a ON v.achat_source_id = a.id
        LEFT JOIN achats_headers ah ON a.achat_header_id = ah.id
        WHERE v.vente_header_id = ?
        ORDER BY v.id DESC
    """, conn, params=(vente_header_id,))
    
    if articles_vente.empty:
        st.info("🛒 Aucun article ajouté au panier")
        return
    
    st.markdown("---")
    st.markdown("<div class='section-header'>📋 Panier Actuel</div>", unsafe_allow_html=True)
    
    # --- Préparer les colonnes manquantes pour produits hors stock ---
    articles_vente['prix_achat_mad'] = articles_vente['prix_achat_mad'].fillna(0)
    articles_vente['fournisseur'] = articles_vente['fournisseur'].fillna("—")
    articles_vente['produit_achat'] = articles_vente.apply(
        lambda x: x['produit'] if pd.isna(x['produit_achat']) else x['produit_achat'],
        axis=1
    )
    
    # --- Calcul des marges ---
    panier_display = articles_vente.copy()
    panier_display['Total Vente MAD'] = panier_display['quantite'] * panier_display['prix_mad']
    panier_display['Total Achat MAD'] = panier_display['quantite'] * panier_display['prix_achat_mad']
    panier_display['Marge MAD'] = panier_display['Total Vente MAD'] - panier_display['Total Achat MAD']
    
    # CORRECTION : Calculer la marge en pourcentage avec gestion des cas hors stock
    def calculer_marge_pourcentage(row):
        if row['Total Achat MAD'] > 0:
            return (row['Marge MAD'] / row['Total Achat MAD'] * 100)
        elif pd.isna(row['achat_source_id']):
            return None  # Produit hors stock - pas de calcul de marge
        else:
            return 0  # Cas où prix achat est 0 mais produit est lié à un achat
    
    panier_display['Marge %'] = panier_display.apply(calculer_marge_pourcentage, axis=1)
    
    # Arrondir les valeurs numériques
    panier_display['Marge %'] = panier_display['Marge %'].apply(
        lambda x: round(x, 1) if pd.notnull(x) and isinstance(x, (int, float)) else x
    )
    
    # --- Label pour indiquer le type de produit ---
    panier_display['Origine'] = panier_display.apply(
        lambda r: "🟢 Hors stock" if pd.isna(r['achat_source_id']) else f"🔵 Achat #{int(r['achat_source_id'])}",
        axis=1
    )
    
    # --- Afficher le tableau ---
    display_cols = [
        'produit_achat', 'quantite', 'prix_mad', 'Total Vente MAD',
        'prix_achat_mad', 'Total Achat MAD', 'Marge MAD', 'Marge %', 'fournisseur', 'Origine'
    ]
    
    st.dataframe(
        panier_display[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "produit_achat": "Produit",
            "quantite": "Quantité",
            "prix_mad": "Prix Vente",
            "Total Vente MAD": "Total Vente",
            "prix_achat_mad": "Prix Achat",
            "Total Achat MAD": "Total Achat",
            "Marge MAD": "Marge",
            "Marge %": "Marge %",
            "fournisseur": "Fournisseur",
            "Origine": "Source"
        }
    )
    
    # --- Interface de suppression d'article ---
    st.markdown("### 🗑️ Gérer les articles")
    col_del1, col_del2 = st.columns([3, 1])
    with col_del1:
        options_suppr = {row['id']: f"{row['produit_achat']} ({row['quantite']} unités) - {float(row['prix_mad']):.2f} MAD" for _, row in articles_vente.iterrows()}
        item_to_delete = st.selectbox("Sélectionner un article à supprimer", options=list(options_suppr.keys()), format_func=lambda x: options_suppr.get(x, ""), key=f"sel_del_{vente_header_id}")
    with col_del2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❌ Supprimer l'article", key=f"btn_del_{vente_header_id}", use_container_width=True):
            if item_to_delete:
                try:
                    supprimer_vente_item(conn, item_to_delete)
                    st.success("Article supprimé avec succès!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la suppression: {e}")
                    
    # --- Totaux globaux ---
    total_vente = panier_display['Total Vente MAD'].sum()
    total_achat = panier_display['Total Achat MAD'].sum()
    total_marge = panier_display['Marge MAD'].sum()
    
    # Calculer la marge moyenne uniquement sur les produits avec calcul de marge
    produits_avec_marge = panier_display[panier_display['Marge %'].notna()]
    marge_moyenne = produits_avec_marge['Marge %'].mean() if not produits_avec_marge.empty else None
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Vente", f"{total_vente:.2f} MAD")
    with col2:
        st.metric("📦 Coût Total", f"{total_achat:.2f} MAD")
    with col3:
        st.metric("✅ Marge Totale", f"{total_marge:.2f} MAD")
    with col4:
        if marge_moyenne is not None:
            st.metric("📊 Marge Moyenne", f"{marge_moyenne:.1f}%")
        else:
            st.metric("📊 Marge Moyenne", "—")
    
    # --- Informations supplémentaires ---
    nb_articles_hors_stock = panier_display[panier_display['Origine'].str.contains("Hors stock")].shape[0]
    if nb_articles_hors_stock > 0:
        st.info(f"📝 **Note :** {nb_articles_hors_stock} article(s) hors stock - Marge non calculée")
    
    # --- Actions ---
    if st.button("✅ Finaliser la Vente", type="primary", use_container_width=True, key=f"finaliser_vente_{vente_header_id}"):
        del st.session_state.current_vente_id
        st.success("🎉 Vente finalisée avec succès !")
        st.balloons()
        st.rerun()
        
    if st.button("❌ Annuler la Vente", type="secondary", use_container_width=True, key=f"annuler_vente_{vente_header_id}"):
        supprimer_vente_header(conn, vente_header_id)
        del st.session_state.current_vente_id
        st.info("📝 Vente annulée")
        st.rerun()

# -------- FONCTIONS D'INSERTION --------
def insert_vente_header(conn: sqlite3.Connection, date_op: str, client: str, telephone_client: str, ville: str = "") -> int:
    """Crée un en-tête de vente et retourne son ID"""
    with conn:
        cursor = conn.execute(
            """INSERT INTO ventes_headers (date, client, telephone_client, ville) 
               VALUES (?, ?, ?, ?)""",
            (date_op, client, telephone_client, ville)
        )
        return cursor.lastrowid

def insert_vente_item(conn: sqlite3.Connection, vente_header_id: int, produit: str, 
                     quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Ajoute un article à une vente existante"""
    with conn:
        conn.execute(
            """INSERT INTO ventes (vente_header_id, produit, quantite, prix_mad, devise_origine, prix_origine) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (vente_header_id, produit, int(quantite), float(prix_mad), devise, float(prix_origine))
        )
        
        total_vente = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM ventes WHERE vente_header_id = ?",
            (vente_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE ventes_headers SET total_mad = ? WHERE id = ?",
            (float(total_vente), vente_header_id)
        )

def insert_vente_item_avec_liaison_obligatoire(conn, vente_header_id, produit, quantite, 
                                               prix_origine, devise, prix_mad, achat_source_id=None):
    """Ajoute un article à une vente, avec ou sans liaison à un achat (contrôle de stock si lié)."""
    
    # --- Si la vente est liée à un achat, on fait les contrôles ---
    if achat_source_id is not None:
        stock_restant = conn.execute("""
            SELECT 
                (a.quantite - COALESCE((
                    SELECT SUM(v2.quantite) 
                    FROM ventes v2 
                    WHERE v2.achat_source_id = a.id
                ), 0)) as quantite_restante,
                a.produit as produit_achat
            FROM achats a
            WHERE a.id = ?
        """, (achat_source_id,)).fetchone()
        
        if not stock_restant:
            raise ValueError(f"L'achat source #{achat_source_id} n'existe pas")
        
        if stock_restant['quantite_restante'] < quantite:
            raise ValueError(f"Stock insuffisant dans l'achat #{achat_source_id}. Stock restant: {stock_restant['quantite_restante']}")
        
        if stock_restant['produit_achat'] != produit:
            raise ValueError(f"L'achat #{achat_source_id} concerne le produit '{stock_restant['produit_achat']}', pas '{produit}'")
        
        type_attribution = "obligatoire"
    else:
        # --- Vente hors stock ---
        type_attribution = "hors_stock"
    
    # --- Insertion de l'article ---
    with conn:
        cursor = conn.execute(
            """INSERT INTO ventes (
                vente_header_id, produit, quantite, prix_mad, devise_origine, prix_origine, achat_source_id, type_attribution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (vente_header_id, produit, int(quantite), float(prix_mad), devise, float(prix_origine), achat_source_id, type_attribution)
        )
        
        # --- Mise à jour du total de la vente ---
        total_vente = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM ventes WHERE vente_header_id = ?",
            (vente_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE ventes_headers SET total_mad = ? WHERE id = ?",
            (float(total_vente), vente_header_id)
        )
    
    return cursor.lastrowid

def insert_achat_header(conn: sqlite3.Connection, date_op: str, fournisseur: str, type_achat: str = "achat") -> int:
    """Crée un en-tête d'achat et retourne son ID"""
    with conn:
        cursor = conn.execute(
            """INSERT INTO achats_headers (date, fournisseur, type) 
               VALUES (?, ?, ?)""",
            (date_op, fournisseur, type_achat)
        )
        return cursor.lastrowid

def insert_achat_item(conn: sqlite3.Connection, achat_header_id: int, produit: str, 
                     quantite: int, prix_origine: float, devise: str, prix_mad: float) -> None:
    """Ajoute un article à un achat existant"""
    with conn:
        conn.execute(
            """INSERT INTO achats (achat_header_id, produit, quantite, prix_mad, devise_origine, prix_origine) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (achat_header_id, produit, int(quantite), float(prix_mad), devise, float(prix_origine))
        )
        
        total_achat = conn.execute(
            "SELECT SUM(prix_mad * quantite) FROM achats WHERE achat_header_id = ?",
            (achat_header_id,)
        ).fetchone()[0] or 0
        
        conn.execute(
            "UPDATE achats_headers SET total_mad = ? WHERE id = ?",
            (float(total_achat), achat_header_id)
        )

def insert_depense(conn: sqlite3.Connection, date_op: str, categorie: str, 
                  montant_origine: float, devise: str, montant_mad: float, description: str,
                  source_fonds: str = "argent_disponible", achat_header_id: int = None) -> None:
    """Insère une dépense avec indication de la source des fonds"""
    type_depense = 'import' if achat_header_id is not None else 'generale'
    
    with conn:
        conn.execute(
            """INSERT INTO depenses (date, categorie, montant_mad, description, devise_origine, 
               montant_origine, source_fonds, achat_header_id, type_depense) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date_op, categorie, float(montant_mad), description, devise, 
             float(montant_origine), source_fonds, achat_header_id, type_depense),
        )

def insert_prestation(conn: sqlite3.Connection, date_op: str, client: str, telephone_client: str, 
                     type_prestation: str, description: str, montant_mad: float, devise: str, 
                     montant_origine: float, avance_mad: float) -> int:
    reste_a_payer = montant_mad - avance_mad
    statut = 'Payé' if reste_a_payer <= 0 else 'Devis'
    
    with conn:
        cursor = conn.execute(
            """INSERT INTO prestations (date, client, telephone_client, type_prestation, description, 
               montant_mad, devise_origine, montant_origine, avance_mad, reste_a_payer_mad, statut) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date_op, client, telephone_client, type_prestation, description, 
             float(montant_mad), devise, float(montant_origine),
             float(avance_mad), float(reste_a_payer), statut),
        )
        return cursor.lastrowid

def insert_paiement_prestation(conn: sqlite3.Connection, prestation_id: int, date_paiement: str,
                              montant_mad: float, devise: str, montant_origine: float,
                              reference: str) -> None:
    with conn:
        conn.execute(
            """INSERT INTO paiements_prestations (prestation_id, date_paiement, montant_mad, 
               devise_origine, montant_origine, type_paiement, reference) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (prestation_id, date_paiement, float(montant_mad), devise, float(montant_origine),
             "Espèces", reference),
        )
        
        paiements_totaux = conn.execute(
            "SELECT SUM(montant_mad) FROM paiements_prestations WHERE prestation_id = ?",
            (prestation_id,)
        ).fetchone()[0] or 0
        
        montant_total = conn.execute(
            "SELECT montant_mad FROM prestations WHERE id = ?",
            (prestation_id,)
        ).fetchone()[0]
        
        reste_a_payer = montant_total - paiements_totaux
        
        conn.execute(
            "UPDATE prestations SET avance_mad = ?, reste_a_payer_mad = ? WHERE id = ?",
            (float(paiements_totaux), float(reste_a_payer), prestation_id)
        )
        
        if reste_a_payer <= 0:
            conn.execute(
                "UPDATE prestations SET statut = 'Payé' WHERE id = ?",
                (prestation_id,)
            )
        else:
            conn.execute(
                "UPDATE prestations SET statut = 'Confirmé' WHERE id = ?",
                (prestation_id,)
            )

def update_statut_prestation(conn: sqlite3.Connection, prestation_id: int, nouveau_statut: str) -> None:
    with conn:
        conn.execute(
            "UPDATE prestations SET statut = ? WHERE id = ?",
            (nouveau_statut, prestation_id)
        )

# -------- FONCTIONS POUR PAIEMENTS --------
def get_paiements_prestation(prestation_id: int) -> pd.DataFrame:
    """Récupère tous les paiements d'une prestation"""
    conn = get_conn()
    try:
        df = pd.read_sql(
            "SELECT * FROM paiements_prestations WHERE prestation_id = ? ORDER BY date_paiement",
            conn, params=(prestation_id,)
        )
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des paiements: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# -------- FONCTIONS POUR LES DÉTAILS PAR CLIENT/FOURNISSEUR --------
def get_ventes_par_client(conn: sqlite3.Connection) -> pd.DataFrame:
    """Récupère les ventes groupées par client"""
    query = """
    SELECT 
        client,
        COUNT(*) as nb_ventes,
        SUM(total_mad) as total_mad,
        AVG(total_mad) as moyenne_vente,
        MIN(date) as premiere_vente,
        MAX(date) as derniere_vente
    FROM ventes_headers 
    GROUP BY client
    ORDER BY total_mad DESC
    """
    return pd.read_sql(query, conn)

def get_achats_par_fournisseur(conn: sqlite3.Connection) -> pd.DataFrame:
    """Récupère les achats groupées par fournisseur"""
    query = """
    SELECT 
        fournisseur,
        COUNT(*) as nb_achats,
        SUM(total_mad) as total_mad,
        AVG(total_mad) as moyenne_achat,
        MIN(date) as premier_achat,
        MAX(date) as dernier_achat
    FROM achats_headers 
    GROUP BY fournisseur
    ORDER BY total_mad DESC
    """
    return pd.read_sql(query, conn)

def get_prestations_par_client(conn: sqlite3.Connection) -> pd.DataFrame:
    """Récupère les prestations groupées par client"""
    query = """
    SELECT 
        client,
        COUNT(*) as nb_prestations,
        SUM(montant_mad) as total_mad,
        AVG(montant_mad) as moyenne_prestation,
        SUM(avance_mad) as total_avances,
        SUM(reste_a_payer_mad) as total_reste,
        MIN(date) as premiere_prestation,
        MAX(date) as derniere_prestation
    FROM prestations 
    GROUP BY client
    ORDER BY total_mad DESC
    """
    return pd.read_sql(query, conn)

def get_detail_client(conn: sqlite3.Connection, client: str) -> pd.DataFrame:
    """Récupère le détail complet d'un client"""
    query_ventes = """
    SELECT 
        'Vente' as type,
        date,
        total_mad as montant,
        'MAD' as devise,
        'Vente de produits' as description
    FROM ventes_headers 
    WHERE client = ?
    """
    
    query_prestations = """
    SELECT 
        'Prestation' as type,
        date,
        montant_mad as montant,
        devise_origine as devise,
        type_prestation as description
    FROM prestations 
    WHERE client = ?
    """
    
    ventes = pd.read_sql(query_ventes, conn, params=(client,))
    prestations = pd.read_sql(query_prestations, conn, params=(client,))
    
    return pd.concat([ventes, prestations], ignore_index=True).sort_values('date', ascending=False)

def get_detail_fournisseur(conn: sqlite3.Connection, fournisseur: str) -> pd.DataFrame:
    """Récupère le détail complet d'un fournisseur"""
    query = """
    SELECT 
        date,
        type,
        total_mad as montant,
        'MAD' as devise
    FROM achats_headers 
    WHERE fournisseur = ?
    ORDER BY date DESC
    """
    return pd.read_sql(query, conn, params=(fournisseur,))

# -------- TAUX DE CHANGE --------
def taux_par_defaut(devise: str) -> float:
    fallback = {
        "USD": 10.00,
        "TRY": 0.22
    }
    taux = fallback.get(devise, 1.0)
    return float(taux)

def get_taux_depuis_api(devise: str) -> Optional[float]:
    try:
        url = f"https://api.exchangerate.host/convert?from={devise}&to=MAD"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('success', False) and 'result' in data:
            return float(data['result'])
        
        url = f"https://api.exchangerate.host/latest?base={devise}&symbols=MAD"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('success', False):
            taux = data.get('rates', {}).get('MAD')
            if taux is not None:
                return float(taux)
        
        return None
        
    except Exception as e:
        st.error(f"❌ Erreur API pour {devise}: {e}")
        return None

def sauvegarder_taux(conn: sqlite3.Connection, devise: str, taux: float, source: str = "api") -> None:
    today = date.today().isoformat()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO taux_change (devise, taux, date, source) VALUES (?, ?, ?, ?)",
            (devise, float(taux), today, source)
        )

def get_taux_cached(devise: str, conn: sqlite3.Connection) -> float:
    if devise == "MAD":
        return 1.0

    today = date.today().isoformat()
    
    row = conn.execute(
        "SELECT taux, source FROM taux_change WHERE devise = ? AND date = ?",
        (devise, today)
    ).fetchone()
    
    if row:
        return float(row['taux'])

    taux_api = get_taux_depuis_api(devise)
    
    if taux_api is not None:
        sauvegarder_taux(conn, devise, taux_api, "api")
        return taux_api
    else:
        st.warning(f"⚠️ Taux {devise}→MAD non trouvé, utilisation d'un taux par défaut.")
        taux_defaut = taux_par_defaut(devise)
        sauvegarder_taux(conn, devise, taux_defaut, "defaut")
        return taux_defaut

def convertir_en_mad(montant: float, devise: str, conn: sqlite3.Connection) -> float:
    try:
        if devise == "MAD":
            return float(montant)
        
        taux = get_taux_cached(devise, conn)
        resultat = float(montant) * taux
        return round(resultat, 2)
    except Exception as e:
        st.error(f"❌ Erreur conversion {devise}→MAD: {e}")
        return 0.0

# -------- INTERFACE GESTION TAUX --------
def interface_gestion_taux(conn: sqlite3.Connection):
    st.sidebar.markdown("<div class='subsection-header'>💱 Gestion des taux de change</div>", unsafe_allow_html=True)
    
    with st.sidebar.expander("📊 Définir taux manuellement", expanded=False):
        devise_manuelle = st.selectbox("Devise", [d for d in SUPPORTED_DEVISES if d != "MAD"])
        taux_actuel = conn.execute(
            "SELECT taux, source FROM taux_change WHERE devise = ? AND date = ?",
            (devise_manuelle, date.today().isoformat())
        ).fetchone()
        
        taux_par_defaut_val = taux_par_defaut(devise_manuelle)
        valeur_initiale = float(taux_actuel[0]) if taux_actuel else taux_par_defaut_val
        
        nouveau_taux = st.number_input(
            f"Taux {devise_manuelle}→MAD", 
            min_value=0.0001, 
            value=valeur_initiale,
            format="%.4f",
            key="taux_manuel_input"
        )
        
        if st.button("💾 Sauvegarder le taux manuel", key="save_taux_manuel", use_container_width=True):
            sauvegarder_taux(conn, devise_manuelle, nouveau_taux, "manuel")
            display_success_message(f"Taux {devise_manuelle}→MAD sauvegardé: {nouveau_taux}")
    
    with st.sidebar.expander("📈 Historique des taux", expanded=False):
        try:
            taux_history = pd.read_sql(
                "SELECT devise, taux, date, source FROM taux_change ORDER BY date DESC LIMIT 10", 
                conn
            )
            if not taux_history.empty:
                st.dataframe(taux_history, use_container_width=True)
            else:
                st.info("Aucun taux enregistré")
        except:
            st.info("Aucun taux enregistré")

def initialize_session_state():
    """Initialise les variables de session state pour les filtres"""
    if 'filtre_prestation_type' not in st.session_state:
        st.session_state.filtre_prestation_type = "Tous"
    if 'filtre_prestation_statut' not in st.session_state:
        st.session_state.filtre_prestation_statut = "Tous"
    if 'filtre_prestation_client' not in st.session_state:
        st.session_state.filtre_prestation_client = ""

# -------- APPLICATION STREAMLIT COMPLÈTE --------

def check_password():
    """Return `True` if the user had the correct password."""
    def password_entered():
        import streamlit as st
        # Utiliser .strip() pour ignorer les espaces accidentels
        pwd = st.session_state.get("password", "").strip()
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state["password_correct"] = True
            if "password" in st.session_state:
                del st.session_state["password"]  # clean up session
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<h2 style='text-align: center; margin-top: 15%;'>🔒 Accès Sécurisé</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Veuillez entrer le mot de passe de l'application.")
        st.text_input(
            "👉 Mot de passe", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Mot de passe incorrect")
            
    return False


def apply_custom_chart_style(fig):
    """
    Uniformise le design des graphiques Plotly
    """
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#64748b"),
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        separators=", ",
        showlegend=True
    )
    if hasattr(fig, 'update_xaxes'):
        fig.update_xaxes(
            showgrid=True, 
            gridcolor='rgba(226, 232, 240, 0.4)', 
            linecolor='rgba(226, 232, 240, 0.8)',
            zeroline=False
        )
    if hasattr(fig, 'update_yaxes'):
        fig.update_yaxes(
            showgrid=True, 
            gridcolor='rgba(226, 232, 240, 0.4)', 
            linecolor='rgba(226, 232, 240, 0.8)',
            zeroline=False,
            tickformat=',.0f'
        )
    return fig

def main() -> None:
    st.set_page_config(
        page_title="Gestion Commerciale Pro", 
        layout="wide",
        page_icon="🏢",
        initial_sidebar_state="expanded"
    )
    
    if not check_password():
        st.stop()
        
    inject_custom_css()
    initialize_session_state()
    conn = get_conn()
    create_tables(conn)
    update_database_structure(conn)
    update_database_structure_v2(conn)
    update_database_structure_v3(conn)
    update_database_structure_v4(conn)

    # Sidebar avec style amélioré
    with st.sidebar:
        # Afficher le logo au lieu du texte
        st.image("logo.jpg", width=200)  # Remplacez par le nom réel de votre logo
        st.markdown("---")
        
        menu = st.radio(
            "Navigation", 
            ["📦 Ventes", "🛒 Achats", "💰 Dépenses", "🎯 Prestations", "📊 Tableau de Bord", "📅 Hebdo", "🔧 Devises", "👥 Clients & Fournisseurs"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        interface_gestion_taux(conn)
        
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #7f8c8d; font-size: 0.8rem;'>"
            "Système de Gestion Commerciale<br>© 2025"
            "</div>", 
            unsafe_allow_html=True
        )

    if menu == "📦 Ventes":
        display_view_header("Gestion des Ventes", "Gérez vos ventes et suivez votre chiffre d'affaires", "📦")
        
        tab_ventes1, tab_ventes2, tab_ventes3, tab_ventes4 = st.tabs(["➕ Nouvelle Vente", "🗂️ Historique & Gestion", "✏️ Modifier Vente", "🔗 Attribution Achats"])
        
        with tab_ventes1:
            # === NOUVELLE VENTE SIMPLIFIÉE ===
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            
            # Étape 1 : Créer la fiche de vente (ou récupérer si existe déjà)
            if 'current_vente_id' not in st.session_state:
                # Aucune vente en cours - afficher le formulaire de création
                st.markdown("<div class='section-header'>📋 Nouvelle Vente</div>", unsafe_allow_html=True)
                
                with st.form("form_vente_header_simple"):
                    col1, col2 = st.columns(2)
                    with col1:
                        date_vente = st.date_input("📅 Date de la vente", value=date.today())
                        client = st.text_input("👤 Nom du client", placeholder="Nom complet du client")
                    with col2:
                        telephone = st.text_input("📞 Téléphone", placeholder="06XXXXXXXX")
                        ville = st.text_input("🏙️ Ville", placeholder="Ex: Casablanca", key="new_sale_ville")
                    
                    submitted_header = st.form_submit_button("📋 Créer la fiche de vente", use_container_width=True)
                
                if submitted_header:
                    if not client.strip():
                        st.error("❌ Veuillez saisir le nom du client")
                    else:
                        vente_id = insert_vente_header(conn, date_vente.isoformat(), client.strip(), telephone.strip(), ville.strip())
                        st.session_state.current_vente_id = vente_id
                        st.success(f"✅ Fiche de vente créée (ID: {vente_id}) - Vous pouvez maintenant ajouter des articles")
                        st.rerun()
            else:
                # Une vente est déjà en cours - afficher les informations
                vente_info = pd.read_sql(
                    "SELECT * FROM ventes_headers WHERE id = ?", 
                    conn, params=(st.session_state.current_vente_id,)
                ).iloc[0]
                
                st.markdown("<div class='section-header'>📋 Vente en Cours</div>", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Client:** {vente_info['client']}")
                with col2:
                    st.write(f"**Téléphone:** {vente_info['telephone_client'] or 'Non renseigné'}")
                with col3:
                    st.write(f"**Ville:** {vente_info.get('ville') or 'Non renseignée'}")
                with col4:
                    st.write(f"**Date:** {parse_date_safe(vente_info['date'])}")
                
                # Bouton pour annuler et recommencer
                if st.button("🔄 Nouvelle Vente", type="secondary", key="btn_nouvelle_vente"):
                    del st.session_state.current_vente_id
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Étape 2 : Si une vente est en cours, ajouter des articles
            if 'current_vente_id' in st.session_state:
                ajouter_articles_vente_simplifie(conn, st.session_state.current_vente_id)

        with tab_ventes2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique des Ventes</div>", unsafe_allow_html=True)
                
                # Ajouter des sous-onglets pour différentes vues
                ventes_subtabs = st.tabs(["📋 Liste des Ventes", "🔍 Détail par Vente", "📊 Rapport par Produit", "📈 Analyses Produits"])
                
                with ventes_subtabs[0]:  # Liste des ventes existante
                    try:
                        ventes_headers = pd.read_sql(
                            """SELECT vh.*, COUNT(v.id) as nb_articles 
                               FROM ventes_headers vh 
                               LEFT JOIN ventes v ON vh.id = v.vente_header_id 
                               GROUP BY vh.id 
                               ORDER BY vh.date DESC""", 
                            conn
                        )
                        
                        if not ventes_headers.empty:
                            st.markdown("<div class='subsection-header'>🔍 Filtres de recherche</div>", unsafe_allow_html=True)
                            col_f1, col_f2 = st.columns(2)
                            with col_f1:
                                filter_name = st.text_input("👤 Filtrer par nom", placeholder="Nom du client...", key="filter_name_sales")
                            with col_f2:
                                filter_city = st.text_input("🏙️ Filtrer par ville", placeholder="Ville...", key="filter_city_sales")
                            
                            if filter_name:
                                ventes_headers = ventes_headers[ventes_headers['client'].str.contains(filter_name, case=False, na=False)]
                            if filter_city:
                                if 'ville' in ventes_headers.columns:
                                    ventes_headers = ventes_headers[ventes_headers['ville'].str.contains(filter_city, case=False, na=False)]

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                total_ventes = ventes_headers['total_mad'].sum()
                                display_metric_with_icon("💰", "Chiffre d'Affaires", f"{total_ventes:,.2f} MAD")
                            with col2:
                                nb_ventes = len(ventes_headers)
                                display_metric_with_icon("📦", "Nombre de Ventes", f"{nb_ventes}")
                            with col3:
                                avg_vente = total_ventes / nb_ventes if nb_ventes > 0 else 0
                                display_metric_with_icon("📊", "Moyenne par Vente", f"{avg_vente:,.2f} MAD")
                            
                            st.markdown("<div class='subsection-header'>📋 Liste des Ventes</div>", unsafe_allow_html=True)
                            
                            ventes_display = ventes_headers.copy()
                            # Sécurité si la colonne ville est manquante
                            if 'ville' not in ventes_display.columns:
                                ventes_display['ville'] = "N/A"
                                
                            ventes_display = ventes_display[['id', 'date', 'client', 'ville', 'telephone_client', 'nb_articles', 'total_mad']]
                            ventes_display.columns = ['ID', 'Date', 'Client', 'Ville', 'Téléphone', 'Nb Articles', 'Total MAD']
                            
                            st.dataframe(
                                ventes_display,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "ID": st.column_config.NumberColumn("ID", format="%d"),
                                    "Date": "Date",
                                    "Client": "Client",
                                    "Téléphone": "Téléphone",
                                    "Nb Articles": st.column_config.NumberColumn("Articles", format="%d"),
                                    "Total MAD": st.column_config.NumberColumn("Total (MAD)", format="%.2f MAD")
                                }
                            )

                            st.markdown("<div class='subsection-header'>⚡ Actions Rapides</div>", unsafe_allow_html=True)
                            selected_vente_quick = st.selectbox(
                                "Modifier rapidement une vente",
                                ventes_headers['id'].tolist(),
                                format_func=lambda x: f"Vente #{x} - {ventes_headers[ventes_headers['id'] == x].iloc[0]['client']} - {ventes_headers[ventes_headers['id'] == x].iloc[0]['date']}",
                                key="quick_edit_vente"
                            )
                            if st.button("✏️ Modifier cette vente", key="btn_quick_edit_vente"):
                                st.session_state.selected_vente_for_edit = selected_vente_quick
                                st.rerun()
                        
                        else:
                            st.info("📊 Aucune vente enregistrée")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement des ventes: {e}")
                
                with ventes_subtabs[1]:  # NOUVEAU : Détail par vente
                    st.markdown("<div class='subsection-header'>🔍 Détail des Ventes par Transaction</div>", unsafe_allow_html=True)
                    
                    try:
                        # Récupérer toutes les ventes pour la sélection
                        ventes_liste = pd.read_sql("""
                            SELECT 
                                vh.id,
                                vh.date,
                                vh.client,
                                vh.ville,
                                vh.telephone_client,
                                vh.total_mad,
                                COUNT(v.id) as nb_articles,
                                SUM(v.quantite) as total_quantite
                            FROM ventes_headers vh
                            LEFT JOIN ventes v ON vh.id = v.vente_header_id
                            GROUP BY vh.id
                            ORDER BY vh.date DESC
                        """, conn)
                        
                        if not ventes_liste.empty:
                            # Sélection de la vente à détailler
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                vente_selectionnee_id = st.selectbox(
                                    "Sélectionner une vente",
                                    ventes_liste['id'].tolist(),
                                    format_func=lambda x: f"Vente #{x} - {ventes_liste[ventes_liste['id'] == x].iloc[0]['client']} - {ventes_liste[ventes_liste['id'] == x].iloc[0]['date']} - {ventes_liste[ventes_liste['id'] == x].iloc[0]['total_mad']:.2f} MAD",
                                    key="select_vente_detail"
                                )
                            
                            if vente_selectionnee_id:
                                # Récupérer les informations de l'en-tête
                                vente_header = ventes_liste[ventes_liste['id'] == vente_selectionnee_id].iloc[0]
                                
                                # Afficher les informations générales
                                st.markdown(f"""
                                <div class='info-card'>
                                    <strong>Vente #{vente_selectionnee_id}</strong><br>
                                    <strong>Date :</strong> {parse_date_safe(vente_header['date'])}<br>
                                    <strong>Client :</strong> {vente_header['client']}<br>
                                    <strong>Ville :</strong> {vente_header.get('ville') or 'Non renseignée'}<br>
                                    <strong>Téléphone :</strong> {vente_header['telephone_client'] or 'Non renseigné'}<br>
                                    <strong>Total :</strong> {vente_header['total_mad']:.2f} MAD<br>
                                    <strong>Articles :</strong> {vente_header['nb_articles']} ({vente_header['total_quantite']} unités)
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Récupérer le détail des produits vendus
                                detail_vente = pd.read_sql("""
                                    SELECT 
                                        v.id as item_id,
                                        v.produit,
                                        v.quantite,
                                        v.prix_origine,
                                        v.devise_origine,
                                        v.prix_mad as prix_vente_mad,
                                        (v.quantite * v.prix_mad) as total_ligne_mad,
                                        v.achat_source_id,
                                        v.type_attribution,
                                        a.prix_mad as prix_achat_mad,
                                        a.id as achat_item_id,
                                        ah.fournisseur,
                                        ah.date as date_achat,
                                        CASE 
                                            WHEN v.achat_source_id IS NOT NULL THEN (v.prix_mad - a.prix_mad)
                                            ELSE NULL
                                        END as marge_unitaire,
                                        CASE 
                                            WHEN v.achat_source_id IS NOT NULL THEN ((v.prix_mad - a.prix_mad) * v.quantite)
                                            ELSE NULL
                                        END as marge_totale,
                                        CASE 
                                            WHEN v.achat_source_id IS NOT NULL AND a.prix_mad > 0 
                                            THEN ((v.prix_mad - a.prix_mad) / a.prix_mad * 100)
                                            ELSE NULL
                                        END as marge_pourcentage
                                    FROM ventes v
                                    LEFT JOIN achats a ON v.achat_source_id = a.id
                                    LEFT JOIN achats_headers ah ON a.achat_header_id = ah.id
                                    WHERE v.vente_header_id = ?
                                    ORDER BY v.produit
                                """, conn, params=(vente_selectionnee_id,))
                                
                                if not detail_vente.empty:
                                    # Métriques du détail
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("📦 Produits distincts", len(detail_vente))
                                    with col2:
                                        total_articles = detail_vente['quantite'].sum()
                                        st.metric("🔢 Total articles", f"{total_articles}")
                                    with col3:
                                        total_vente = detail_vente['total_ligne_mad'].sum()
                                        st.metric("💰 Total vente", f"{total_vente:,.2f} MAD")
                                    
                                    # Calcul des marges si disponibles
                                    ventes_avec_marge = detail_vente[detail_vente['marge_totale'].notna()]
                                    if not ventes_avec_marge.empty:
                                        total_marge = ventes_avec_marge['marge_totale'].sum()
                                        marge_moyenne = ventes_avec_marge['marge_pourcentage'].mean()
                                        with col4:
                                            st.metric("✅ Marge totale", f"{total_marge:,.2f} MAD")
                                        
                                        # Afficher la marge moyenne en dessous
                                        st.caption(f"📊 Marge moyenne: {marge_moyenne:.1f}%")
                                    else:
                                        with col4:
                                            st.metric("✅ Marge", "Non calculée")
                                    
                                    # Tableau détaillé des produits
                                    st.markdown("#### 📋 Détail des produits vendus")
                                    
                                    detail_display = detail_vente.copy()
                                    
                                    # Préparer les colonnes d'affichage
                                    display_cols = [
                                        'produit', 'quantite', 'prix_origine', 'devise_origine',
                                        'prix_vente_mad', 'total_ligne_mad'
                                    ]
                                    
                                    # Ajouter les colonnes de marge si disponibles
                                    if not ventes_avec_marge.empty:
                                        display_cols.extend(['fournisseur', 'prix_achat_mad', 'marge_unitaire', 'marge_totale', 'marge_pourcentage'])
                                    
                                    detail_display = detail_display[display_cols].copy()
                                    
                                    # Renommer les colonnes
                                    column_names = {
                                        'produit': 'Produit',
                                        'quantite': 'Quantité',
                                        'prix_origine': 'Prix unitaire',
                                        'devise_origine': 'Devise',
                                        'prix_vente_mad': 'Prix (MAD)',
                                        'total_ligne_mad': 'Total (MAD)',
                                        'fournisseur': 'Fournisseur source',
                                        'prix_achat_mad': 'Prix achat',
                                        'marge_unitaire': 'Marge unitaire',
                                        'marge_totale': 'Marge totale',
                                        'marge_pourcentage': 'Marge %'
                                    }
                                    
                                    detail_display = detail_display.rename(columns=column_names)
                                    
                                    st.dataframe(
                                        detail_display,
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    
                                    # Visualisations
                                    st.markdown("#### 📊 Analyses de la vente")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Répartition par produit (en valeur)
                                        fig_repartition = px.pie(
                                            detail_vente,
                                            values='total_ligne_mad',
                                            names='produit',
                                            title="Répartition du montant par produit"
                                        )
                                        fig_repartition.update_traces(textposition='inside', textinfo='percent+label')
                                        fig_repartition.update_layout(height=300)
                                        st.plotly_chart(fig_repartition, use_container_width=True)
                                    
                                    with col2:
                                        # Répartition par produit (en quantité)
                                        fig_quantite = px.bar(
                                            detail_vente,
                                            x='produit',
                                            y='quantite',
                                            title="Quantités vendues par produit",
                                            labels={'produit': 'Produit', 'quantite': 'Quantité'}
                                        )
                                        fig_quantite.update_layout(height=300, xaxis_tickangle=-45)
                                        st.plotly_chart(fig_quantite, use_container_width=True)
                                    
                                    # Analyse des sources d'approvisionnement
                                    if not ventes_avec_marge.empty:
                                        st.markdown("#### 🔗 Sources d'approvisionnement")
                                        
                                        sources_stats = detail_vente[detail_vente['fournisseur'].notna()].groupby('fournisseur').agg({
                                            'quantite': 'sum',
                                            'marge_totale': 'sum',
                                            'produit': 'count'
                                        }).reset_index()
                                        
                                        sources_stats.columns = ['Fournisseur', 'Quantité', 'Marge totale', 'Nb produits']
                                        
                                        st.dataframe(
                                            sources_stats,
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                    
                                    # Actions sur la vente
                                    st.markdown("#### ⚙️ Actions")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button("📝 Modifier cette vente", use_container_width=True):
                                            st.session_state.selected_vente_for_edit = vente_selectionnee_id
                                            st.switch_page("📦 Ventes")  # Ou utiliser st.rerun() et navigation
                                            st.rerun()
                                    with col2:
                                        if st.button("🖨️ Aperçu ticket", use_container_width=True):
                                            generer_apercu_ticket_avance(conn, vente_selectionnee_id)
                                    with col3:
                                        if st.button("❌ Annuler la vente", use_container_width=True, type="secondary"):
                                            if st.checkbox("Confirmer l'annulation de cette vente ?"):
                                                supprimer_vente_header(conn, vente_selectionnee_id)
                                                display_success_message("Vente annulée avec succès!")
                                                st.rerun()
                                
                                else:
                                    st.warning("Aucun détail trouvé pour cette vente")
                        
                        else:
                            st.info("📊 Aucune vente disponible")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement du détail: {e}")
                
                with ventes_subtabs[2]:  # Rapport par produit (existant)
                    # ... (code existant du rapport par produit)
                    st.markdown("<div class='subsection-header'>📊 Rapport Détail des Ventes par Produit</div>", unsafe_allow_html=True)
                    
                    # Récupérer la liste des produits vendus
                    produits_stats = get_produits_vendus(conn)
                    
                    if not produits_stats.empty:
                        # Métriques globales
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            nb_produits_distincts = len(produits_stats)
                            display_metric_with_icon("📦", "Produits distincts", f"{nb_produits_distincts}")
                        with col2:
                            total_quantite = produits_stats['quantite_totale_vendue'].sum()
                            display_metric_with_icon("🔢", "Quantité totale vendue", f"{total_quantite:,.0f}")
                        with col3:
                            ca_total = produits_stats['chiffre_affaires_mad'].sum()
                            display_metric_with_icon("💰", "CA Total", f"{ca_total:,.2f} MAD")
                        with col4:
                            ca_moyen = ca_total / nb_produits_distincts if nb_produits_distincts > 0 else 0
                            display_metric_with_icon("📊", "CA moyen par produit", f"{ca_moyen:,.2f} MAD")
                        
                        # Sélection du produit
                        st.markdown("<div class='subsection-header'>🔍 Filtrer par produit</div>", unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            produit_selectionne = st.selectbox(
                                "Sélectionner un produit",
                                ["Tous les produits"] + produits_stats['produit'].tolist(),
                                key="select_produit_rapport"
                            )
                        with col2:
                            date_debut_rapport = st.date_input(
                                "Date début",
                                value=date.today() - timedelta(days=365),
                                key="date_debut_rapport"
                            )
                        with col3:
                            date_fin_rapport = st.date_input(
                                "Date fin",
                                value=date.today(),
                                key="date_fin_rapport"
                            )
                        
                        # Récupérer les ventes détaillées
                        produit_filtre = None if produit_selectionne == "Tous les produits" else produit_selectionne
                        ventes_detail = get_ventes_par_produit(
                            conn, 
                            produit=produit_filtre,
                            date_debut=date_debut_rapport.isoformat(),
                            date_fin=date_fin_rapport.isoformat()
                        )
                        
                        if not ventes_detail.empty:
                            # Statistiques du produit sélectionné
                            if produit_filtre:
                                st.markdown(f"<div class='subsection-header'>📋 Détail des ventes - {produit_filtre}</div>", unsafe_allow_html=True)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    nb_ventes_produit = ventes_detail['vente_header_id'].nunique()
                                    st.metric("📊 Nombre de ventes", f"{nb_ventes_produit}")
                                with col2:
                                    quantite_produit = ventes_detail['quantite'].sum()
                                    st.metric("🔢 Quantité vendue", f"{quantite_produit}")
                                with col3:
                                    ca_produit = ventes_detail['total_vente_mad'].sum()
                                    st.metric("💰 Chiffre d'affaires", f"{ca_produit:,.2f} MAD")
                                
                                # Calcul des marges si disponibles
                                ventes_avec_marge = ventes_detail[ventes_detail['marge_mad'].notna()]
                                if not ventes_avec_marge.empty:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        marge_totale = ventes_avec_marge['marge_mad'].sum()
                                        st.metric("✅ Marge totale", f"{marge_totale:,.2f} MAD")
                                    with col2:
                                        marge_moyenne = ventes_avec_marge['marge_pourcentage'].mean()
                                        st.metric("📊 Marge moyenne", f"{marge_moyenne:.1f}%")
                                    with col3:
                                        prix_achat_moyen = ventes_avec_marge['prix_achat_mad'].mean()
                                        st.metric("💰 Prix achat moyen", f"{prix_achat_moyen:,.2f} MAD")
                            
                            # Tableau détaillé
                            st.markdown("<div class='subsection-header'>📋 Détail des ventes</div>", unsafe_allow_html=True)
                            
                            # Préparer l'affichage
                            display_cols = [
                                'date_vente', 'client', 'produit', 'quantite', 
                                'prix_origine', 'devise_origine', 'prix_vente_mad', 'total_vente_mad'
                            ]
                            
                            # Ajouter les colonnes de marge si disponibles
                            if not ventes_detail[ventes_detail['marge_mad'].notna()].empty:
                                display_cols.extend(['fournisseur', 'prix_achat_mad', 'total_achat_mad', 'marge_mad', 'marge_pourcentage'])
                            
                            df_display = ventes_detail[display_cols].copy()
                            
                            # Renommer les colonnes pour l'affichage
                            column_names = {
                                'date_vente': 'Date',
                                'client': 'Client',
                                'produit': 'Produit',
                                'quantite': 'Qté',
                                'prix_origine': 'Prix unitaire',
                                'devise_origine': 'Devise',
                                'prix_vente_mad': 'Prix MAD',
                                'total_vente_mad': 'Total MAD',
                                'fournisseur': 'Fournisseur',
                                'prix_achat_mad': 'Prix achat MAD',
                                'total_achat_mad': 'Total achat',
                                'marge_mad': 'Marge MAD',
                                'marge_pourcentage': 'Marge %'
                            }
                            
                            df_display = df_display.rename(columns=column_names)
                            
                            # Arrondir les valeurs numériques
                            for col in ['Prix MAD', 'Total MAD', 'Prix achat MAD', 'Total achat', 'Marge MAD']:
                                if col in df_display.columns:
                                    df_display[col] = df_display[col].round(2)
                            
                            if 'Marge %' in df_display.columns:
                                df_display['Marge %'] = df_display['Marge %'].round(1)
                            
                            st.dataframe(
                                df_display,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Résumé et visualisations
                            st.markdown("<div class='subsection-header'>📊 Analyses</div>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Évolution des ventes du produit dans le temps
                                ventes_detail['date_vente'] = pd.to_datetime(ventes_detail['date_vente'])
                                evolution = ventes_detail.groupby(
                                    [ventes_detail['date_vente'].dt.to_period('M'), 'produit']
                                )['total_vente_mad'].sum().reset_index()
                                evolution['date_vente'] = evolution['date_vente'].dt.to_timestamp()
                                
                                fig_evolution = px.line(
                                    evolution,
                                    x='date_vente',
                                    y='total_vente_mad',
                                    color='produit' if produit_filtre is None else None,
                                    title="Évolution du chiffre d'affaires",
                                    labels={'date_vente': 'Mois', 'total_vente_mad': 'CA (MAD)'}
                                )
                                fig_evolution.update_layout(height=300)
                                st.plotly_chart(fig_evolution, use_container_width=True)
                            
                            with col2:
                                # Répartition par client
                                if produit_filtre:
                                    top_clients = ventes_detail.groupby('client')['total_vente_mad'].sum().nlargest(10)
                                    fig_clients = px.bar(
                                        x=top_clients.values,
                                        y=top_clients.index,
                                        orientation='h',
                                        title=f"Top 10 clients - {produit_filtre}",
                                        labels={'x': 'CA (MAD)', 'y': 'Client'}
                                    )
                                    fig_clients.update_layout(height=300)
                                    st.plotly_chart(fig_clients, use_container_width=True)
                                else:
                                    # Répartition par produit
                                    repartition_produits = ventes_detail.groupby('produit')['total_vente_mad'].sum().nlargest(10)
                                    fig_produits = px.pie(
                                        values=repartition_produits.values,
                                        names=repartition_produits.index,
                                        title="Top 10 produits par CA"
                                    )
                                    st.plotly_chart(fig_produits, use_container_width=True)
                        
                        else:
                            st.info(f"📊 Aucune vente trouvée pour {produit_filtre if produit_filtre else 'les produits sélectionnés'} sur cette période")
                    
                    else:
                        st.info("📊 Aucun produit vendu pour le moment")
                
                with ventes_subtabs[3]:  # Analyses Produits (existant)
                    st.markdown("<div class='subsection-header'>📈 Analyses et Comparaisons Produits</div>", unsafe_allow_html=True)
                    
                    produits_stats = get_produits_vendus(conn)
                    
                    if not produits_stats.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Top produits par CA
                            top_ca = produits_stats.nlargest(10, 'chiffre_affaires_mad')
                            fig_top_ca = px.bar(
                                top_ca,
                                x='produit',
                                y='chiffre_affaires_mad',
                                title="Top 10 produits par chiffre d'affaires",
                                labels={'produit': 'Produit', 'chiffre_affaires_mad': 'CA (MAD)'}
                            )
                            fig_top_ca.update_layout(height=350, xaxis_tickangle=-45)
                            st.plotly_chart(fig_top_ca, use_container_width=True)
                        
                        with col2:
                            # Top produits par quantité
                            top_quantite = produits_stats.nlargest(10, 'quantite_totale_vendue')
                            fig_top_qte = px.bar(
                                top_quantite,
                                x='produit',
                                y='quantite_totale_vendue',
                                title="Top 10 produits par quantité vendue",
                                labels={'produit': 'Produit', 'quantite_totale_vendue': 'Quantité'}
                            )
                            fig_top_qte.update_layout(height=350, xaxis_tickangle=-45)
                            st.plotly_chart(fig_top_qte, use_container_width=True)
                        
                        # Matrice CA/Quantité
                        fig_scatter = px.scatter(
                            produits_stats,
                            x='quantite_totale_vendue',
                            y='chiffre_affaires_mad',
                            size='nb_ventes',
                            hover_name='produit',
                            text='produit',
                            title="Matrice Produits : Quantité vs Chiffre d'affaires",
                            labels={
                                'quantite_totale_vendue': 'Quantité totale vendue',
                                'chiffre_affaires_mad': "Chiffre d'affaires (MAD)",
                                'nb_ventes': 'Nombre de ventes'
                            }
                        )
                        fig_scatter.update_traces(textposition='top center')
                        fig_scatter.update_layout(height=400)
                        st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Tableau comparatif des produits
                        st.markdown("<div class='subsection-header'>📋 Comparatif Produits</div>", unsafe_allow_html=True)
                        
                        produits_display = produits_stats.copy()
                        produits_display = produits_display[[
                            'produit', 'nb_ventes', 'quantite_totale_vendue', 
                            'chiffre_affaires_mad', 'prix_vente_moyen', 
                            'premiere_vente', 'derniere_vente'
                        ]]
                        produits_display.columns = [
                            'Produit', 'Nb ventes', 'Quantité totale', 
                            'CA (MAD)', 'Prix moyen (MAD)', 
                            'Première vente', 'Dernière vente'
                        ]
                        
                        # Formater les colonnes numériques
                        produits_display['CA (MAD)'] = produits_display['CA (MAD)'].round(2)
                        produits_display['Prix moyen (MAD)'] = produits_display['Prix moyen (MAD)'].round(2)
                        
                        st.dataframe(
                            produits_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Produit": "Produit",
                                "Nb ventes": st.column_config.NumberColumn("Ventes", format="%d"),
                                "Quantité totale": st.column_config.NumberColumn("Quantité", format="%d"),
                                "CA (MAD)": st.column_config.NumberColumn("CA", format="%.2f MAD"),
                                "Prix moyen (MAD)": st.column_config.NumberColumn("Prix moyen", format="%.2f MAD"),
                                "Première vente": "Première vente",
                                "Dernière vente": "Dernière vente"
                            }
                        )
                        
                    else:
                        st.info("📊 Aucune donnée produit disponible pour l'analyse")
                
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_ventes3:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Modifier une Vente</div>", unsafe_allow_html=True)
                
                try:
                    ventes_headers = pd.read_sql("SELECT * FROM ventes_headers ORDER BY date DESC", conn)
                    
                    if not ventes_headers.empty:
                        selected_vente_id = st.selectbox(
                            "Sélectionner une vente à modifier",
                            ventes_headers['id'].tolist(),
                            format_func=lambda x: f"Vente #{x} - {ventes_headers[ventes_headers['id'] == x].iloc[0]['client']} - {ventes_headers[ventes_headers['id'] == x].iloc[0]['date']}",
                            key="select_vente_modify"
                        )
                        
                        if selected_vente_id:
                            vente_data = ventes_headers[ventes_headers['id'] == selected_vente_id].iloc[0]
                            articles_vente = pd.read_sql(
                                "SELECT * FROM ventes WHERE vente_header_id = ?", 
                                conn, params=(selected_vente_id,)
                            )
                            
                            with st.form("form_modify_vente_header"):
                                st.markdown("### Modifier l'en-tête de la vente")
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_date = st.date_input("📅 Date", value=datetime.strptime(vente_data['date'], '%Y-%m-%d').date())
                                    new_client = st.text_input("👤 Client", value=vente_data['client'])
                                with col2:
                                    new_telephone = st.text_input("📞 Téléphone", value=vente_data['telephone_client'] or "")
                                    new_ville = st.text_input("🏙️ Ville", value=vente_data.get('ville') or "", key=f"edit_ville_{selected_vente_id}")
                                
                                if st.form_submit_button("💾 Mettre à jour l'en-tête"):
                                    modifier_vente_header(conn, selected_vente_id, new_date.isoformat(), new_client, new_telephone, new_ville)
                                    display_success_message("En-tête de vente mis à jour")
                                    st.rerun()
                            
                            st.markdown("### Modifier les articles")
                            
                            if not articles_vente.empty:
                                st.markdown("#### Articles existants")
                                for index, article in articles_vente.iterrows():
                                    with st.form(f"form_modify_article_{article['id']}"):
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            new_produit = st.text_input("📦 Produit", value=article['produit'], key=f"prod_{article['id']}")
                                            new_quantite = st.number_input("🔢 Quantité", min_value=1, value=article['quantite'], key=f"qte_{article['id']}")
                                        with col2:
                                            new_prix = st.number_input("💰 Prix", min_value=0.0, value=float(article['prix_origine']), key=f"prix_{article['id']}")
                                            new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, 
                                                                    index=SUPPORTED_DEVISES.index(article['devise_origine']), 
                                                                    key=f"dev_{article['id']}")
                                        with col3:
                                            st.write("")
                                            if st.form_submit_button("✏️ Mettre à jour l'article", use_container_width=True):
                                                new_prix_mad = convertir_en_mad(new_prix, new_devise, conn)
                                                modifier_vente_item(conn, article['id'], new_produit, new_quantite, new_prix, new_devise, new_prix_mad)
                                                display_success_message("Article mis à jour")
                                                st.rerun()
                                            if st.form_submit_button("❌ Supprimer", use_container_width=True):
                                                supprimer_vente_item(conn, article['id'])
                                                display_success_message("Article supprimé avec succès!")
                                                st.rerun()
                            
                            st.markdown("### 🔗 Attribution des Articles aux Achats")
                            
                            if not articles_vente.empty:
                                for index, article in articles_vente.iterrows():
                                    with st.expander(f"Article: {article['produit']} - {article['quantite']} unités", expanded=False):
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            statut_actuel = "Non attribué"
                                            if article['achat_source_id'] is not None:
                                                statut_actuel = f"Attribué à l'achat #{article['achat_source_id']}"
                                            elif article.get('type_attribution') == 'autre':
                                                statut_actuel = "Marqué comme 'Autre'"
                                            
                                            st.write(f"**Statut actuel :** {statut_actuel}")
                                            st.write(f"**Produit :** {article['produit']}")
                                            st.write(f"**Quantité vendue :** {article['quantite']}")
                                        
                                        with col2:
                                            achats_disponibles = pd.read_sql("""
                                                SELECT * FROM (
                                                    SELECT 
                                                        a.id as achat_item_id, 
                                                        a.produit, 
                                                        a.quantite as quantite_achetee,
                                                        ah.date as date_achat, 
                                                        ah.fournisseur,
                                                        (a.quantite - COALESCE((
                                                            SELECT SUM(v2.quantite) 
                                                            FROM ventes v2 
                                                            WHERE v2.achat_source_id = a.id
                                                        ), 0)) as quantite_restante
                                                    FROM achats a
                                                    JOIN achats_headers ah ON a.achat_header_id = ah.id
                                                ) 
                                                WHERE quantite_restante > 0 AND produit = ?
                                                ORDER BY date_achat
                                            """, conn, params=(article['produit'],))
                                            
                                            if not achats_disponibles.empty:
                                                options_attribution = []
                                                
                                                for _, achat in achats_disponibles.iterrows():
                                                    options_attribution.append({
                                                        'id': achat['achat_item_id'],
                                                        'label': f"Achat #{achat['achat_item_id']} - {achat['fournisseur']} - Reste: {achat['quantite_restante']}",
                                                        'type': 'achat'
                                                    })
                                                
                                                options_attribution.append({
                                                    'id': -1,
                                                    'label': "🔄 Autre (stock initial)",
                                                    'type': 'autre'
                                                })
                                                
                                                options_attribution.append({
                                                    'id': -2,
                                                    'label': "❌ Aucune attribution",
                                                    'type': 'aucun'
                                                })
                                                
                                                default_index = len(options_attribution) - 1
                                                if article['achat_source_id'] is not None:
                                                    for i, opt in enumerate(options_attribution):
                                                        if opt['type'] == 'achat' and opt['id'] == article['achat_source_id']:
                                                            default_index = i
                                                            break
                                                elif article.get('type_attribution') == 'autre':
                                                    default_index = len(options_attribution) - 2
                                                
                                                attribution_selectionnee = st.selectbox(
                                                    "Attribuer à :",
                                                    options_attribution,
                                                    index=default_index,
                                                    format_func=lambda x: x['label'],
                                                    key=f"attribution_modify_{article['id']}"
                                                )
                                                
                                                if st.button("💾 Mettre à jour l'attribution", 
                                                           key=f"btn_attribution_{article['id']}",
                                                           use_container_width=True):
                                                    with conn:
                                                        if attribution_selectionnee['type'] == 'achat':
                                                            conn.execute(
                                                                "UPDATE ventes SET achat_source_id = ?, type_attribution = 'manuel' WHERE id = ?",
                                                                (attribution_selectionnee['id'], article['id'])
                                                            )
                                                            display_success_message(f"Article attribué à l'achat #{attribution_selectionnee['id']}")
                                                        elif attribution_selectionnee['type'] == 'autre':
                                                            conn.execute(
                                                                "UPDATE ventes SET achat_source_id = NULL, type_attribution = 'autre' WHERE id = ?",
                                                                (article['id'],)
                                                            )
                                                            display_success_message("Article marqué comme 'Autre'")
                                                        else:
                                                            conn.execute(
                                                                "UPDATE ventes SET achat_source_id = NULL, type_attribution = NULL WHERE id = ?",
                                                                (article['id'],)
                                                            )
                                                            display_success_message("Attribution supprimée")
                                                    st.rerun()
                                                
                                            else:
                                                st.info("Aucun achat disponible pour ce produit")
                                                if st.button("🔄 Marquer comme 'Autre'", 
                                                           key=f"btn_autre_{article['id']}",
                                                           use_container_width=True):
                                                    with conn:
                                                        conn.execute(
                                                            "UPDATE ventes SET achat_source_id = NULL, type_attribution = 'autre' WHERE id = ?",
                                                            (article['id'],)
                                                        )
                                                    display_success_message("Article marqué comme 'Autre'")
                                                    st.rerun()

                            st.markdown("#### ➕ Ajouter un nouvel article")
                            with st.form("form_add_article_vente"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    new_produit = st.text_input("📦 Nouveau produit", placeholder="Nom du produit", key=f"new_prod_vente_{selected_vente_id}")
                                    new_quantite = st.number_input("🔢 Quantité", min_value=1, value=1, key=f"new_qte_vente_{selected_vente_id}")
                                with col2:
                                    new_prix = st.number_input("💰 Prix unitaire", min_value=0.0, value=0.0, step=0.01, key=f"new_prix_vente_{selected_vente_id}")
                                    new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, key=f"new_dev_vente_{selected_vente_id}")
                                with col3:
                                    st.write("")
                                    if st.form_submit_button("➕ Ajouter l'article à la vente"):
                                        if not new_produit.strip():
                                            display_warning_message("Veuillez saisir un produit")
                                        else:
                                            try:
                                                new_prix_mad = convertir_en_mad(new_prix, new_devise, conn)
                                                ajouter_article_vente_existante(conn, selected_vente_id, new_produit.strip(), 
                                                                              new_quantite, new_prix, new_devise, new_prix_mad)
                                                display_success_message(f"Nouvel article ajouté: {new_quantite} × {new_produit}")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Erreur lors de l'ajout: {e}")

                            st.markdown("### Supprimer la vente")
                            if st.button("🗑️ Supprimer cette vente", type="secondary"):
                                supprimer_vente_header(conn, selected_vente_id)
                                display_success_message("Vente supprimée")
                                st.rerun()
                    
                    else:
                        st.info("📊 Aucune vente à modifier")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la modification: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_ventes4:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>🔗 Gestion des Attributions Ventes-Achats</div>", unsafe_allow_html=True)
                
                subtab1, subtab2, subtab3 = st.tabs(["📊 Récapitulatif Complet", "🎯 Attribution Manuelle", "✅ Ventes Attribuées"])
                
                with subtab1:
                    st.markdown("<div class='subsection-header'>📊 Récapitulatif Global des Attributions</div>", unsafe_allow_html=True)
                    
                    try:
                        recap_complet = pd.read_sql("""
                            SELECT 
                                vh.id as vente_id,
                                vh.date as date_vente,
                                vh.client,
                                v.id as item_id,
                                v.produit,
                                v.quantite,
                                v.prix_mad,
                                (v.quantite * v.prix_mad) as total_mad,
                                CASE 
                                    WHEN v.achat_source_id IS NOT NULL THEN CONCAT('✅ Achat #', v.achat_source_id)
                                    WHEN v.type_attribution = 'autre' THEN '🔄 Autre'
                                    ELSE '❌ Non attribué'
                                END as statut_attribution,
                                a2.fournisseur,
                                a2.date as date_achat,
                                v.type_attribution
                            FROM ventes v
                            JOIN ventes_headers vh ON v.vente_header_id = vh.id
                            LEFT JOIN achats a ON v.achat_source_id = a.id
                            LEFT JOIN achats_headers a2 ON a.achat_header_id = a2.id
                            ORDER BY vh.date DESC, v.id
                        """, conn)
                        
                        if not recap_complet.empty:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                filtre_statut = st.selectbox(
                                    "Filtrer par statut",
                                    ["Tous", "✅ Attribués", "🔄 Autre", "❌ Non attribués"],
                                    key="filtre_recap"
                                )
                            with col2:
                                filtre_produit = st.text_input("Filtrer par produit", placeholder="Nom du produit...")
                            with col3:
                                filtre_client = st.text_input("Filtrer par client", placeholder="Nom du client...")
                            
                            recap_filtre = recap_complet.copy()
                            if filtre_statut != "Tous":
                                recap_filtre = recap_filtre[recap_filtre['statut_attribution'] == filtre_statut]
                            if filtre_produit:
                                recap_filtre = recap_filtre[recap_filtre['produit'].str.contains(filtre_produit, case=False, na=False)]
                            if filtre_client:
                                recap_filtre = recap_filtre[recap_filtre['client'].str.contains(filtre_client, case=False, na=False)]
                            
                            st.markdown("#### 📈 Métriques Globales")
                            
                            total_ventes = len(recap_complet)
                            total_attribues = len(recap_complet[recap_complet['statut_attribution'].str.startswith('✅')])
                            total_autre = len(recap_complet[recap_complet['statut_attribution'] == '🔄 Autre'])
                            total_non_attribues = len(recap_complet[recap_complet['statut_attribution'] == '❌ Non attribué'])
                            taux_attribution = ((total_attribues + total_autre) / total_ventes * 100) if total_ventes > 0 else 0
                            valeur_totale = recap_complet['total_mad'].sum()
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                st.metric("📦 Total Articles", total_ventes)
                            with col2:
                                st.metric("✅ Attribués", f"{total_attribues} ({total_attribues/total_ventes*100:.0f}%)")
                            with col3:
                                st.metric("🔄 Autre", f"{total_autre} ({total_autre/total_ventes*100:.0f}%)")
                            with col4:
                                st.metric("❌ Non attribués", f"{total_non_attribues} ({total_non_attribues/total_ventes*100:.0f}%)")
                            with col5:
                                st.metric("📊 Taux Attribution", f"{taux_attribution:.0f}%")
                            
                            st.markdown("#### 📋 Détail des Attributions")
                            
                            recap_display = recap_filtre[['vente_id', 'date_vente', 'client', 'produit', 'quantite', 'total_mad', 'statut_attribution', 'fournisseur', 'date_achat']]
                            recap_display.columns = ['ID Vente', 'Date Vente', 'Client', 'Produit', 'Quantité', 'Total MAD', 'Statut', 'Fournisseur', 'Date Achat']
                            
                            st.dataframe(
                                recap_display,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "ID Vente": st.column_config.NumberColumn("Vente", format="%d"),
                                    "Date Vente": "Date Vente",
                                    "Client": "Client",
                                    "Produit": "Produit",
                                    "Quantité": st.column_config.NumberColumn("Qté", format="%d"),
                                    "Total MAD": st.column_config.NumberColumn("Total", format="%.2f MAD"),
                                    "Statut": "Statut",
                                    "Fournisseur": "Fournisseur",
                                    "Date Achat": "Date Achat"
                                }
                            )
                            
                            st.markdown("#### 📊 Visualisations")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                statuts_counts = recap_complet['statut_attribution'].value_counts()
                                fig_statuts = px.pie(
                                    values=statuts_counts.values,
                                    names=statuts_counts.index,
                                    title="Répartition des Statuts d'Attribution",
                                    color=statuts_counts.index,
                                    color_discrete_map={
                                        '✅ Achat': '#2ecc71',
                                        '🔄 Autre': '#f39c12', 
                                        '❌ Non attribué': '#e74c3c'
                                    }
                                )
                                st.plotly_chart(fig_statuts, use_container_width=True)
                            
                            with col2:
                                recap_complet['date_vente'] = pd.to_datetime(recap_complet['date_vente'])
                                evolution = recap_complet.groupby([recap_complet['date_vente'].dt.to_period('M'), 'statut_attribution']).size().reset_index()
                                evolution['date_vente'] = evolution['date_vente'].dt.to_timestamp()
                                
                                fig_evolution = px.line(
                                    evolution,
                                    x='date_vente',
                                    y=0,
                                    color='statut_attribution',
                                    title="Évolution des Attributions dans le Temps",
                                    labels={'date_vente': 'Mois', '0': "Nombre d'articles"}
                                )
                                st.plotly_chart(fig_evolution, use_container_width=True)
                            
                        else:
                            st.info("📊 Aucune donnée d'attribution disponible")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement du récapitulatif: {e}")
                
                with subtab2:
                    st.markdown("<div class='subsection-header'>🎯 Attribution Manuelle des Ventes Non Attribuées</div>", unsafe_allow_html=True)
                    
                    try:
                        ventes_non_attribuees = pd.read_sql("""
                            SELECT v.*, vh.date as date_vente, vh.client
                            FROM ventes v
                            JOIN ventes_headers vh ON v.vente_header_id = vh.id
                            WHERE v.achat_source_id IS NULL AND v.type_attribution IS NULL
                            ORDER BY vh.date DESC
                        """, conn)
                        
                        if not ventes_non_attribuees.empty:
                            st.write(f"**{len(ventes_non_attribuees)} ventes non attribuées trouvées**")
                            
                            for index, vente in ventes_non_attribuees.iterrows():
                                with st.expander(f"Vente #{vente['id']} - {vente['client']} - {vente['produit']} ({vente['quantite']} unités)", expanded=False):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.write(f"**Date :** {vente['date_vente']}")
                                        st.write(f"**Produit :** {vente['produit']}")
                                        st.write(f"**Quantité :** {vente['quantite']}")
                                        st.write(f"**Prix :** {vente['prix_mad']:.2f} MAD")
                                    
                                    with col2:
                                        achats_disponibles = pd.read_sql("""
                                            SELECT * FROM (
                                                SELECT 
                                                    a.id as achat_item_id, 
                                                    a.produit, 
                                                    a.quantite as quantite_achetee,
                                                    ah.date as date_achat, 
                                                    ah.fournisseur,
                                                    (a.quantite - COALESCE((
                                                        SELECT SUM(v2.quantite) 
                                                        FROM ventes v2 
                                                        WHERE v2.achat_source_id = a.id
                                                    ), 0)) as quantite_restante
                                                FROM achats a
                                                JOIN achats_headers ah ON a.achat_header_id = ah.id
                                            ) 
                                            WHERE quantite_restante > 0 AND produit = ?
                                            ORDER BY date_achat
                                        """, conn, params=(vente['produit'],))
                                        
                                        if not achats_disponibles.empty:
                                            options_attribution = []
                                            
                                            for _, achat in achats_disponibles.iterrows():
                                                options_attribution.append({
                                                    'id': achat['achat_item_id'],
                                                    'label': f"Achat #{achat['achat_item_id']} - {achat['fournisseur']} - Reste: {achat['quantite_restante']}",
                                                    'type': 'achat'
                                                })
                                            
                                            options_attribution.append({
                                                'id': -1,
                                                'label': "🔄 Autre (stock initial)",
                                                'type': 'autre'
                                            })
                                            
                                            attribution_selectionnee = st.selectbox(
                                                "Attribuer à :",
                                                options_attribution,
                                                format_func=lambda x: x['label'],
                                                key=f"attribution_manual_{vente['id']}"
                                            )
                                            
                                            if st.button("💾 Appliquer l'attribution", 
                                                       key=f"btn_apply_attribution_{vente['id']}",
                                                       use_container_width=True):
                                                with conn:
                                                    if attribution_selectionnee['type'] == 'achat':
                                                        conn.execute(
                                                            "UPDATE ventes SET achat_source_id = ?, type_attribution = 'manuel' WHERE id = ?",
                                                            (attribution_selectionnee['id'], vente['id'])
                                                        )
                                                        display_success_message(f"Vente #{vente['id']} attribuée à l'achat #{attribution_selectionnee['id']}")
                                                    else:
                                                        conn.execute(
                                                            "UPDATE ventes SET achat_source_id = NULL, type_attribution = 'autre' WHERE id = ?",
                                                            (vente['id'],)
                                                        )
                                                        display_success_message(f"Vente #{vente['id']} marquée comme 'Autre'")
                                                st.rerun()
                                            
                                        else:
                                            st.info("Aucun achat disponible pour ce produit")
                                            if st.button("🔄 Marquer comme 'Autre'", 
                                                       key=f"btn_autre_manual_{vente['id']}",
                                                       use_container_width=True):
                                                with conn:
                                                    conn.execute(
                                                        "UPDATE ventes SET achat_source_id = NULL, type_attribution = 'autre' WHERE id = ?",
                                                        (vente['id'],)
                                                    )
                                                display_success_message(f"Vente #{vente['id']} marquée comme 'Autre'")
                                                st.rerun()
                        else:
                            st.success("🎉 Toutes les ventes sont attribuées !")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement des ventes non attribuées: {e}")
                
                with subtab3:
                    st.markdown("<div class='subsection-header'>✅ Ventes Déjà Attribuées</div>", unsafe_allow_html=True)
                    
                    try:
                        ventes_attribuees = pd.read_sql("""
                            SELECT 
                                v.*, 
                                vh.date as date_vente, 
                                vh.client,
                                a2.fournisseur,
                                a2.date as date_achat,
                                CASE 
                                    WHEN v.achat_source_id IS NOT NULL THEN CONCAT('✅ Achat #', v.achat_source_id)
                                    ELSE '🔄 Autre'
                                END as statut_attribution
                            FROM ventes v
                            JOIN ventes_headers vh ON v.vente_header_id = vh.id
                            LEFT JOIN achats a ON v.achat_source_id = a.id
                            LEFT JOIN achats_headers a2 ON a.achat_header_id = a2.id
                            WHERE v.achat_source_id IS NOT NULL OR v.type_attribution = 'autre'
                            ORDER BY vh.date DESC
                        """, conn)
                        
                        if not ventes_attribuees.empty:
                            st.write(f"**{len(ventes_attribuees)} ventes attribuées trouvées**")
                            
                            for index, vente in ventes_attribuees.iterrows():
                                with st.expander(f"{vente['statut_attribution']} - {vente['client']} - {vente['produit']}", expanded=False):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.write(f"**Date vente :** {vente['date_vente']}")
                                        st.write(f"**Produit :** {vente['produit']}")
                                        st.write(f"**Quantité :** {vente['quantite']}")
                                        st.write(f"**Prix :** {vente['prix_mad']:.2f} MAD")
                                        
                                        if vente['achat_source_id'] is not None:
                                            st.write(f"**Achat source :** #{vente['achat_source_id']}")
                                            st.write(f"**Fournisseur :** {vente['fournisseur']}")
                                            st.write(f"**Date achat :** {vente['date_achat']}")
                                        else:
                                            st.write("**Source :** 🔄 Autre (stock initial ou source externe)")
                                    
                                    with col2:
                                        if st.button("🗑️ Supprimer l'attribution", 
                                                   key=f"btn_remove_attribution_{vente['id']}",
                                                   use_container_width=True):
                                            with conn:
                                                conn.execute(
                                                    "UPDATE ventes SET achat_source_id = NULL, type_attribution = NULL WHERE id = ?",
                                                    (vente['id'],)
                                                )
                                            display_success_message("Attribution supprimée")
                                            st.rerun()
                        else:
                            st.info("📊 Aucune vente attribuée trouvée")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement des ventes attribuées: {e}")
                
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "🛒 Achats":
        display_view_header("Gestion des Achats", "Suivez vos achats et votre stock", "🛒")
        
        tab_achats1, tab_achats2, tab_achats3, tab_achats4 = st.tabs(["➕ Nouvel Achat", "🗂️ Historique & Gestion", "✏️ Modifier Achat", "📈 Analyse Produits"])
        
        with tab_achats1:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Créer un Nouvel Achat</div>", unsafe_allow_html=True)
                
                with st.form("form_achat_header", clear_on_submit=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        date_op = st.date_input("📅 Date de l'achat", value=date.today(), key="achat_date")
                        fournisseur = st.text_input("🏢 Fournisseur", placeholder="Nom du fournisseur", key="achat_fournisseur")
                    with col2:
                        type_achat = st.selectbox("📋 Type", ["achat", "stock"], 
                                                 help="'achat': achat avec l'argent des ventes, 'stock': stock initial")
                    
                    submitted_header = st.form_submit_button("📋 Créer la fiche d'achat", use_container_width=True)
                
                if submitted_header:
                    if not fournisseur.strip():
                        display_warning_message("Veuillez saisir le nom du fournisseur")
                    else:
                        try:
                            achat_header_id = insert_achat_header(conn, date_op.isoformat(), fournisseur.strip(), type_achat)
                            st.session_state.current_achat_id = achat_header_id
                            display_success_message(f"Fiche d'achat créée (ID: {achat_header_id}) - Vous pouvez maintenant ajouter des articles")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la création: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            if 'current_achat_id' in st.session_state:
                with st.container():
                    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                    st.markdown("<div class='subsection-header'>📦 Ajouter des Articles</div>", unsafe_allow_html=True)
                    
                    with st.form("form_achat_item", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            produit = st.text_input("📦 Produit", placeholder="Nom du produit", key="achat_produit")
                            quantite = st.number_input("🔢 Quantité", min_value=1, value=1, key="achat_quantite")
                        with col2:
                            prix = st.number_input("💰 Prix unitaire", min_value=0.0, value=0.0, step=0.01, key="achat_prix")
                            devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, key="achat_devise")
                        
                        submitted_item = st.form_submit_button("➕ Ajouter l'article", use_container_width=True)
                    
                    if submitted_item:
                        if not produit.strip():
                            display_warning_message("Veuillez saisir un produit")
                        else:
                            try:
                                prix_mad = convertir_en_mad(prix, devise, conn)
                                insert_achat_item(conn, st.session_state.current_achat_id, produit.strip(), 
                                                quantite, prix, devise, prix_mad)
                                display_success_message(f"Article ajouté: {quantite} × {produit}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur lors de l'ajout: {e}")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                try:
                    items_achat = pd.read_sql(
                        "SELECT * FROM achats WHERE achat_header_id = ?", 
                        conn, params=(st.session_state.current_achat_id,)
                    )
                    if not items_achat.empty:
                        with st.container():
                            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                            st.markdown("<div class='subsection-header'>📋 Panier en Cours</div>", unsafe_allow_html=True)
                            
                            items_display = items_achat.copy()
                            items_display['Total MAD'] = items_display['quantite'] * items_display['prix_mad']
                            
                            st.dataframe(
                                items_display[['produit', 'quantite', 'prix_origine', 'devise_origine', 'prix_mad', 'Total MAD']],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # --- Interface de suppression d'article ---
                            st.markdown("### 🗑️ Gérer les articles")
                            col_del1, col_del2 = st.columns([3, 1])
                            with col_del1:
                                options_suppr = {row['id']: f"{row['produit']} ({row['quantite']} unités) - {float(row['prix_mad']):.2f} MAD" for _, row in items_achat.iterrows()}
                                item_to_delete = st.selectbox("Sélectionner un article à supprimer", options=list(options_suppr.keys()), format_func=lambda x: options_suppr.get(x, ""), key=f"sel_del_achat_{st.session_state.current_achat_id}")
                            with col_del2:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("❌ Supprimer l'article", key=f"btn_del_achat_{st.session_state.current_achat_id}", use_container_width=True):
                                    if item_to_delete:
                                        try:
                                            supprimer_achat_item(conn, item_to_delete)
                                            st.success("Article supprimé avec succès!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erreur lors de la suppression: {e}")

                            total_achat = items_display['Total MAD'].sum()
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.metric("💰 Total de l'achat", f"{total_achat:.2f} MAD")
                            with col2:
                                if st.button("✅ Finaliser l'achat", type="primary", use_container_width=True):
                                    del st.session_state.current_achat_id
                                    display_success_message("Achat finalisé avec succès!")
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("📦 Aucun article ajouté à cet achat")
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement des articles: {e}")
        
        with tab_achats2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique des Achats</div>", unsafe_allow_html=True)
                
                # Ajouter des sous-onglets pour différentes vues
                achats_subtabs = st.tabs(["📋 Liste des Achats", "🔍 Détail par Achat", "📊 Analyses Achats"])
                
                with achats_subtabs[0]:  # Liste des achats existante
                    try:
                        achats_headers = pd.read_sql(
                            """SELECT ah.*, COUNT(a.id) as nb_articles 
                               FROM achats_headers ah 
                               LEFT JOIN achats a ON ah.id = a.achat_header_id 
                               GROUP BY ah.id 
                               ORDER BY ah.date DESC""", 
                            conn
                        )
                        
                        if not achats_headers.empty:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                total_achats = achats_headers['total_mad'].sum()
                                display_metric_with_icon("💰", "Total Achats", f"{total_achats:,.2f} MAD")
                            with col2:
                                nb_achats = len(achats_headers)
                                display_metric_with_icon("📦", "Nombre d'Achats", f"{nb_achats}")
                            with col3:
                                achat_ventes = achats_headers[achats_headers['type'] == 'achat']['total_mad'].sum()
                                stock_initial = achats_headers[achats_headers['type'] == 'stock']['total_mad'].sum()
                                display_metric_with_icon("📊", "Achat vs Stock", f"{achat_ventes:,.0f} / {stock_initial:,.0f} MAD")
                            
                            st.markdown("<div class='subsection-header'>📋 Liste des Achats</div>", unsafe_allow_html=True)
                            
                            achats_display = achats_headers.copy()
                            achats_display = achats_display[['id', 'date', 'fournisseur', 'type', 'nb_articles', 'total_mad']]
                            achats_display.columns = ['ID', 'Date', 'Fournisseur', 'Type', 'Nb Articles', 'Total MAD']
                            
                            st.dataframe(
                                achats_display,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "ID": st.column_config.NumberColumn("ID", format="%d"),
                                    "Date": "Date",
                                    "Fournisseur": "Fournisseur",
                                    "Type": "Type",
                                    "Nb Articles": st.column_config.NumberColumn("Articles", format="%d"),
                                    "Total MAD": st.column_config.NumberColumn("Total (MAD)", format="%.2f MAD")
                                }
                            )

                            st.markdown("<div class='subsection-header'>⚡ Actions Rapides</div>", unsafe_allow_html=True)
                            selected_achat_quick = st.selectbox(
                                "Modifier rapidement un achat",
                                achats_headers['id'].tolist(),
                                format_func=lambda x: f"Achat #{x} - {achats_headers[achats_headers['id'] == x].iloc[0]['fournisseur']} - {achats_headers[achats_headers['id'] == x].iloc[0]['date']}",
                                key="quick_edit_achat"
                            )
                            if st.button("✏️ Modifier cet achat", key="btn_quick_edit_achat"):
                                st.session_state.selected_achat_for_edit = selected_achat_quick
                                st.rerun()
                        
                        else:
                            st.info("📊 Aucun achat enregistré")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement des achats: {e}")
                
                with achats_subtabs[1]:  # NOUVEAU : Détail par achat
                    st.markdown("<div class='subsection-header'>🔍 Détail des Achats par Transaction</div>", unsafe_allow_html=True)
                    
                    try:
                        # Récupérer tous les achats pour la sélection
                        achats_liste = pd.read_sql("""
                            SELECT 
                                ah.id,
                                ah.date,
                                ah.fournisseur,
                                ah.type,
                                ah.total_mad,
                                COUNT(a.id) as nb_articles
                            FROM achats_headers ah
                            LEFT JOIN achats a ON ah.id = a.achat_header_id
                            GROUP BY ah.id
                            ORDER BY ah.date DESC
                        """, conn)
                        
                        if not achats_liste.empty:
                            # Sélection de l'achat à détailler
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                achat_selectionne_id = st.selectbox(
                                    "Sélectionner un achat",
                                    achats_liste['id'].tolist(),
                                    format_func=lambda x: f"Achat #{x} - {achats_liste[achats_liste['id'] == x].iloc[0]['fournisseur']} - {achats_liste[achats_liste['id'] == x].iloc[0]['date']} - {achats_liste[achats_liste['id'] == x].iloc[0]['total_mad']:.2f} MAD",
                                    key="select_achat_detail"
                                )
                            
                            if achat_selectionne_id:
                                # Récupérer les informations de l'en-tête
                                achat_header = achats_liste[achats_liste['id'] == achat_selectionne_id].iloc[0]
                                
                                # Afficher les informations générales
                                st.markdown(f"""
                                <div class='info-card'>
                                    <strong>Achat #{achat_selectionne_id}</strong><br>
                                    <strong>Date :</strong> {achat_header['date']}<br>
                                    <strong>Fournisseur :</strong> {achat_header['fournisseur']}<br>
                                    <strong>Type :</strong> {achat_header['type']}<br>
                                    <strong>Total :</strong> {achat_header['total_mad']:.2f} MAD
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Récupérer le détail des produits
                                detail_achat = pd.read_sql("""
                                    SELECT 
                                        a.id as item_id,
                                        a.produit,
                                        a.quantite,
                                        a.prix_origine,
                                        a.devise_origine,
                                        a.prix_mad as prix_achat_mad,
                                        (a.quantite * a.prix_mad) as total_ligne_mad,
                                        COALESCE((
                                            SELECT SUM(v.quantite)
                                            FROM ventes v
                                            WHERE v.achat_source_id = a.id
                                        ), 0) as quantite_vendue,
                                        a.quantite - COALESCE((
                                            SELECT SUM(v.quantite)
                                            FROM ventes v
                                            WHERE v.achat_source_id = a.id
                                        ), 0) as quantite_restante
                                    FROM achats a
                                    WHERE a.achat_header_id = ?
                                    ORDER BY a.produit
                                """, conn, params=(achat_selectionne_id,))
                                
                                if not detail_achat.empty:
                                    # Métriques du détail
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("📦 Produits distincts", len(detail_achat))
                                    with col2:
                                        total_articles = detail_achat['quantite'].sum()
                                        st.metric("🔢 Total articles", f"{total_articles}")
                                    with col3:
                                        total_vendus = detail_achat['quantite_vendue'].sum()
                                        st.metric("✅ Vendus", f"{total_vendus}")
                                    with col4:
                                        total_restants = detail_achat['quantite_restante'].sum()
                                        st.metric("📊 Restants", f"{total_restants}")
                                    
                                    # Tableau détaillé des produits
                                    st.markdown("#### 📋 Détail des produits achetés")
                                    
                                    detail_display = detail_achat.copy()
                                    detail_display = detail_display[[
                                        'produit', 'quantite', 'prix_origine', 'devise_origine', 
                                        'prix_achat_mad', 'total_ligne_mad', 'quantite_vendue', 'quantite_restante'
                                    ]]
                                    
                                    # Calculer le taux de vente
                                    detail_display['taux_vente'] = (detail_display['quantite_vendue'] / detail_display['quantite'] * 100).round(1)
                                    
                                    # Renommer les colonnes
                                    detail_display.columns = [
                                        'Produit', 'Quantité achetée', 'Prix unitaire', 'Devise',
                                        'Prix achat (MAD)', 'Total (MAD)', 'Quantité vendue', 'Stock restant', 'Taux vente %'
                                    ]
                                    
                                    # Ajouter une colonne de statut coloré
                                    def get_statut_stock(row):
                                        if row['Stock restant'] == 0:
                                            return "🟢 Épuisé"
                                        elif row['Stock restant'] < row['Quantité achetée'] * 0.2:
                                            return "🟡 Stock faible"
                                        else:
                                            return "🔵 En stock"
                                    
                                    detail_display['Statut'] = detail_display.apply(get_statut_stock, axis=1)
                                    
                                    st.dataframe(
                                        detail_display,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "Produit": "Produit",
                                            "Quantité achetée": st.column_config.NumberColumn("Acheté", format="%d"),
                                            "Prix unitaire": st.column_config.NumberColumn("Prix unitaire", format="%.2f"),
                                            "Devise": "Devise",
                                            "Prix achat (MAD)": st.column_config.NumberColumn("Prix MAD", format="%.2f MAD"),
                                            "Total (MAD)": st.column_config.NumberColumn("Total", format="%.2f MAD"),
                                            "Quantité vendue": st.column_config.NumberColumn("Vendu", format="%d"),
                                            "Stock restant": st.column_config.NumberColumn("Restant", format="%d"),
                                            "Taux vente %": st.column_config.NumberColumn("Taux vente", format="%.1f%%"),
                                            "Statut": "Statut"
                                        }
                                    )
                                    
                                    # Visualisations
                                    st.markdown("#### 📊 Analyses")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Répartition par produit (en valeur)
                                        fig_repartition = px.pie(
                                            detail_achat,
                                            values='total_ligne_mad',
                                            names='produit',
                                            title="Répartition de la valeur par produit"
                                        )
                                        fig_repartition.update_traces(textposition='inside', textinfo='percent+label')
                                        fig_repartition.update_layout(height=300)
                                        st.plotly_chart(fig_repartition, use_container_width=True)
                                    
                                    with col2:
                                        # État des stocks
                                        stock_data = detail_achat[['produit', 'quantite_vendue', 'quantite_restante']].copy()
                                        stock_data = stock_data.melt(id_vars=['produit'], 
                                                                   value_vars=['quantite_vendue', 'quantite_restante'],
                                                                   var_name='statut', value_name='quantite')
                                        stock_data['statut'] = stock_data['statut'].map({
                                            'quantite_vendue': 'Vendu',
                                            'quantite_restante': 'En stock'
                                        })
                                        
                                        fig_stock = px.bar(
                                            stock_data,
                                            x='produit',
                                            y='quantite',
                                            color='statut',
                                            title="État des stocks par produit",
                                            barmode='stack',
                                            color_discrete_map={'Vendu': '#2ecc71', 'En stock': '#3498db'}
                                        )
                                        fig_stock.update_layout(height=300, xaxis_tickangle=-45)
                                        st.plotly_chart(fig_stock, use_container_width=True)
                                    
                                    # Détail des ventes liées à cet achat
                                    ventes_liees = pd.read_sql("""
                                        SELECT 
                                            v.id as vente_item_id,
                                            vh.id as vente_header_id,
                                            vh.date as date_vente,
                                            vh.client,
                                            v.produit,
                                            v.quantite,
                                            v.prix_mad as prix_vente_mad,
                                            (v.quantite * v.prix_mad) as total_vente_mad,
                                            (v.prix_mad - a.prix_mad) as marge_unitaire,
                                            ((v.prix_mad - a.prix_mad) * v.quantite) as marge_totale,
                                            ((v.prix_mad - a.prix_mad) / a.prix_mad * 100) as marge_pourcentage
                                        FROM ventes v
                                        JOIN ventes_headers vh ON v.vente_header_id = vh.id
                                        JOIN achats a ON v.achat_source_id = a.id
                                        WHERE a.achat_header_id = ?
                                        ORDER BY vh.date DESC
                                    """, conn, params=(achat_selectionne_id,))
                                    
                                    if not ventes_liees.empty:
                                        st.markdown("#### 💰 Ventes liées à cet achat")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            total_ventes = ventes_liees['total_vente_mad'].sum()
                                            st.metric("💰 Total ventes", f"{total_ventes:,.2f} MAD")
                                        with col2:
                                            total_marge = ventes_liees['marge_totale'].sum()
                                            st.metric("✅ Marge totale", f"{total_marge:,.2f} MAD")
                                        with col3:
                                            marge_moyenne = ventes_liees['marge_pourcentage'].mean()
                                            st.metric("📊 Marge moyenne", f"{marge_moyenne:.1f}%")
                                        
                                        ventes_display = ventes_liees[[
                                            'date_vente', 'client', 'produit', 'quantite',
                                            'prix_vente_mad', 'total_vente_mad', 'marge_unitaire', 'marge_pourcentage'
                                        ]].copy()
                                        
                                        ventes_display.columns = [
                                            'Date vente', 'Client', 'Produit', 'Qté',
                                            'Prix vente MAD', 'Total MAD', 'Marge unitaire', 'Marge %'
                                        ]
                                        
                                        st.dataframe(
                                            ventes_display,
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                    
                                else:
                                    st.warning("Aucun détail trouvé pour cet achat")
                        
                        else:
                            st.info("📊 Aucun achat disponible")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement du détail: {e}")
                
                with achats_subtabs[2]:  # NOUVEAU : Analyses Achats
                    st.markdown("<div class='subsection-header'>📊 Analyses des Achats</div>", unsafe_allow_html=True)
                    
                    try:
                        # Récupérer toutes les données pour analyse
                        achats_complets = pd.read_sql("""
                            SELECT 
                                ah.id as achat_id,
                                ah.date,
                                ah.fournisseur,
                                ah.type,
                                a.id as item_id,
                                a.produit,
                                a.quantite,
                                a.prix_mad as prix_achat_mad,
                                (a.quantite * a.prix_mad) as total_ligne,
                                COALESCE((
                                    SELECT SUM(v.quantite)
                                    FROM ventes v
                                    WHERE v.achat_source_id = a.id
                                ), 0) as quantite_vendue,
                                COALESCE((
                                    SELECT SUM(v.quantite * v.prix_mad)
                                    FROM ventes v
                                    WHERE v.achat_source_id = a.id
                                ), 0) as total_vendu
                            FROM achats_headers ah
                            JOIN achats a ON ah.id = a.achat_header_id
                            ORDER BY ah.date DESC
                        """, conn)
                        
                        if not achats_complets.empty:
                            # Calcul des métriques globales
                            total_achete = achats_complets['total_ligne'].sum()
                            total_vendu = achats_complets['total_vendu'].sum()
                            total_non_vendu = total_achete - total_vendu
                            taux_ecoulement = (total_vendu / total_achete * 100) if total_achete > 0 else 0
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("💰 Total acheté", f"{total_achete:,.2f} MAD")
                            with col2:
                                st.metric("💵 Total vendu", f"{total_vendu:,.2f} MAD")
                            with col3:
                                st.metric("📦 Non vendu", f"{total_non_vendu:,.2f} MAD")
                            with col4:
                                st.metric("📊 Taux d'écoulement", f"{taux_ecoulement:.1f}%")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Top fournisseurs
                                top_fournisseurs = achats_complets.groupby('fournisseur').agg({
                                    'total_ligne': 'sum',
                                    'achat_id': 'nunique'
                                }).reset_index().nlargest(10, 'total_ligne')
                                
                                fig_fournisseurs = px.bar(
                                    top_fournisseurs,
                                    x='fournisseur',
                                    y='total_ligne',
                                    title="Top 10 fournisseurs par montant",
                                    labels={'fournisseur': 'Fournisseur', 'total_ligne': 'Montant (MAD)'}
                                )
                                fig_fournisseurs.update_layout(height=300, xaxis_tickangle=-45)
                                st.plotly_chart(fig_fournisseurs, use_container_width=True)
                            
                            with col2:
                                # Top produits achetés
                                top_produits = achats_complets.groupby('produit').agg({
                                    'total_ligne': 'sum',
                                    'quantite': 'sum'
                                }).reset_index().nlargest(10, 'total_ligne')
                                
                                fig_produits = px.bar(
                                    top_produits,
                                    x='produit',
                                    y='total_ligne',
                                    title="Top 10 produits par montant d'achat",
                                    labels={'produit': 'Produit', 'total_ligne': 'Montant (MAD)'}
                                )
                                fig_produits.update_layout(height=300, xaxis_tickangle=-45)
                                st.plotly_chart(fig_produits, use_container_width=True)
                            
                            # Analyse par type d'achat
                            st.markdown("#### 📊 Répartition par type d'achat")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                type_stats = achats_complets.groupby('type').agg({
                                    'total_ligne': 'sum',
                                    'achat_id': 'nunique'
                                }).reset_index()
                                
                                fig_type = px.pie(
                                    type_stats,
                                    values='total_ligne',
                                    names='type',
                                    title="Répartition des montants par type",
                                    color='type',
                                    color_discrete_map={'achat': '#3498db', 'stock': '#2ecc71'}
                                )
                                fig_type.update_traces(textposition='inside', textinfo='percent+label')
                                fig_type.update_layout(height=300)
                                st.plotly_chart(fig_type, use_container_width=True)
                            
                            with col2:
                                # Évolution mensuelle des achats
                                achats_complets['date'] = pd.to_datetime(achats_complets['date'])
                                achats_mensuels = achats_complets.groupby(
                                    achats_complets['date'].dt.to_period('M')
                                )['total_ligne'].sum().reset_index()
                                achats_mensuels['date'] = achats_mensuels['date'].dt.to_timestamp()
                                
                                fig_evolution = px.line(
                                    achats_mensuels,
                                    x='date',
                                    y='total_ligne',
                                    title="Évolution mensuelle des achats",
                                    markers=True
                                )
                                fig_evolution.update_layout(height=300)
                                st.plotly_chart(fig_evolution, use_container_width=True)
                            
                        else:
                            st.info("📊 Aucune donnée d'achat disponible pour l'analyse")
                            
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'analyse: {e}")
                
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_achats3:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Modifier un Achat</div>", unsafe_allow_html=True)
                
                try:
                    achats_headers = pd.read_sql("SELECT * FROM achats_headers ORDER BY date DESC", conn)
                    
                    if not achats_headers.empty:
                        selected_achat_id = st.selectbox(
                            "Sélectionner un achat à modifier",
                            achats_headers['id'].tolist(),
                            format_func=lambda x: f"Achat #{x} - {achats_headers[achats_headers['id'] == x].iloc[0]['fournisseur']} - {achats_headers[achats_headers['id'] == x].iloc[0]['date']}",
                            key="select_achat_modify"
                        )
                        
                        if selected_achat_id:
                            achat_data = achats_headers[achats_headers['id'] == selected_achat_id].iloc[0]
                            articles_achat = pd.read_sql(
                                "SELECT * FROM achats WHERE achat_header_id = ?", 
                                conn, params=(selected_achat_id,)
                            )
                            
                            with st.form("form_modify_achat_header"):
                                st.markdown("### Modifier l'en-tête de l'achat")
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_date = st.date_input("📅 Date", value=datetime.strptime(achat_data['date'], '%Y-%m-%d').date(), key="mod_achat_date")
                                    new_fournisseur = st.text_input("🏢 Fournisseur", value=achat_data['fournisseur'], key="mod_achat_fournisseur")
                                with col2:
                                    new_type = st.selectbox("📋 Type", ["achat", "stock"], 
                                                          index=0 if achat_data['type'] == 'achat' else 1,
                                                          key="mod_achat_type")
                                
                                if st.form_submit_button("💾 Mettre à jour l'en-tête"):
                                    modifier_achat_header(conn, selected_achat_id, new_date.isoformat(), new_fournisseur, new_type)
                                    display_success_message("En-tête d'achat mis à jour")
                                    st.rerun()
                            
                            st.markdown("### Modifier les articles")
                            
                            if not articles_achat.empty:
                                st.markdown("#### Articles existants")
                                for index, article in articles_achat.iterrows():
                                    with st.form(f"form_modify_achat_article_{article['id']}"):
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            new_produit = st.text_input("📦 Produit", value=article['produit'], key=f"achat_prod_{article['id']}")
                                            new_quantite = st.number_input("🔢 Quantité", min_value=1, value=article['quantite'], key=f"achat_qte_{article['id']}")
                                        with col2:
                                            new_prix = st.number_input("💰 Prix", min_value=0.0, value=float(article['prix_origine']), key=f"achat_prix_{article['id']}")
                                            new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, 
                                                                    index=SUPPORTED_DEVISES.index(article['devise_origine']), 
                                                                    key=f"achat_dev_{article['id']}")
                                        with col3:
                                            st.write("")
                                            if st.form_submit_button("✏️ Mettre à jour l'article", use_container_width=True):
                                                new_prix_mad = convertir_en_mad(new_prix, new_devise, conn)
                                                modifier_achat_item(conn, article['id'], new_produit, new_quantite, new_prix, new_devise, new_prix_mad)
                                                display_success_message("Article mis à jour")
                                                st.rerun()
                                            if st.form_submit_button("❌ Supprimer", use_container_width=True):
                                                supprimer_achat_item(conn, article['id'])
                                                display_success_message("Article supprimé avec succès!")
                                                st.rerun()
                            
                            st.markdown("#### ➕ Ajouter un nouvel article")
                            with st.form("form_add_article_achat"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    new_produit = st.text_input("📦 Nouveau produit", placeholder="Nom du produit", key=f"new_prod_achat_{selected_achat_id}")
                                    new_quantite = st.number_input("🔢 Quantité", min_value=1, value=1, key=f"new_qte_achat_{selected_achat_id}")
                                with col2:
                                    new_prix = st.number_input("💰 Prix unitaire", min_value=0.0, value=0.0, step=0.01, key=f"new_prix_achat_{selected_achat_id}")
                                    new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, key=f"new_dev_achat_{selected_achat_id}")
                                with col3:
                                    st.write("")
                                    if st.form_submit_button("➕ Ajouter l'article à l'achat"):
                                        if not new_produit.strip():
                                            display_warning_message("Veuillez saisir un produit")
                                        else:
                                            try:
                                                new_prix_mad = convertir_en_mad(new_prix, new_devise, conn)
                                                ajouter_article_achat_existant(conn, selected_achat_id, new_produit.strip(), 
                                                                             new_quantite, new_prix, new_devise, new_prix_mad)
                                                display_success_message(f"Nouvel article ajouté: {new_quantite} × {new_produit}")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Erreur lors de l'ajout: {e}")
                            
                            st.markdown("### Supprimer l'achat")
                            if st.button("🗑️ Supprimer cet achat", type="secondary"):
                                supprimer_achat_header(conn, selected_achat_id)
                                display_success_message("Achat supprimée")
                                st.rerun()
                    
                    else:
                        st.info("📊 Aucun achat à modifier")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la modification: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_achats4:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>📈 Analyse des Achats par Produit</div>", unsafe_allow_html=True)
                
                produits_stats = get_produits_achetes(conn)
                
                if not produits_stats.empty:
                    # Métriques Clés
                    st.markdown("#### 📊 Indicateurs Clés")
                    cols = st.columns(3)
                    
                    top_cout = produits_stats.nlargest(3, 'cout_total_mad')
                    for i, (idx, row) in enumerate(top_cout.iterrows()):
                        if i < 3:
                            with cols[i]:
                                st.metric(f"🏆 Top {i+1} : {row['produit']}", f"{row['cout_total_mad']:,.2f} MAD")
                    
                    st.markdown("---")
                    
                    # Graphiques
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top produits par Coût
                        top_10_cout = produits_stats.nlargest(10, 'cout_total_mad')
                        fig_cout = px.bar(
                            top_10_cout,
                            x='produit',
                            y='cout_total_mad',
                            title="Top 10 produits par coût total d'achat",
                            labels={'produit': 'Produit', 'cout_total_mad': 'Coût Total (MAD)'},
                            color='cout_total_mad',
                            color_continuous_scale='Viridis'
                        )
                        fig_cout.update_layout(height=350, xaxis_tickangle=-45)
                        st.plotly_chart(fig_cout, use_container_width=True)
                    
                    with col2:
                        # Top produits par Quantité
                        top_10_qte = produits_stats.nlargest(10, 'quantite_totale_achetee')
                        fig_qte = px.bar(
                            top_10_qte,
                            x='produit',
                            y='quantite_totale_achetee',
                            title="Top 10 produits par quantité achetée",
                            labels={'produit': 'Produit', 'quantite_totale_achetee': 'Quantité Totale'},
                            color='quantite_totale_achetee',
                            color_continuous_scale='Magma'
                        )
                        fig_qte.update_layout(height=350, xaxis_tickangle=-45)
                        st.plotly_chart(fig_qte, use_container_width=True)
                    
                    # Matrice Coût/Quantité
                    fig_scatter = px.scatter(
                        produits_stats,
                        x='quantite_totale_achetee',
                        y='cout_total_mad',
                        size='nb_factures',
                        hover_name='produit',
                        text='produit',
                        title="Matrice Achats : Quantité vs Coût Total",
                        labels={
                            'quantite_totale_achetee': 'Quantité totale achetée',
                            'cout_total_mad': "Coût total (MAD)",
                            'nb_factures': 'Nombre de factures'
                        }
                    )
                    fig_scatter.update_traces(textposition='top center')
                    fig_scatter.update_layout(height=400)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # Tableau détaillé
                    st.markdown("<div class='subsection-header'>📋 Détail des Achats par Produit</div>", unsafe_allow_html=True)
                    
                    produits_display = produits_stats.copy()
                    produits_display = produits_display[[
                        'produit', 'nb_factures', 'quantite_totale_achetee', 
                        'cout_total_mad', 'prix_achat_moyen', 
                        'premier_achat', 'dernier_achat'
                    ]]
                    
                    # Formater les colonnes
                    produits_display['cout_total_mad'] = produits_display['cout_total_mad'].round(2)
                    produits_display['prix_achat_moyen'] = produits_display['prix_achat_moyen'].round(2)
                    
                    st.dataframe(
                        produits_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "produit": "Produit",
                            "nb_factures": st.column_config.NumberColumn("Factures", format="%d"),
                            "quantite_totale_achetee": st.column_config.NumberColumn("Qté Totale", format="%d"),
                            "cout_total_mad": st.column_config.NumberColumn("Coût Total", format="%.2f MAD"),
                            "prix_achat_moyen": st.column_config.NumberColumn("Prix Moyen", format="%.2f MAD"),
                            "premier_achat": "Premier achat",
                            "dernier_achat": "Dernier achat"
                        }
                    )
                else:
                    st.info("📊 Aucune donnée d'achat disponible pour l'analyse")
                
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "💰 Dépenses":
        display_view_header("Gestion des Dépenses", "Contrôlez vos dépenses et votre trésorerie", "💰")
        
        try:
            ventes_headers = pd.read_sql("SELECT * FROM ventes_headers", conn)
            achats_headers = pd.read_sql("SELECT * FROM achats_headers", conn)
            prestations = pd.read_sql("SELECT * FROM prestations", conn)
            depenses_existantes = pd.read_sql("SELECT * FROM depenses", conn)
            
            ca_ventes = ventes_headers['total_mad'].sum() if not ventes_headers.empty else 0.0
            ca_prestations = prestations['montant_mad'].sum() if not prestations.empty else 0.0
            ca_total = ca_ventes + ca_prestations
            
            cout_achats_ventes = achats_headers[achats_headers["type"] == "achat"]['total_mad'].sum() if not achats_headers.empty else 0.0
            
            # Déduire également les salaires hebdomadaires
            try:
                hebdo_data = pd.read_sql("SELECT SUM(salaire_1) as s1, SUM(salaire_2) as s2 FROM hebdo", conn)
                total_salaires = float(hebdo_data['s1'].fillna(0).iloc[0]) + float(hebdo_data['s2'].fillna(0).iloc[0])
            except:
                total_salaires = 0.0
            
            argent_disponible = ca_total - cout_achats_ventes - depenses_argent_disponible - total_salaires
        except Exception as e:
            st.error(f"Erreur calcul trésorerie: {e}")
            argent_disponible = 0.0
        
        tab_depenses1, tab_depenses2, tab_depenses3 = st.tabs(["➕ Nouvelle Dépense", "🗂️ Historique", "✏️ Modifier Dépense"])
        
        with tab_depenses1:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Nouvelle Dépense</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='subsection-header'>💵 État de la Trésorerie</div>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💰 Argent Disponible", f"{argent_disponible:,.2f} MAD")
                with col2:
                    if argent_disponible < 0:
                        st.error("⚠️ Trésorerie négative")
                    elif argent_disponible < 1000:
                        st.warning("📉 Trésorerie faible")
                    else:
                        st.success("✅ Trésorerie saine")
                
                with st.form("form_depense", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        date_op = st.date_input("📅 Date", value=date.today(), key="depense_date")
                        categorie = st.text_input("📂 Catégorie", placeholder="Ex: Transport, Fournitures...", key="depense_categorie")
                        montant = st.number_input("💰 Montant", min_value=0.0, value=0.0, step=0.01, key="depense_montant")
                        devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, key="depense_devise")
                    with col2:
                        description = st.text_area("📝 Description", placeholder="Détails de la dépense...", key="depense_description")
                        source_fonds = st.radio(
                            "💰 Source des fonds",
                            ["argent_disponible", "autre_source"],
                            format_func=lambda x: "💵 Argent des ventes" if x == "argent_disponible" else "🆕 Autre source",
                            key="depense_source"
                        )
                        
                        st.markdown("**🔄 Lier à un achat (import)**")
                        achats_existants = pd.read_sql("SELECT id, date, fournisseur FROM achats_headers ORDER BY date DESC", conn)
                        if not achats_existants.empty:
                            options_achats = ["Aucun"] + achats_existants['id'].tolist()
                            format_func = lambda x: "Aucun" if x == "Aucun" else f"Achat #{x} - {achats_existants[achats_existants['id'] == x].iloc[0]['fournisseur']} - {achats_existants[achats_existants['id'] == x].iloc[0]['date']}"
                            achat_lie = st.selectbox("Lier à un achat", options_achats, format_func=format_func, key="depense_achat_lie")
                            achat_header_id = None if achat_lie == "Aucun" else achat_lie
                        else:
                            achat_header_id = None
                            st.info("Aucun achat disponible pour liaison")
                    
                    if source_fonds == "argent_disponible" and montant > argent_disponible:
                        st.warning(f"⚠️ Attention : Cette dépense dépasse l'argent disponible ({argent_disponible:,.2f} MAD)")
                    
                    submitted_depense = st.form_submit_button("✅ Ajouter la dépense", use_container_width=True)
                
                if submitted_depense:
                    if not categorie.strip():
                        display_warning_message("Veuillez saisir une catégorie")
                    elif montant <= 0:
                        display_warning_message("Le montant doit être supérieur à 0")
                    elif source_fonds == "argent_disponible" and montant > argent_disponible:
                        display_warning_message("Dépense impossible : montant supérieur à l'argent disponible")
                    else:
                        try:
                            montant_mad = convertir_en_mad(montant, devise, conn)
                            insert_depense(conn, date_op.isoformat(), categorie.strip(), montant, devise, montant_mad, description, source_fonds, achat_header_id)
                            
                            if source_fonds == "argent_disponible":
                                if achat_header_id:
                                    display_success_message(f"Dépense d'import enregistrée: {montant} {devise} = {montant_mad:.2f} MAD (liée à l'achat #{achat_header_id})")
                                else:
                                    display_success_message(f"Dépense enregistrée: {montant} {devise} = {montant_mad:.2f} MAD (Argent des ventes)")
                            else:
                                display_success_message(f"Dépense enregistrée: {montant} {devise} = {montant_mad:.2f} MAD (Autre source)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'enregistrement: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab_depenses2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique des Dépenses</div>", unsafe_allow_html=True)
                
                try:
                    depenses = pd.read_sql("SELECT * FROM depenses ORDER BY date DESC", conn)
                    if not depenses.empty:
                        if 'source_fonds' not in depenses.columns:
                            st.warning("⚠️ La structure de la base de données nécessite une mise à jour. Veuillez rafraîchir la page.")
                            depenses['source_fonds'] = 'argent_disponible'
                        else:
                            total_depenses = depenses['montant_mad'].sum()
                            nb_depenses = len(depenses)
                            depenses_argent_disponible = depenses[depenses['source_fonds'] == 'argent_disponible']['montant_mad'].sum()
                            depenses_autre_source = depenses[depenses['source_fonds'] == 'autre_source']['montant_mad'].sum()
                            
                            depenses_import = depenses[depenses['type_depense'] == 'import']
                            nb_depenses_import = len(depenses_import)
                            total_depenses_import = depenses_import['montant_mad'].sum()
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                display_metric_with_icon("💰", "Total Dépenses", f"{total_depenses:,.2f} MAD")
                            with col2:
                                display_metric_with_icon("📊", "Nombre", f"{nb_depenses}")
                            with col3:
                                display_metric_with_icon("💵", "Dep. Argent Ventes", f"{depenses_argent_disponible:,.2f} MAD")
                            with col4:
                                display_metric_with_icon("🆕", "Dep. Autre Source", f"{depenses_autre_source:,.2f} MAD")
                            
                            if nb_depenses_import > 0:
                                col1, col2 = st.columns(2)
                                with col1:
                                    display_metric_with_icon("🔄", "Dépenses Import", f"{total_depenses_import:,.2f} MAD")
                                with col2:
                                    display_metric_with_icon("📦", "Nb Dépenses Import", f"{nb_depenses_import}")
                            
                            st.markdown("<div class='subsection-header'>📊 Répartition des Dépenses par Source</div>", unsafe_allow_html=True)
                            
                            try:
                                depenses_par_source = pd.read_sql("""
                                    SELECT 
                                        source_fonds,
                                        COUNT(*) as nb_depenses,
                                        SUM(montant_mad) as total_mad,
                                        AVG(montant_mad) as moyenne_depense
                                    FROM depenses 
                                    GROUP BY source_fonds
                                    ORDER BY total_mad DESC
                                """, conn)
                                
                                if not depenses_par_source.empty:
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        fig_source = px.pie(
                                            depenses_par_source,
                                            values='total_mad',
                                            names='source_fonds',
                                            color='source_fonds',
                                            color_discrete_map={
                                                'argent_disponible': '#3498db',
                                                'autre_source': '#e74c3c'
                                            },
                                            title="Répartition des dépenses par source"
                                        )
                                        fig_source.update_traces(textposition='inside', textinfo='percent+label')
                                        fig_source.update_layout(height=300)
                                        st.plotly_chart(fig_source, use_container_width=True)
                                    
                                    with col2:
                                        depenses_argent = depenses_par_source[depenses_par_source['source_fonds'] == 'argent_disponible']
                                        depenses_autre = depenses_par_source[depenses_par_source['source_fonds'] == 'autre_source']
                                        
                                        if not depenses_argent.empty:
                                            st.metric(
                                                "💵 Dépenses Argent Ventes",
                                                f"{depenses_argent.iloc[0]['total_mad']:,.2f} MAD",
                                                f"{depenses_argent.iloc[0]['nb_depenses']} dépenses"
                                            )
                                        
                                        if not depenses_autre.empty:
                                            st.metric(
                                                "🆕 Dépenses Autre Source",
                                                f"{depenses_autre.iloc[0]['total_mad']:,.2f} MAD",
                                                f"{depenses_autre.iloc[0]['nb_depenses']} dépenses"
                                            )
                                            
                            except Exception as e:
                                st.error(f"Erreur lors de l'analyse des sources: {e}")
                            
                            st.markdown("<div class='subsection-header'>🔍 Filtres Avancés</div>", unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                filtre_source = st.selectbox(
                                    "Source des fonds",
                                    ["Toutes", "Argent disponible", "Autre source"],
                                    key="filtre_source_depenses"
                                )

                            with col2:
                                date_debut = st.date_input("Date début", value=date.today() - timedelta(days=30))

                            with col3:
                                date_fin = st.date_input("Date fin", value=date.today())

                            try:
                                query = "SELECT * FROM depenses WHERE date BETWEEN ? AND ?"
                                params = [date_debut.isoformat(), date_fin.isoformat()]
                                
                                if filtre_source == "Argent disponible":
                                    query += " AND source_fonds = ?"
                                    params.append("argent_disponible")
                                elif filtre_source == "Autre source":
                                    query += " AND source_fonds = ?"
                                    params.append("autre_source")
                                
                                query += " ORDER BY date DESC"
                                
                                depenses_filtrees = pd.read_sql(query, conn, params=params)
                                
                                if not depenses_filtrees.empty:
                                    total_filtre = depenses_filtrees['montant_mad'].sum()
                                    nb_depenses_filtre = len(depenses_filtrees)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric(f"💰 Total ({filtre_source})", f"{total_filtre:,.2f} MAD")
                                    with col2:
                                        st.metric("📊 Nombre de dépenses", nb_depenses_filtre)
                                    
                                    st.markdown("<div class='subsection-header'>📋 Liste des Dépenses</div>", unsafe_allow_html=True)
                                    
                                    depenses_display = depenses_filtrees.copy()
                                    depenses_display = depenses_display[['id', 'date', 'categorie', 'description', 'montant_origine', 'devise_origine', 'montant_mad', 'source_fonds', 'achat_header_id', 'type_depense']]
                                    depenses_display['source_fonds'] = depenses_display['source_fonds'].map({
                                        'argent_disponible': '💵 Argent ventes',
                                        'autre_source': '🆕 Autre source'
                                    })
                                    depenses_display['type_depense'] = depenses_display['type_depense'].map({
                                        'generale': 'Générale',
                                        'import': '🔄 Import'
                                    })
                                    depenses_display.columns = ['ID', 'Date', 'Catégorie', 'Description', 'Montant', 'Devise', 'MAD', 'Source', 'Achat Lié', 'Type']
                                    
                                    st.dataframe(
                                        depenses_display,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "ID": st.column_config.NumberColumn("ID", format="%d"),
                                            "Date": "Date",
                                            "Catégorie": "Catégorie",
                                            "Description": "Description",
                                            "Montant": st.column_config.NumberColumn("Montant", format="%.2f"),
                                            "Devise": "Devise",
                                            "MAD": st.column_config.NumberColumn("MAD", format="%.2f MAD"),
                                            "Source": "Source",
                                            "Achat Lié": st.column_config.NumberColumn("Achat Lié", format="%d"),
                                            "Type": "Type"
                                        }
                                    )
                                else:
                                    st.info("Aucune dépense trouvée avec les critères sélectionnés")
                                    
                            except Exception as e:
                                st.error(f"Erreur lors du filtrage: {e}")
                    
                    else:
                        st.info("💰 Aucune dépense enregistrée")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement des dépenses: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_depenses3:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Modifier une Dépense</div>", unsafe_allow_html=True)
                
                try:
                    try:
                        depenses = pd.read_sql("SELECT * FROM depenses ORDER BY date DESC", conn)
                    except:
                        depenses = pd.read_sql("SELECT id, date, categorie, montant_mad, description, devise_origine, montant_origine FROM depenses ORDER BY date DESC", conn)
                        depenses['source_fonds'] = 'argent_disponible'
                        depenses['achat_header_id'] = None
                        depenses['type_depense'] = 'generale'
                    
                    if not depenses.empty:
                        if 'source_fonds' not in depenses.columns:
                            st.warning("⚠️ La structure de la base de données nécessite une mise à jour. Veuillez rafraîchir la page.")
                        else:
                            options_depenses = []
                            for _, depense in depenses.iterrows():
                                option_text = f"Dépense #{depense['id']} - {depense['categorie']} - {depense['date']} - {depense['montant_mad']:.2f} MAD"
                                options_depenses.append((option_text, depense['id']))
                            
                            selected_option = st.selectbox(
                                "Sélectionner une dépense à modifier",
                                options=[opt[0] for opt in options_depenses],
                                key="select_depense_modify_unique"
                            )
                            
                            selected_depense_id = None
                            for option_text, depense_id in options_depenses:
                                if option_text == selected_option:
                                    selected_depense_id = depense_id
                                    break
                            
                            if selected_depense_id:
                                depense_data = depenses[depenses['id'] == selected_depense_id].iloc[0]
                                
                                try:
                                    ventes_headers = pd.read_sql("SELECT * FROM ventes_headers", conn)
                                    achats_headers = pd.read_sql("SELECT * FROM achats_headers", conn)
                                    prestations = pd.read_sql("SELECT * FROM prestations", conn)
                                    autres_depenses = depenses[depenses['id'] != selected_depense_id]
                                    
                                    ca_ventes = ventes_headers['total_mad'].sum() if not ventes_headers.empty else 0.0
                                    ca_prestations = prestations['montant_mad'].sum() if not prestations.empty else 0.0
                                    ca_total = ca_ventes + ca_prestations
                                    
                                    cout_achats_ventes = achats_headers[achats_headers["type"] == "achat"]['total_mad'].sum() if not achats_headers.empty else 0.0
                                    depenses_argent_disponible = autres_depenses[autres_depenses["source_fonds"] == "argent_disponible"]['montant_mad'].sum() if not autres_depenses.empty else 0.0
                                    
                                    argent_disponible_modif = ca_total - cout_achats_ventes - depenses_argent_disponible
                                except Exception as e:
                                    st.error(f"Erreur calcul trésorerie: {e}")
                                    argent_disponible_modif = 0.0
                                
                                st.markdown("<div class='subsection-header'>💵 État de la Trésorerie</div>", unsafe_allow_html=True)
                                st.metric("💰 Argent Disponible", f"{argent_disponible_modif:,.2f} MAD")
                                
                                try:
                                    date_existante = datetime.strptime(depense_data['date'], '%Y-%m-%d').date()
                                except:
                                    date_existante = date.today()
                                
                                source_fonds_existant = depense_data.get('source_fonds', 'argent_disponible')
                                achat_header_id_existant = depense_data.get('achat_header_id', None)
                                type_depense_existant = depense_data.get('type_depense', 'generale')
                                
                                st.markdown(f"**Dépense sélectionnée :** {depense_data['categorie']} - {depense_data['montant_mad']:.2f} MAD - {depense_data['date']}")
                                
                                with st.form(f"form_modify_depense_{selected_depense_id}"):
                                    st.markdown("### Modifier la dépense")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        new_date = st.date_input("📅 Date", value=date_existante, key=f"mod_depense_date_{selected_depense_id}")
                                        new_categorie = st.text_input("📂 Catégorie", value=depense_data['categorie'], key=f"mod_depense_categorie_{selected_depense_id}")
                                        new_montant = st.number_input("💰 Montant", min_value=0.0, value=float(depense_data['montant_origine']), step=0.01, key=f"mod_depense_montant_{selected_depense_id}")
                                    with col2:
                                        new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, 
                                                                index=SUPPORTED_DEVISES.index(depense_data['devise_origine']), 
                                                                key=f"mod_depense_devise_{selected_depense_id}")
                                        new_description = st.text_area("📝 Description", value=depense_data.get('description', ''), key=f"mod_depense_description_{selected_depense_id}")
                                        new_source_fonds = st.radio(
                                            "💰 Source des fonds",
                                            ["argent_disponible", "autre_source"],
                                            format_func=lambda x: "💵 Argent des ventes" if x == "argent_disponible" else "🆕 Autre source",
                                            index=0 if source_fonds_existant == 'argent_disponible' else 1,
                                            key=f"mod_depense_source_{selected_depense_id}"
                                        )
                                        
                                        st.markdown("**🔄 Lier à un achat (import)**")
                                        achats_existants = pd.read_sql("SELECT id, date, fournisseur FROM achats_headers ORDER BY date DESC", conn)
                                        if not achats_existants.empty:
                                            options_achats = ["Aucun"] + achats_existants['id'].tolist()
                                            format_func = lambda x: "Aucun" if x == "Aucun" else f"Achat #{x} - {achats_existants[achats_existants['id'] == x].iloc[0]['fournisseur']} - {achats_existants[achats_existants['id'] == x].iloc[0]['date']}"
                                            
                                            default_index = 0
                                            if achat_header_id_existant is not None:
                                                try:
                                                    default_index = options_achats.index(achat_header_id_existant)
                                                except:
                                                    default_index = 0
                                            
                                            new_achat_lie = st.selectbox("Lier à un achat", options_achats, 
                                                                        index=default_index,
                                                                        format_func=format_func, 
                                                                        key=f"mod_depense_achat_lie_{selected_depense_id}")
                                            new_achat_header_id = None if new_achat_lie == "Aucun" else new_achat_lie
                                        else:
                                            new_achat_header_id = None
                                            st.info("Aucun achat disponible pour liaison")
                                    
                                    if new_source_fonds == "argent_disponible" and new_montant > argent_disponible_modif:
                                        st.warning(f"⚠️ Attention : Cette dépense dépasse l'argent disponible ({argent_disponible_modif:,.2f} MAD)")
                                    
                                    submitted = st.form_submit_button("💾 Mettre à jour la dépense", use_container_width=True)
                                    
                                    if submitted:
                                        if not new_categorie.strip():
                                            display_warning_message("Veuillez saisir une catégorie")
                                        elif new_montant <= 0:
                                            display_warning_message("Le montant doit être supérieur à 0")
                                        elif new_source_fonds == "argent_disponible" and new_montant > argent_disponible_modif:
                                            display_warning_message("Dépense impossible : montant supérieur à l'argent disponible")
                                        else:
                                            try:
                                                new_montant_mad = convertir_en_mad(new_montant, new_devise, conn)
                                                modifier_depense(conn, selected_depense_id, new_date.isoformat(), new_categorie.strip(), new_montant, new_devise, new_montant_mad, new_description, new_source_fonds, new_achat_header_id)
                                                display_success_message("Dépense mise à jour avec succès!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Erreur lors de la mise à jour: {e}")
                                
                                st.markdown("### Supprimer la dépense")
                                if st.button("🗑️ Supprimer cette dépense", type="secondary", key=f"delete_depense_{selected_depense_id}"):
                                    supprimer_depense(conn, selected_depense_id)
                                    display_success_message("Dépense supprimée avec succès!")
                                    st.rerun()
                            
                            else:
                                st.info("Veuillez sélectionner une dépense à modifier")
                    
                    else:
                        st.info("💰 Aucune dépense à modifier")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la modification: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "🎯 Prestations":
        display_view_header("Gestion des Prestations", "Organisez vos services et prestations", "🎯")
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Nouvelle Prestation", "💳 Gestion des Paiements", "📋 Historique", "✏️ Modifier Prestation"])

        with tab1:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Nouvelle Prestation de Service</div>", unsafe_allow_html=True)
                
                with st.form("form_prestation", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        date_op = st.date_input("📅 Date de la prestation", value=date.today(), key="prestation_date")
                        client = st.text_input("👤 Client", placeholder="Nom du client", key="prestation_client")
                        telephone_client = st.text_input("📞 Téléphone", placeholder="06XXXXXXXX", key="prestation_telephone")
                        type_prestation = st.selectbox("🎯 Type de prestation", TYPES_PRESTATION, key="prestation_type")
                    with col2:
                        montant_origine = st.number_input("💰 Montant total", min_value=0.0, value=0.0, step=10.0, key="prestation_montant_total")
                        devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, key="prestation_devise")
                        avance_origine = st.number_input("💵 Avance versée", min_value=0.0, value=0.0, step=10.0, key="prestation_avance")
                        description = st.text_area("📝 Description", 
                                                 placeholder="Détails de la prestation...", 
                                                 height=100,
                                                 key="prestation_description")
                    
                    submitted_prestation = st.form_submit_button("✅ Créer la prestation", use_container_width=True)
                
                if submitted_prestation:
                    if not client.strip():
                        display_warning_message("Veuillez saisir un nom de client")
                    elif not description.strip():
                        display_warning_message("Veuillez saisir une description")
                    elif montant_origine <= 0:
                        display_warning_message("Le montant total doit être supérieur à 0")
                    elif avance_origine > montant_origine:
                        display_warning_message("L'avance ne peut pas dépasser le montant total")
                    else:
                        try:
                            montant_mad = convertir_en_mad(montant_origine, devise, conn)
                            avance_mad = convertir_en_mad(avance_origine, devise, conn)
                            
                            prestation_id = insert_prestation(conn, date_op.isoformat(), client.strip(), telephone_client.strip(), 
                                            type_prestation, description.strip(), montant_mad, devise, 
                                            montant_origine, avance_mad)
                            
                            if avance_origine > 0:
                                insert_paiement_prestation(conn, prestation_id, date_op.isoformat(),
                                                         avance_mad, devise, avance_origine,
                                                         f"Avance initiale - {client}")
                            
                            display_success_message(f"Prestation créée: {montant_origine} {devise} = {montant_mad:.2f} MAD")
                            if avance_origine > 0:
                                display_success_message(f"Avance enregistrée: {avance_origine} {devise} = {avance_mad:.2f} MAD")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la création: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Gestion des Paiements</div>", unsafe_allow_html=True)
                
                try:
                    prestations = pd.read_sql("SELECT * FROM prestations ORDER BY date DESC", conn)
                except:
                    prestations = pd.DataFrame()
                    
                if not prestations.empty:
                    prestations_avec_reste = prestations[prestations['reste_a_payer_mad'] > 0]
                    
                    if not prestations_avec_reste.empty:
                        prestations_list = [(f"{row['id']} - {row['client']} - {row['montant_origine']} {row['devise_origine']} - Reste: {row['reste_a_payer_mad']:.2f} MAD", row['id']) 
                                          for index, row in prestations_avec_reste.iterrows()]
                        
                        prestation_choice = st.selectbox("Sélectionner une prestation", 
                                                       [p[0] for p in prestations_list],
                                                       key="select_prestation_paiement")
                        
                        prestation_id = [p[1] for p in prestations_list if p[0] == prestation_choice][0]
                        prestation_data = prestations[prestations['id'] == prestation_id].iloc[0]
                        
                        with st.container():
                            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                            st.markdown(f"**Prestation sélectionnée:** {prestation_data['client']}")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("💰 Total", f"{prestation_data['montant_origine']} {prestation_data['devise_origine']}")
                            with col2:
                                st.metric("💵 Avance", f"{prestation_data['avance_mad']:.2f} MAD")
                            with col3:
                                st.metric("⏳ Reste à payer", f"{prestation_data['reste_a_payer_mad']:.2f} MAD")
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        with st.container():
                            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                            with st.form("form_paiement"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    date_paiement = st.date_input("📅 Date du paiement", value=date.today(), key="paiement_date")
                                    montant_origine = st.number_input("💰 Montant du paiement", 
                                                                    min_value=0.0, 
                                                                    max_value=float(prestation_data['reste_a_payer_mad']),
                                                                    value=min(100.0, float(prestation_data['reste_a_payer_mad'])),
                                                                    key="paiement_montant")
                                with col2:
                                    reference = st.text_input("🏷️ Référence", placeholder="N° de reçu...", key="paiement_ref")
                                
                                submitted_paiement = st.form_submit_button("💳 Enregistrer le paiement", use_container_width=True)
                            
                            if submitted_paiement:
                                if montant_origine <= 0:
                                    display_warning_message("Le montant doit être supérieur à 0")
                                else:
                                    try:
                                        montant_mad = convertir_en_mad(montant_origine, prestation_data['devise_origine'], conn)
                                        insert_paiement_prestation(conn, prestation_id, date_paiement.isoformat(),
                                                                 montant_mad, prestation_data['devise_origine'], 
                                                                 montant_origine, reference or f"Paiement {date_paiement}")
                                        display_success_message(f"Paiement enregistré: {montant_origine} {prestation_data['devise_origine']} = {montant_mad:.2f} MAD")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors de l'enregistrement: {e}")
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    else:
                        st.info("🎉 Toutes les prestations sont entièrement payées !")
                else:
                    st.info("📊 Aucune prestation enregistrée")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique des Prestations</div>", unsafe_allow_html=True)
                
                try:
                    prestations = pd.read_sql("SELECT * FROM prestations ORDER BY date DESC", conn)
                    if not prestations.empty:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            total_prestations = prestations['montant_mad'].sum()
                            display_metric_with_icon("💰", "Total Prestations", f"{total_prestations:.2f} MAD")
                        with col2:
                            total_avances = prestations['avance_mad'].sum()
                            display_metric_with_icon("💵", "Total Avances", f"{total_avances:.2f} MAD")
                        with col3:
                            total_reste = prestations['reste_a_payer_mad'].sum()
                            display_metric_with_icon("⏳", "Reste à payer", f"{total_reste:.2f} MAD")
                        with col4:
                            prestations_payees = len(prestations[prestations['reste_a_payer_mad'] <= 0])
                            display_metric_with_icon("✅", "Prestations payées", f"{prestations_payees}/{len(prestations)}")

                        st.markdown("<div class='subsection-header'>📋 Liste des Prestations</div>", unsafe_allow_html=True)
                        
                        prestations_display = prestations.copy()
                        prestations_display = prestations_display[['id', 'date', 'client', 'telephone_client', 'type_prestation', 'statut', 'montant_origine', 'devise_origine', 'montant_mad', 'avance_mad', 'reste_a_payer_mad']]
                        prestations_display.columns = ['ID', 'Date', 'Client', 'Téléphone', 'Type', 'Statut', 'Montant', 'Devise', 'MAD Total', 'Avance MAD', 'Reste MAD']
                        
                        st.dataframe(
                            prestations_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "ID": st.column_config.NumberColumn("ID", format="%d"),
                                "Date": "Date",
                                "Client": "Client",
                                "Téléphone": "Téléphone",
                                "Type": "Type",
                                "Statut": "Statut",
                                "Montant": st.column_config.NumberColumn("Montant", format="%.2f"),
                                "Devise": "Devise",
                                "MAD Total": st.column_config.NumberColumn("Total MAD", format="%.2f MAD"),
                                "Avance MAD": st.column_config.NumberColumn("Avance", format="%.2f MAD"),
                                "Reste MAD": st.column_config.NumberColumn("Reste", format="%.2f MAD")
                            }
                        )
                        
                    else:
                        st.info("📊 Aucune prestation enregistrée")
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab4:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Modifier une Prestation</div>", unsafe_allow_html=True)
                
                try:
                    # Récupérer toutes les prestations
                    prestations = pd.read_sql("SELECT * FROM prestations ORDER BY date DESC", conn)
                    
                    if not prestations.empty:
                        # Utiliser session_state pour stocker la prestation sélectionnée
                        if 'selected_prestation_id' not in st.session_state:
                            st.session_state.selected_prestation_id = prestations.iloc[0]['id']
                        
                        # Créer un dictionnaire pour un accès facile
                        prestations_dict = {row['id']: row for _, row in prestations.iterrows()}
                        
                        # Créer les options pour le selectbox
                        prestation_options = []
                        for prestation_id, prestation_data in prestations_dict.items():
                            option_text = f"#{prestation_id} - {prestation_data['client']} - {prestation_data['date']} - {prestation_data['type_prestation']} - {prestation_data['montant_mad']:.2f} MAD"
                            prestation_options.append({"id": prestation_id, "text": option_text})
                        
                        # Sélection de la prestation
                        selected_index = st.selectbox(
                            "Sélectionner une prestation à modifier",
                            options=range(len(prestation_options)),
                            format_func=lambda i: prestation_options[i]['text'],
                            key="prestation_select",
                            index=[i for i, opt in enumerate(prestation_options) if opt['id'] == st.session_state.selected_prestation_id][0] 
                            if any(opt['id'] == st.session_state.selected_prestation_id for opt in prestation_options) else 0
                        )
                        
                        # Mettre à jour l'ID sélectionné dans session_state
                        selected_prestation_id = prestation_options[selected_index]['id']
                        if selected_prestation_id != st.session_state.selected_prestation_id:
                            st.session_state.selected_prestation_id = selected_prestation_id
                            st.rerun()
                        
                        # Récupérer les données de la prestation sélectionnée
                        if st.session_state.selected_prestation_id in prestations_dict:
                            prestation_data = prestations_dict[st.session_state.selected_prestation_id]
                            
                            # Afficher les informations de la prestation sélectionnée
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>Prestation sélectionnée :</strong> #{st.session_state.selected_prestation_id}<br>
                                <strong>Client :</strong> {prestation_data['client']}<br>
                                <strong>Date :</strong> {prestation_data['date']}<br>
                                <strong>Type :</strong> {prestation_data['type_prestation']}<br>
                                <strong>Montant :</strong> {prestation_data['montant_origine']} {prestation_data['devise_origine']} ({prestation_data['montant_mad']:.2f} MAD)
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Formulaire de modification
                            with st.form(key=f"form_modify_prestation_{st.session_state.selected_prestation_id}"):
                                st.markdown("### Modifier la prestation")
                                col1, col2 = st.columns(2)
                                with col1:
                                    try:
                                        date_existante = datetime.strptime(prestation_data['date'], '%Y-%m-%d').date()
                                    except:
                                        date_existante = date.today()
                                    
                                    new_date = st.date_input("📅 Date", value=date_existante)
                                    new_client = st.text_input("👤 Client", value=prestation_data['client'])
                                    new_telephone = st.text_input("📞 Téléphone", value=prestation_data['telephone_client'] or "")
                                    new_type = st.selectbox("🎯 Type", TYPES_PRESTATION, 
                                                          index=TYPES_PRESTATION.index(prestation_data['type_prestation']) 
                                                          if prestation_data['type_prestation'] in TYPES_PRESTATION else 0)
                                with col2:
                                    new_montant = st.number_input("💰 Montant total", 
                                                                 min_value=0.0, 
                                                                 value=float(prestation_data['montant_origine']), 
                                                                 step=10.0)
                                    new_devise = st.selectbox("💱 Devise", SUPPORTED_DEVISES, 
                                                            index=SUPPORTED_DEVISES.index(prestation_data['devise_origine']) 
                                                            if prestation_data['devise_origine'] in SUPPORTED_DEVISES else 0)
                                    new_avance = st.number_input("💵 Avance", 
                                                               min_value=0.0, 
                                                               value=float(prestation_data['avance_mad']), 
                                                               step=10.0)
                                    new_description = st.text_area("📝 Description", 
                                                                 value=prestation_data['description'], 
                                                                 height=100)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    submitted = st.form_submit_button("💾 Mettre à jour la prestation", use_container_width=True)
                                with col2:
                                    reset_form = st.form_submit_button("🔄 Réinitialiser", use_container_width=True)
                                
                                if submitted:
                                    if not new_client.strip():
                                        display_warning_message("Veuillez saisir un nom de client")
                                    elif not new_description.strip():
                                        display_warning_message("Veuillez saisir une description")
                                    elif new_montant <= 0:
                                        display_warning_message("Le montant total doit être supérieur à 0")
                                    elif new_avance > new_montant:
                                        display_warning_message("L'avance ne peut pas dépasser le montant total")
                                    else:
                                        try:
                                            new_montant_mad = convertir_en_mad(new_montant, new_devise, conn)
                                            new_avance_mad = convertir_en_mad(new_avance, new_devise, conn)
                                            modifier_prestation(conn, st.session_state.selected_prestation_id, 
                                                              new_date.isoformat(), 
                                                              new_client.strip(), 
                                                              new_telephone.strip(), 
                                                              new_type, 
                                                              new_description.strip(), 
                                                              new_montant_mad, 
                                                              new_devise, 
                                                              new_montant, 
                                                              new_avance_mad)
                                            display_success_message("✅ Prestation mise à jour avec succès!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erreur lors de la mise à jour: {e}")
                                
                                if reset_form:
                                    st.rerun()
                            
                            # Formulaire de modification du statut séparé
                            st.markdown("### Modifier le statut")
                            with st.form(key=f"form_modify_statut_{st.session_state.selected_prestation_id}"):
                                new_statut = st.selectbox("Nouveau statut", 
                                                        STATUTS_PRESTATION, 
                                                        index=STATUTS_PRESTATION.index(prestation_data['statut']) 
                                                        if prestation_data['statut'] in STATUTS_PRESTATION else 0)
                                if st.form_submit_button("🔄 Mettre à jour le statut", use_container_width=True):
                                    update_statut_prestation(conn, st.session_state.selected_prestation_id, new_statut)
                                    display_success_message("✅ Statut mis à jour avec succès!")
                                    st.rerun()
                            
                            # Afficher l'historique des paiements
                            paiements = get_paiements_prestation(st.session_state.selected_prestation_id)
                            if not paiements.empty:
                                st.markdown("### 💳 Historique des paiements")
                                st.dataframe(
                                    paiements[['date_paiement', 'montant_origine', 'devise_origine', 'montant_mad', 'reference']],
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "date_paiement": "Date",
                                        "montant_origine": "Montant",
                                        "devise_origine": "Devise",
                                        "montant_mad": "Montant (MAD)",
                                        "reference": "Référence"
                                    }
                                )
                            
                            # Supprimer la prestation
                            st.markdown("### Supprimer la prestation")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🗑️ Supprimer cette prestation", type="secondary", use_container_width=True):
                                    st.session_state.confirm_delete_prestation = True
                            with col2:
                                if st.session_state.get('confirm_delete_prestation', False):
                                    if st.button("⚠️ CONFIRMER LA SUPPRESSION", type="primary", use_container_width=True):
                                        try:
                                            supprimer_prestation(conn, st.session_state.selected_prestation_id)
                                            del st.session_state.confirm_delete_prestation
                                            del st.session_state.selected_prestation_id
                                            display_success_message("✅ Prestation supprimée avec succès!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erreur lors de la suppression: {e}")
                                    
                                    if st.button("Annuler", use_container_width=True):
                                        del st.session_state.confirm_delete_prestation
                                        st.rerun()
                    
                    else:
                        st.info("📊 Aucune prestation à modifier")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la modification: {e}")
                    import traceback
                    st.error(traceback.format_exc())
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📊 Tableau de Bord":
        display_view_header("Tableau de Bord", "Analyses et indicateurs de performance", "📊")
        
        try:
            ventes_headers = pd.read_sql("SELECT * FROM ventes_headers ORDER BY date DESC", conn)
            achats_headers = pd.read_sql("SELECT * FROM achats_headers ORDER BY date DESC", conn)
            depenses = pd.read_sql("SELECT * FROM depenses ORDER BY date DESC", conn)
            prestations = pd.read_sql("SELECT * FROM prestations ORDER BY date DESC", conn)
            stock_actuel = get_stock_actuel(conn)

            ca_ventes = ventes_headers['total_mad'].sum() if not ventes_headers.empty else 0.0
            ca_prestations = prestations['montant_mad'].sum() if not prestations.empty else 0.0
            ca_total = ca_ventes + ca_prestations
            
            cout_achats_ventes = achats_headers[achats_headers["type"] == "achat"]['total_mad'].sum() if not achats_headers.empty else 0.0
            cout_stock_initial = achats_headers[achats_headers["type"] == "stock"]['total_mad'].sum() if not achats_headers.empty else 0.0
            total_depenses = depenses["montant_mad"].sum() if not depenses.empty else 0.0
            
            depenses_detail = pd.read_sql("""
                SELECT 
                    source_fonds,
                    SUM(montant_mad) as total_mad,
                    COUNT(*) as nb_depenses
                FROM depenses 
                GROUP BY source_fonds
            """, conn) if not depenses.empty else pd.DataFrame()
            
            depenses_argent_disponible = depenses_detail[depenses_detail['source_fonds'] == 'argent_disponible']['total_mad'].sum() if not depenses_detail.empty else 0
            depenses_autre_source = depenses_detail[depenses_detail['source_fonds'] == 'autre_source']['total_mad'].sum() if not depenses_detail.empty else 0
            
            tresorerie_disponible = ca_total - cout_achats_ventes - depenses_argent_disponible
            benefice = ca_total - cout_achats_ventes - total_depenses - cout_stock_initial

            st.markdown("<div class='section-header'>💹 Synthèse de Performance</div>", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_metric_with_icon("💰", "CA Total", f"{ca_total:,.2f} MAD", 
                                      delta=f"Ventes: {ca_ventes:,.0f} + Prestat.: {ca_prestations:,.0f}")
            with col2:
                display_metric_with_icon("📦", "Coût Achats", f"{cout_achats_ventes:,.2f} MAD")
            with col3:
                display_metric_with_icon("💸", "Charges", f"{total_depenses:,.2f} MAD")
            with col4:
                display_metric_with_icon("📈", "Bénéfice Net", f"{benefice:,.2f} MAD", 
                                       delta_color="inverse" if benefice < 0 else "normal")

            st.markdown("<div class='section-header'>📊 Flux de Trésorerie</div>", unsafe_allow_html=True)
            
            col_tr1, col_tr2 = st.columns([1, 2])
            with col_tr1:
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='subsection-header'>💵 Disponibilités</div>", unsafe_allow_html=True)
                st.metric("Argent Disponible", f"{tresorerie_disponible:,.2f} MAD",
                         delta_color="inverse" if tresorerie_disponible < 0 else "normal")
                st.write("---")
                st.metric("Taux d'utilisation CA", f"{( (cout_achats_ventes + depenses_argent_disponible) / ca_total * 100 if ca_total > 0 else 0):.1f}%")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_tr2:
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                try:
                    categories = ['CA Total', 'Achats', 'Dépenses', 'Disponible']
                    valeurs = [ca_total, -cout_achats_ventes, -depenses_argent_disponible, tresorerie_disponible]
                    mesures = ['absolute', 'relative', 'relative', 'total']
                    
                    fig_cascade = go.Figure(go.Waterfall(
                        name="Trésorerie",
                        orientation="v",
                        measure=mesures,
                        x=categories,
                        textposition="outside",
                        text=[f"{v:+,.0f}" for v in valeurs],
                        y=valeurs,
                        connector={"line": {"color": "#e2e8f0"}},
                        increasing={"marker": {"color": "#10b981"}},
                        decreasing={"marker": {"color": "#ef4444"}},
                        totals={"marker": {"color": "#6366f1"}}
                    ))
                    
                    fig_cascade.update_layout(title="Répartition des Flux de Trésorerie", height=380)
                    st.plotly_chart(apply_custom_chart_style(fig_cascade), use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur graphique flux: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>💳 Trésorerie & Liquidités</div>", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_metric_with_icon("💵", "Argent Disponible", f"{tresorerie_disponible:,.2f} MAD")
            with col2:
                if ca_total > 0:
                    pourcentage_utilise = (cout_achats_ventes / ca_total) * 100
                else:
                    pourcentage_utilise = 0
                display_metric_with_icon("📊", "Taux Dépenses", f"{pourcentage_utilise:.1f}%")
            with col3:
                display_metric_with_icon("📦", "Stock Initial", f"{cout_stock_initial:,.2f} MAD")
            with col4:
                valeur_stock_actuel = stock_actuel['Valeur MAD'].sum() if not stock_actuel.empty else 0
                display_metric_with_icon("🏪", "Stock Actuel", f"{valeur_stock_actuel:,.2f} MAD")

            st.markdown("<div class='section-header'>🏥 Santé Financière</div>", unsafe_allow_html=True)

            try:
                if ca_total > 0:
                    ratio_depenses_ventes = (depenses_argent_disponible / ca_total) * 100
                    ratio_achats_ventes = (cout_achats_ventes / ca_total) * 100
                    ratio_utilisation_argent = ((cout_achats_ventes + depenses_argent_disponible) / ca_total) * 100
                else:
                    ratio_depenses_ventes = ratio_achats_ventes = ratio_utilisation_argent = 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if ratio_utilisation_argent <= 70:
                        couleur = "green"
                        statut = "✅ Bon"
                    elif ratio_utilisation_argent <= 90:
                        couleur = "orange"
                        statut = "⚠️ Modéré"
                    else:
                        couleur = "red"
                        statut = "❌ Risqué"
                    
                    st.markdown(f"""
                    <div style='background-color: {couleur}20; padding: 1rem; border-radius: 10px; border-left: 4px solid {couleur};'>
                        <h4 style='margin: 0; color: {couleur};'>Performance</h4>
                        <p style='margin: 0.5rem 0; font-size: 1.5rem; font-weight: bold;'>{statut}</p>
                        <p style='margin: 0;'>Utilisation: {ratio_utilisation_argent:.1f}% du CA</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric(
                        "📊 Dépenses/CA",
                        f"{ratio_depenses_ventes:.1f}%",
                        help="Pourcentage du CA utilisé pour les dépenses"
                    )
                
                with col3:
                    st.metric(
                        "🛒 Achats/CA",
                        f"{ratio_achats_ventes:.1f}%",
                        help="Pourcentage du CA utilisé pour les achats"
                    )

            except Exception as e:
                st.error(f"Erreur analyse santé: {e}")

            st.markdown("<div class='section-header'>🚨 Alertes & Recommandations</div>", unsafe_allow_html=True)

            alertes = []

            try:
                if tresorerie_disponible < 0:
                    alertes.append({
                        "type": "error",
                        "message": "Trésorerie négative ! L'argent des ventes ne couvre pas les dépenses.",
                        "action": "Réduisez les dépenses ou augmentez les ventes."
                    })
                elif tresorerie_disponible < 1000:
                    alertes.append({
                        "type": "warning", 
                        "message": "Trésorerie faible.",
                        "action": "Surveillez vos dépenses de près."
                    })
                
                if ratio_utilisation_argent > 90:
                    alertes.append({
                        "type": "warning",
                        "message": "Utilisation élevée de l'argent des ventes.",
                        "action": "Envisagez de réduire les dépenses ou d'utiliser d'autres sources."
                    })
                
                if depenses_autre_source > depenses_argent_disponible:
                    alertes.append({
                        "type": "info",
                        "message": "Les dépenses autres dépassent les dépenses de l'argent des ventes.",
                        "action": "Vérifiez la source de ces fonds."
                    })
                
                if alertes:
                    for alerte in alertes:
                        if alerte["type"] == "error":
                            st.error(f"**{alerte['message']}** {alerte['action']}")
                        elif alerte["type"] == "warning":
                            st.warning(f"**{alerte['message']}** {alerte['action']}")
                        else:
                            st.info(f"**{alerte['message']}** {alerte['action']}")
                else:
                    st.success("✅ Aucun problème détecté - Situation financière saine")

            except Exception as e:
                st.error(f"Erreur système d'alertes: {e}")

            # Dans la section "📦 Stock Actuel - Détail" du tableau de bord
            st.markdown("<div class='section-header'>📦 Stock Actuel - Détail avec Prix de Vente</div>", unsafe_allow_html=True)

            if not stock_actuel.empty and 'Valeur MAD' in stock_actuel.columns:
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='subsection-header'>📦 État Global du Stock</div>", unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.dataframe(
                        stock_actuel,
                        use_container_width=True,
                        hide_index=True,
                        height=780, # Ajusté pour l'alignement avec la 6ème carte (Marge Unitaire Moyenne)
                        column_config={
                            "Produit": "Produit",
                            "Quantité en stock": st.column_config.NumberColumn("Quantité", format="%d"),
                            "Prix Achat MAD": st.column_config.NumberColumn("Prix Achat", format="%.2f MAD"),
                            "Coût Revient MAD": st.column_config.NumberColumn("Coût Revient", format="%.2f MAD"),
                            "Prix Vente MAD": st.column_config.NumberColumn("Prix Vente", format="%.2f MAD"),
                            "Valeur MAD": st.column_config.NumberColumn("Valeur Achat", format="%.2f MAD"),
                            "Valeur Vente MAD": st.column_config.NumberColumn("Valeur Vente", format="%.2f MAD")
                        }
                    )
                
                with col2:
                    total_articles = stock_actuel['Quantité en stock'].sum()
                    total_valeur_achat = stock_actuel['Valeur MAD'].sum()
                    total_valeur_vente = stock_actuel['Valeur Vente MAD'].sum()
                    marge_totale = total_valeur_vente - total_valeur_achat
                    marge_pourcentage = (marge_totale / total_valeur_achat * 100) if total_valeur_achat > 0 else 0
                    
                    st.metric("📦 Total Articles", f"{total_articles:,}")
                    st.metric("💰 Valeur Achat", f"{total_valeur_achat:,.2f} MAD")
                    st.metric("💵 Valeur Vente", f"{total_valeur_vente:,.2f} MAD")
                    st.metric("✅ Marge Totale", f"{marge_totale:,.2f} MAD")
                    st.metric("📊 Marge %", f"{marge_pourcentage:.1f}%")
                    
                    # Calcul de la marge unitaire moyenne
                    marge_unitaire_moyenne = stock_actuel['Prix Vente MAD'].mean() - stock_actuel['Prix Achat MAD'].mean()
                    st.metric("📈 Marge Unitaire Moyenne", f"{marge_unitaire_moyenne:.2f} MAD")
                    
                    if not stock_actuel.empty:
                        produit_max = stock_actuel.loc[stock_actuel['Quantité en stock'].idxmax()]
                        st.write(f"**📈 Plus stocké:** {produit_max['Produit']} ({produit_max['Quantité en stock']} unités)")
                
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("📦 Aucun stock disponible pour le moment")
                # Afficher les colonnes disponibles pour debug
                if not stock_actuel.empty:
                    st.write("Colonnes disponibles:", list(stock_actuel.columns))

            st.markdown("<div class='section-header'>📊 Analyses Détaillées</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if ca_total > 0:
                    st.markdown("""
                    <div class='custom-card'>
                        <div class='subsection-header'>📈 Répartition du CA</div>
                    """, unsafe_allow_html=True)
                    fig_ca = px.pie(
                        values=[ca_ventes, ca_prestations],
                        names=['Ventes', 'Prestations'],
                        color_discrete_sequence=['#6366f1', '#10b981'],
                        hole=0.6
                    )
                    fig_ca.update_traces(textposition='outside', textinfo='percent+label')
                    fig_ca.update_layout(height=300)
                    st.plotly_chart(apply_custom_chart_style(fig_ca), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("Aucune donnée de CA disponible")
            
            with col2:
                st.markdown("""
                <div class='custom-card'>
                    <div class='subsection-header'>📊 Évolution des Ventes</div>
                """, unsafe_allow_html=True)
                
                if not ventes_headers.empty:
                    periode_option = st.selectbox(
                        "Période d'analyse",
                        ["Mensuelle", "Hebdomadaire", "Quotidienne"],
                        key="periode_analyse_ventes"
                    )
                    
                    try:
                        ventes_headers['date'] = pd.to_datetime(ventes_headers['date'], errors='coerce')
                        ventes_headers = ventes_headers.dropna(subset=['date'])
                        
                        if not ventes_headers.empty:
                            if periode_option == "Mensuelle":
                                ventes_headers['periode'] = ventes_headers['date'].dt.to_period('M')
                                ventes_agg = ventes_headers.groupby('periode')['total_mad'].sum().reset_index()
                                ventes_agg['date_display'] = ventes_agg['periode'].dt.to_timestamp()
                                xaxis_format = '%b %Y'
                                titre_x = 'Mois'
                                
                            elif periode_option == "Hebdomadaire":
                                ventes_headers['periode'] = ventes_headers['date'].dt.to_period('W')
                                ventes_agg = ventes_headers.groupby('periode')['total_mad'].sum().reset_index()
                                ventes_agg['date_display'] = ventes_agg['periode'].dt.to_timestamp()
                                xaxis_format = '%d %b %Y'
                                titre_x = 'Semaine'
                                
                            else:
                                ventes_agg = ventes_headers.groupby('date')['total_mad'].sum().reset_index()
                                ventes_agg = ventes_agg.rename(columns={'date': 'date_display'})
                                ventes_agg = ventes_agg.sort_values('date_display')
                                xaxis_format = '%d %b %Y'
                                titre_x = 'Date'
                            
                            ventes_agg = ventes_agg.sort_values('date_display')
                            
                            if len(ventes_agg) > 0:
                                fig_ventes = px.line(
                                    ventes_agg, 
                                    x='date_display', 
                                    y='total_mad',
                                    title=f"Évolution des Ventes - {periode_option}",
                                    labels={'date_display': titre_x, 'total_mad': 'CA (MAD)'},
                                    markers=True
                                )
                                
                                fig_ventes.update_traces(
                                    line=dict(color='#3498db', width=3),
                                    marker=dict(size=6, color='#2980b9')
                                )
                                
                                fig_ventes.update_layout(height=350)
                                st.plotly_chart(apply_custom_chart_style(fig_ventes), use_container_width=True)
                                
                                if len(ventes_agg) > 1:
                                    moyenne = ventes_agg['total_mad'].mean()
                                    maximum = ventes_agg['total_mad'].max()
                                    minimum = ventes_agg['total_mad'].min()
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("📊 Moyenne", f"{moyenne:,.0f} MAD")
                                    with col2:
                                        st.metric("📈 Maximum", f"{maximum:,.0f} MAD")
                                    with col3:
                                        st.metric("📉 Minimum", f"{minimum:,.0f} MAD")
                                
                            else:
                                st.info("Aucune donnée après agrégation")
                        else:
                            st.info("Aucune donnée valide")
                            
                    except Exception as e:
                        st.error(f"Erreur: {str(e)}")
                else:
                    st.info("Aucune donnée de vente disponible")
                
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>🏙️ Analyse Géo-Commerciale (Par Ville)</div>", unsafe_allow_html=True)
            
            if not ventes_headers.empty:
                # Préparation des données
                ventes_ville = ventes_headers.copy()
                # Assurer que la colonne ville existe et gérer les valeurs vides
                if 'ville' not in ventes_ville.columns:
                    ventes_ville['ville'] = 'Non spécifiée'
                else:
                    ventes_ville['ville'] = ventes_ville['ville'].fillna('Non spécifiée').replace('', 'Non spécifiée')
                
                ville_stats = ventes_ville.groupby('ville').agg({
                    'total_mad': 'sum',
                    'id': 'count'
                }).reset_index()
                ville_stats.columns = ['Ville', 'Chiffre d\'Affaires', 'Nombre de Ventes']
                ville_stats = ville_stats.sort_values('Chiffre d\'Affaires', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                    st.markdown("<div class='subsection-header'>💰 Chiffre d'Affaires par Ville</div>", unsafe_allow_html=True)
                    fig_ville_bar = px.bar(
                        ville_stats,
                        x='Chiffre d\'Affaires',
                        y='Ville',
                        orientation='h',
                        color='Chiffre d\'Affaires',
                        color_continuous_scale='Blues',
                        labels={'Chiffre d\'Affaires': 'CA (MAD)'}
                    )
                    fig_ville_bar.update_layout(height=500, xaxis_title="CA (MAD)", yaxis_title="")
                    st.plotly_chart(apply_custom_chart_style(fig_ville_bar), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                    st.markdown("<div class='subsection-header'>📈 Répartition par Volume</div>", unsafe_allow_html=True)
                    fig_ville_pie = px.pie(
                        ville_stats,
                        values='Nombre de Ventes',
                        names='Ville',
                        hole=0.6,
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig_ville_pie.update_traces(textinfo='percent+label')
                    fig_ville_pie.update_layout(height=500)
                    st.plotly_chart(apply_custom_chart_style(fig_ville_pie), use_container_width=True)
                    
                    # Métriques intégrées (comme dans l'analyse détaillée)
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        top_ville = ville_stats.iloc[0]['Ville']
                        st.metric("🔝 Top Ville", top_ville)
                    with m_col2:
                        total_ca = ville_stats['Chiffre d\'Affaires'].sum()
                        total_v = ville_stats['Nombre de Ventes'].sum()
                        panier_moyen = total_ca / total_v if total_v > 0 else 0
                        st.metric("🛒 Panier Moyen", f"{panier_moyen:.0f}")
                    with m_col3:
                        nb_villes = len(ville_stats[ville_stats['Ville'] != 'Non spécifiée'])
                        st.metric("📍 Villes", nb_villes)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("🏙️ Aucune donnée géographique disponible pour le moment")

            st.markdown("<div class='section-header'>💵 Détail de la Trésorerie</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class='custom-card'>
                    <div class='subsection-header'>💰 Recettes</div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Ventes:** {ca_ventes:,.2f} MAD")
                st.write(f"**Prestations:** {ca_prestations:,.2f} MAD")
                st.write(f"**Total Recettes:** {ca_total:,.2f} MAD")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class='custom-card'>
                    <div class='subsection-header'>🛒 Dépenses</div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Achats (ventes):** {cout_achats_ventes:,.2f} MAD")
                st.write(f"**Dépenses diverses:** {total_depenses:,.2f} MAD")
                st.write(f"**Dont argent ventes:** {depenses_argent_disponible:,.2f} MAD")
                st.write(f"**Dont autre source:** {depenses_autre_source:,.2f} MAD")
                st.write(f"**Total Dépenses:** {cout_achats_ventes + total_depenses:,.2f} MAD")
                
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>👥 Top Clients</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class='custom-card'>
                    <div class='subsection-header'>🏆 Top Clients Ventes</div>
                """, unsafe_allow_html=True)
                
                if not ventes_headers.empty:
                    top_clients_ventes = ventes_headers.groupby('client')['total_mad'].sum().nlargest(5)
                    for client, montant in top_clients_ventes.items():
                        st.write(f"• **{client}:** {montant:,.2f} MAD")
                else:
                    st.info("Aucun client trouvé")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class='custom-card'>
                    <div class='subsection-header'>🏆 Top Clients Prestations</div>
                """, unsafe_allow_html=True)
                
                if not prestations.empty:
                    top_clients_prestations = prestations.groupby('client')['montant_mad'].sum().nlargest(5)
                    for client, montant in top_clients_prestations.items():
                        st.write(f"• **{client}:** {montant:,.2f} MAD")
                else:
                    st.info("Aucun client trouvé")
                
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>🔄 Gains par Achat</div>", unsafe_allow_html=True)
            
            try:
                gains_df = calculer_gains_par_achat_attribution(conn)
                
                if not gains_df.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_gains = gains_df['gain_net_mad'].sum()
                        display_metric_with_icon("💰", "Total Gains", f"{total_gains:,.2f} MAD")
                    with col2:
                        total_revenus = gains_df['revenus_ventes_mad'].sum()
                        display_metric_with_icon("📈", "Total Revenus", f"{total_revenus:,.2f} MAD")
                    with col3:
                        total_cout = gains_df['cout_total_mad'].sum()
                        display_metric_with_icon("📉", "Total Coûts", f"{total_cout:,.2f} MAD")
                    with col4:
                        marge_moyenne = gains_df['marge_percentage'].mean()
                        display_metric_with_icon("📊", "Marge Moyenne", f"{marge_moyenne:.1f}%")
                    
                    st.markdown("<div class='subsection-header'>📋 Détail des Gains par Achat</div>", unsafe_allow_html=True)
                    
                    gains_display = gains_df.copy()
                    gains_display = gains_display[[
                        'achat_id', 'date_achat', 'fournisseur', 'cout_achat_mad', 
                        'cout_depenses_liees_mad', 'cout_total_mad', 'revenus_ventes_mad', 
                        'gain_net_mad', 'marge_percentage'
                    ]]
                    
                    gains_display.columns = [
                        'ID Achat', 'Date', 'Fournisseur', 'Coût Achat (MAD)', 
                        'Dépenses Liées (MAD)', 'Coût Total (MAD)', 'Revenus (MAD)',
                        'Gain Net (MAD)', 'Marge %'
                    ]
                    
                    st.dataframe(
                        gains_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "ID Achat": st.column_config.NumberColumn("ID", format="%d"),
                            "Date": "Date",
                            "Fournisseur": "Fournisseur",
                            "Coût Achat (MAD)": st.column_config.NumberColumn("Coût Achat", format="%.2f MAD"),
                            "Dépenses Liées (MAD)": st.column_config.NumberColumn("Dépenses", format="%.2f MAD"),
                            "Coût Total (MAD)": st.column_config.NumberColumn("Coût Total", format="%.2f MAD"),
                            "Revenus (MAD)": st.column_config.NumberColumn("Revenus", format="%.2f MAD"),
                            "Gain Net (MAD)": st.column_config.NumberColumn("Gain Net", format="%.2f MAD"),
                            "Marge %": st.column_config.NumberColumn("Marge", format="%.1f%%")
                        }
                    )
                    
                    st.markdown("<div class='subsection-header'>📈 Visualisation des Gains</div>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        top_gains = gains_df.nlargest(10, 'gain_net_mad')
                        fig_top = px.bar(
                            top_gains,
                            x='fournisseur',
                            y='gain_net_mad',
                            title="Top 10 des Achats les Plus Rentables",
                            labels={'fournisseur': 'Fournisseur', 'gain_net_mad': 'Gain Net (MAD)'}
                        )
                        st.plotly_chart(fig_top, use_container_width=True)
                    
                    with col2:
                        fig_marge = px.histogram(
                            gains_df,
                            x='marge_percentage',
                            title="Distribution des Marges",
                            labels={'marge_percentage': 'Marge (%)'}
                        )
                        st.plotly_chart(fig_marge, use_container_width=True)
                    
                else:
                    st.info("📊 Aucune donnée de gain disponible pour le moment")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul des gains: {e}")

        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des rapports: {e}")

    elif menu == "🔧 Devises":
        display_view_header("Gestion des Devises", "Configurez et suivez les taux de change", "🔧")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Taux Actuels</div>", unsafe_allow_html=True)
                
                today = date.today().isoformat()
                for devise in [d for d in SUPPORTED_DEVISES if d != "MAD"]:
                    with st.container():
                        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                        taux_row = conn.execute(
                            "SELECT taux, source FROM taux_change WHERE devise = ? AND date = ?",
                            (devise, today)
                        ).fetchone()
                        
                        if taux_row:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.metric(
                                    label=f"💱 {devise} → MAD",
                                    value=f"{taux_row['taux']:.4f}",
                                    delta=f"Source: {taux_row['source']}"
                                )
                            with col2:
                                if st.button("🔄", key=f"update_{devise}"):
                                    with st.spinner(f"Mise à jour {devise}..."):
                                        nouveau_taux = get_taux_depuis_api(devise)
                                        if nouveau_taux:
                                            sauvegarder_taux(conn, devise, nouveau_taux, "api")
                                            display_success_message(f"Taux {devise} mis à jour: {nouveau_taux:.4f}")
                                            st.rerun()
                                        else:
                                            display_warning_message(f"Échec mise à jour {devise}")
                        else:
                            taux_defaut = taux_par_defaut(devise)
                            st.metric(
                                label=f"💱 {devise} → MAD",
                                value=f"{taux_defaut:.4f}",
                                delta="Source: défaut"
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique Détaillé</div>", unsafe_allow_html=True)
                
                try:
                    historique_taux = pd.read_sql(
                        "SELECT * FROM taux_change ORDER BY date DESC, devise", 
                        conn
                    )
                    if not historique_taux.empty:
                        st.markdown("<div class='subsection-header'>📈 Évolution des Taux</div>", unsafe_allow_html=True)
                        
                        st.dataframe(
                            historique_taux,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("📊 Aucun historique de taux disponible")
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement de l'historique: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "👥 Clients & Fournisseurs":
        display_view_header("Clients & Fournisseurs", "Analysez votre portefeuille clients et fournisseurs", "👥")
        
        tab_clients, tab_fournisseurs = st.tabs(["👤 Clients", "🏢 Fournisseurs"])
        
        with tab_clients:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Analyse des Clients</div>", unsafe_allow_html=True)
                
                try:
                    ventes_par_client = get_ventes_par_client(conn)
                    prestations_par_client = get_prestations_par_client(conn)
                    
                    if not ventes_par_client.empty or not prestations_par_client.empty:
                        clients_data = pd.DataFrame()
                        
                        if not ventes_par_client.empty:
                            clients_data = ventes_par_client[['client', 'total_mad']].rename(columns={'total_mad': 'ventes_total'})
                        
                        if not prestations_par_client.empty:
                            if clients_data.empty:
                                clients_data = prestations_par_client[['client', 'total_mad']].rename(columns={'total_mad': 'prestations_total'})
                            else:
                                prestations_temp = prestations_par_client[['client', 'total_mad']].rename(columns={'total_mad': 'prestations_total'})
                                clients_data = pd.merge(clients_data, prestations_temp, on='client', how='outer')
                        
                        clients_data['ventes_total'] = clients_data['ventes_total'].fillna(0)
                        clients_data['prestations_total'] = clients_data['prestations_total'].fillna(0)
                        clients_data['total_general'] = clients_data['ventes_total'] + clients_data['prestations_total']
                        
                        st.markdown("<div class='subsection-header'>📊 Classement des Clients</div>", unsafe_allow_html=True)
                        
                        clients_display = clients_data.sort_values('total_general', ascending=False)
                        clients_display = clients_display[['client', 'ventes_total', 'prestations_total', 'total_general']]
                        clients_display.columns = ['Client', 'Ventes (MAD)', 'Prestations (MAD)', 'Total Général (MAD)']
                        
                        st.dataframe(
                            clients_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Client": "Client",
                                "Ventes (MAD)": st.column_config.NumberColumn("Ventes", format="%.2f MAD"),
                                "Prestations (MAD)": st.column_config.NumberColumn("Prestations", format="%.2f MAD"),
                                "Total Général (MAD)": st.column_config.NumberColumn("Total", format="%.2f MAD")
                            }
                        )
                        
                        st.markdown("<div class='subsection-header'>🔍 Détail par Client</div>", unsafe_allow_html=True)
                        
                        selected_client = st.selectbox(
                            "Sélectionner un client pour voir le détail",
                            clients_data['client'].unique(),
                            key="select_client_detail"
                        )
                        
                        if selected_client:
                            detail_client = get_detail_client(conn, selected_client)
                            
                            if not detail_client.empty:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("💰 Total Ventes", 
                                             f"{detail_client[detail_client['type'] == 'Vente']['montant'].sum():.2f} MAD")
                                with col2:
                                    st.metric("🎯 Total Prestations", 
                                             f"{detail_client[detail_client['type'] == 'Prestation']['montant'].sum():.2f} MAD")
                                
                                st.markdown("#### 📋 Historique des transactions")
                                st.dataframe(
                                    detail_client,
                                    use_container_width=True,
                                    hide_index=True
                                )
                            else:
                                st.info(f"Aucune transaction trouvée pour {selected_client}")
                    
                    else:
                        st.info("📊 Aucun client trouvé dans la base de données")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement des données clients: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab_fournisseurs:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Analyse des Fournisseurs</div>", unsafe_allow_html=True)
                
                try:
                    achats_par_fournisseur = get_achats_par_fournisseur(conn)
                    
                    if not achats_par_fournisseur.empty:
                        st.markdown("<div class='subsection-header'>📊 Classement des Fournisseurs</div>", unsafe_allow_html=True)
                        
                        fournisseurs_display = achats_par_fournisseur.copy()
                        fournisseurs_display = fournisseurs_display[['fournisseur', 'nb_achats', 'total_mad', 'moyenne_achat']]
                        fournisseurs_display.columns = ['Fournisseur', 'Nb Achats', 'Total (MAD)', 'Moyenne (MAD)']
                        
                        st.dataframe(
                            fournisseurs_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Fournisseur": "Fournisseur",
                                "Nb Achats": st.column_config.NumberColumn("Achats", format="%d"),
                                "Total (MAD)": st.column_config.NumberColumn("Total", format="%.2f MAD"),
                                "Moyenne (MAD)": st.column_config.NumberColumn("Moyenne", format="%.2f MAD")
                            }
                        )
                        
                        st.markdown("<div class='subsection-header'>🔍 Détail par Fournisseur</div>", unsafe_allow_html=True)
                        
                        selected_fournisseur = st.selectbox(
                            "Sélectionner un fournisseur pour voir le détail",
                            achats_par_fournisseur['fournisseur'].unique(),
                            key="select_fournisseur_detail"
                        )
                        
                        if selected_fournisseur:
                            detail_fournisseur = get_detail_fournisseur(conn, selected_fournisseur)
                            
                            if not detail_fournisseur.empty:
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("📦 Total Achats", 
                                             f"{detail_fournisseur['montant'].sum():.2f} MAD")
                                with col2:
                                    st.metric("🔢 Nombre d'achats", 
                                             f"{len(detail_fournisseur)}")
                                with col3:
                                    st.metric("📊 Moyenne par achat", 
                                             f"{detail_fournisseur['montant'].mean():.2f} MAD")
                                
                                st.markdown("#### 📋 Historique des achats")
                                st.dataframe(
                                    detail_fournisseur,
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                if len(detail_fournisseur) > 1:
                                    st.markdown("#### 📈 Évolution des achats")
                                    detail_fournisseur['date'] = pd.to_datetime(detail_fournisseur['date'])
                                    fig_achats = px.line(
                                        detail_fournisseur, 
                                        x='date', 
                                        y='montant',
                                        title=f"Achats chez {selected_fournisseur}",
                                        markers=True
                                    )
                                    fig_achats.update_layout(height=300)
                                    st.plotly_chart(fig_achats, use_container_width=True)
                            else:
                                st.info(f"Aucun achat trouvé pour {selected_fournisseur}")
                    
                    else:
                        st.info("📊 Aucun fournisseur trouvé dans la base de données")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement des données fournisseurs: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📅 Hebdo":
        display_view_header("Suivi Hebdomadaire", "Suivez le fond de caisse et les salaires", "📅")
        
        tab_h1, tab_h2, tab_h3 = st.tabs(["➕ Nouveau Suivi", "🗂️ Historique", "✏️ Modifier"])
        
        with tab_h1:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Enregistrer un nouveau suivi</div>", unsafe_allow_html=True)
                
                with st.form("form_hebdo", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        today = date.today()
                        monday = today - timedelta(days=today.weekday())
                        date_debut = st.date_input("📅 Semaine du (Lundi)", value=monday)
                        fond = st.number_input("💰 Fond de caisse", min_value=0.0, value=0.0, step=10.0)
                    with col2:
                        sal1 = st.number_input("💵 Salaire 1", min_value=0.0, value=0.0, step=10.0)
                        sal2 = st.number_input("💵 Salaire 2", min_value=0.0, value=0.0, step=10.0)
                    
                    notes = st.text_area("📝 Notes", placeholder="Observations éventuelles...")
                    
                    if st.form_submit_button("✅ Enregistrer le suivi", use_container_width=True):
                        try:
                            with conn:
                                conn.execute(
                                    "INSERT INTO hebdo (date_debut, fond_de_caisse, salaire_1, salaire_2, notes) VALUES (?, ?, ?, ?, ?)",
                                    (date_debut.isoformat(), float(fond), float(sal1), float(sal2), notes)
                                )
                            display_success_message("Suivi hebdomadaire enregistré avec succès !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'enregistrement: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_h2:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Historique Hebdomadaire</div>", unsafe_allow_html=True)
                
                try:
                    hebdo_df = pd.read_sql("SELECT * FROM hebdo ORDER BY date_debut DESC", conn)
                    if not hebdo_df.empty:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            total_fond = hebdo_df['fond_de_caisse'].sum()
                            display_metric_with_icon("💰", "Total Fond de Caisse", f"{total_fond:,.2f} MAD")
                        with col2:
                            total_salaires = hebdo_df['salaire_1'].sum() + hebdo_df['salaire_2'].sum()
                            display_metric_with_icon("💵", "Total Salaires", f"{total_salaires:,.2f} MAD")
                        with col3:
                            nb_semaines = len(hebdo_df)
                            display_metric_with_icon("📅", "Semaines Suivies", f"{nb_semaines}")

                        st.markdown("<div class='subsection-header'>📋 Liste des suivis</div>", unsafe_allow_html=True)
                        
                        display_df = hebdo_df.copy()
                        display_df = display_df[['id', 'date_debut', 'fond_de_caisse', 'salaire_1', 'salaire_2', 'notes']]
                        display_df.columns = ['ID', 'Date Début', 'Fond de Caisse', 'Salaire 1', 'Salaire 2', 'Notes']
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "ID": st.column_config.NumberColumn("ID", format="%d"),
                                "Date Début": "Semaine du",
                                "Fond de Caisse": st.column_config.NumberColumn("Fond", format="%.2f MAD"),
                                "Salaire 1": st.column_config.NumberColumn("S1", format="%.2f MAD"),
                                "Salaire 2": st.column_config.NumberColumn("S2", format="%.2f MAD")
                            }
                        )
                    else:
                        st.info("📊 Aucun suivi enregistré pour le moment")
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab_h3:
            with st.container():
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Modifier ou Supprimer</div>", unsafe_allow_html=True)
                
                try:
                    hebdo_list = pd.read_sql("SELECT * FROM hebdo ORDER BY date_debut DESC", conn)
                    if not hebdo_list.empty:
                        selected_h_id = st.selectbox(
                            "Sélectionner une semaine",
                            hebdo_list['id'].tolist(),
                            format_func=lambda x: f"Semaine du {hebdo_list[hebdo_list['id'] == x].iloc[0]['date_debut']}"
                        )
                        
                        if selected_h_id:
                            h_data = hebdo_list[hebdo_list['id'] == selected_h_id].iloc[0]
                            with st.form(f"modify_hebdo_{selected_h_id}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_date = st.date_input("📅 Date", value=pd.to_datetime(h_data['date_debut']).date())
                                    new_fond = st.number_input("💰 Fond", value=float(h_data['fond_de_caisse']))
                                with col2:
                                    new_sal1 = st.number_input("💵 Salaire 1", value=float(h_data['salaire_1']))
                                    new_sal2 = st.number_input("💵 Salaire 2", value=float(h_data['salaire_2']))
                                
                                new_notes = st.text_area("📝 Notes", value=h_data['notes'] or "")
                                
                                col_b1, col_b2 = st.columns(2)
                                with col_b1:
                                    if st.form_submit_button("💾 Mettre à jour"):
                                        with conn:
                                            conn.execute(
                                                "UPDATE hebdo SET date_debut = ?, fond_de_caisse = ?, salaire_1 = ?, salaire_2 = ?, notes = ? WHERE id = ?",
                                                (new_date.isoformat(), new_fond, new_sal1, new_sal2, new_notes, selected_h_id)
                                            )
                                        display_success_message("Suivi mis à jour !")
                                        st.rerun()
                                with col_b2:
                                    if st.form_submit_button("🗑️ Supprimer"):
                                        with conn:
                                            conn.execute("DELETE FROM hebdo WHERE id = ?", (selected_h_id,))
                                        display_success_message("Suivi supprimé !")
                                        st.rerun()
                    else:
                        st.info("📊 Aucun suivi à modifier")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la modification: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

    conn.close()

if __name__ == "__main__":
    main()