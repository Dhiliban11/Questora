"""
================================================================================
EXPLORER QUEST: LYON EDITION (Édition Lyon) — Pure Streamlit Architecture
Stack: Streamlit | streamlit-geolocation | geopy (Nominatim) |
       Google GenAI (`google-genai`) | SQLite3 | ReportLab | Pillow
================================================================================
"""

import os
import io
import json
import uuid
import base64
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Any, Optional

import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
from PIL import Image
from pydantic import BaseModel, Field

# LOGIC: Import Google GenAI SDK (`google-genai`)
from google import genai
from google.genai import types

# LOGIC: Import ReportLab components for formatted PDF Album export
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit


# ==============================================================================
# 1. APPLICATION CONSTANTS, TIERS, THEMES & CUSTOM GOOGLE FONTS
# ==============================================================================

# LOGIC: Local SQLite database and photo storage directory
DB_PATH = "explorer_lyon.db"
PHOTO_DIR = "explorer_photos"

# LOGIC: Scoring rules and Explorer Tier progression
RIDDLE_POINTS = 50
QUEST_POINTS = 200

EXPLORER_TIERS = [
    {"name": "Rookie Explorer", "fr": "Explorateur Débutant", "min_pts": 0, "badge": "🧭"},
    {"name": "Adventurer", "fr": "Aventurier du Rhône", "min_pts": 200, "badge": "⚔️"},
    {"name": "Elite Explorer", "fr": "Explorateur d'Élite", "min_pts": 500, "badge": "🏛️"},
    {"name": "Premium Legend", "fr": "Légende de Lugdunum", "min_pts": 900, "badge": "👑"},
]

# UI EDITING: 10 Custom Google Fonts mapped to Web CSS & ReportLab PDF Type1 fonts
CUSTOM_FONTS: Dict[str, Dict[str, str]] = {
    "Cinzel": {
        "css": "'Cinzel', serif",
        "pdf_title": "Times-Bold",
        "pdf_body": "Times-Roman",
        "vibe": "Classical Roman & Cathedral Stone",
    },
    "Playfair Display": {
        "css": "'Playfair Display', serif",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Times-Roman",
        "vibe": "French Editorial & Haute Couture",
    },
    "Space Grotesk": {
        "css": "'Space Grotesk', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Modern Architectural Geometry",
    },
    "Caveat": {
        "css": "'Caveat', cursive",
        "pdf_title": "Times-Italic",
        "pdf_body": "Times-Italic",
        "vibe": "Handwritten Field Notes",
    },
    "Lobster": {
        "css": "'Lobster', cursive",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Helvetica",
        "vibe": "Vintage Bistro Signage",
    },
    "Montserrat": {
        "css": "'Montserrat', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Clean Contemporary Travelogue",
    },
    "Pacifico": {
        "css": "'Pacifico', cursive",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Helvetica",
        "vibe": "Postcard & Riviera Leisure",
    },
    "Oswald": {
        "css": "'Oswald', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Bold Expedition Headlines",
    },
    "Syne": {
        "css": "'Syne', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Avant-Garde Confluence Art",
    },
    "Special Elite": {
        "css": "'Special Elite', monospace",
        "pdf_title": "Courier-Bold",
        "pdf_body": "Courier",
        "vibe": "Secret Traboule Typewriter Dossier",
    },
}

# UI EDITING: 10 Album Visual Themes synchronized between Live Studio Preview & PDF Export
ALBUM_THEMES: Dict[str, Dict[str, str]] = {
    "Vintage Map": {
        "bg": "#F4ECD8",
        "card_bg": "#FAF4E6",
        "text": "#3B2F2F",
        "accent": "#8B4513",
        "secondary": "#C19A6B",
        "border": "2px dashed #8B4513",
        "tag": "Cartographie Ancienne",
    },
    "Cyberpunk Neon": {
        "bg": "#0D0221",
        "card_bg": "#190B36",
        "text": "#F0F8FF",
        "accent": "#00F5D4",
        "secondary": "#FF007F",
        "border": "2px solid #00F5D4",
        "tag": "Lumières Futuristes",
    },
    "Minimalist Journal": {
        "bg": "#FFFFFF",
        "card_bg": "#F8F9FA",
        "text": "#1A1A1A",
        "accent": "#495057",
        "secondary": "#ADB5BD",
        "border": "1px solid #DEE2E6",
        "tag": "Épure Contemporaine",
    },
    "Golden Hour": {
        "bg": "#FFF3E0",
        "card_bg": "#FFE0B2",
        "text": "#4E342E",
        "accent": "#E65100",
        "secondary": "#FFB300",
        "border": "2px solid #FB8C00",
        "tag": "Crépuscule sur la Saône",
    },
    "Editorial Magazine": {
        "bg": "#F7F5F0",
        "card_bg": "#FFFFFF",
        "text": "#111111",
        "accent": "#9E2A2B",
        "secondary": "#D4A373",
        "border": "3px double #111111",
        "tag": "Revue Lyonnaise",
    },
    "Retro Stamp": {
        "bg": "#EFE6D5",
        "card_bg": "#FFFDF9",
        "text": "#2B3A42",
        "accent": "#C0392B",
        "secondary": "#2980B9",
        "border": "3px dotted #C0392B",
        "tag": "Carte Postale 1950",
    },
    "Dark Elegance": {
        "bg": "#121212",
        "card_bg": "#1E1E24",
        "text": "#EAE0D5",
        "accent": "#D4AF37",
        "secondary": "#8C7853",
        "border": "2px solid #D4AF37",
        "tag": "Nocturne Soie & Or",
    },
    "Pop Art": {
        "bg": "#FFF200",
        "card_bg": "#FFFFFF",
        "text": "#000000",
        "accent": "#FF1E56",
        "secondary": "#00A8E8",
        "border": "3px solid #000000",
        "tag": "Couleurs Vives",
    },
    "Botanical Travel": {
        "bg": "#EDF3EC",
        "card_bg": "#F9FCF8",
        "text": "#1E352F",
        "accent": "#2D6A4F",
        "secondary": "#74C69D",
        "border": "2px solid #52B788",
        "tag": "Parc de la Tête d'Or",
    },
    "Classic Blueprint": {
        "bg": "#0F2C59",
        "card_bg": "#163A70",
        "text": "#F8F9FA",
        "accent": "#90E0EF",
        "secondary": "#48CAE4",
        "border": "2px dashed #90E0EF",
        "tag": "Architecture & Plans",
    },
}


# ==============================================================================
# 2. LYON CULTURAL GUIDE, REAL-LIFE QUESTS & COUPON CATALOG
# ==============================================================================

# LOGIC: Lyon Cultural Dossier (History, Traboules, Architecture, Bouchons, Festivals)
LYON_CULTURAL_TOPICS: Dict[str, Dict[str, Any]] = {
    "Histoire (Fourvière & Presqu'île) | History": {
        "fr": "Fondée en 43 av. J.-C. sous le nom de Lugdunum sur la colline de Fourvière, Lyon fut la capitale des Trois Gaules avant de rayonner à la Renaissance sur la Presqu'île grâce à l'imprimerie et la soie.",
        "en": "Founded in 43 BC as Lugdunum on Fourvière Hill, Lyon served as capital of the Three Gauls before flourishing across the Presqu'île during the Renaissance through printing and silk weaving.",
        "facts": [
            "43 BC: Roman colony Lugdunum founded by Lucius Munatius Plancus.",
            "1536: King François I grants Lyon a silk monopoly, giving rise to the Canut weavers.",
            "1943: Jean Moulin unifies the French Resistance across Lyon's secret courtyards.",
        ],
    },
    "Les Traboules & Secrets | Cool Facts": {
        "fr": "Du latin 'trans ambulare' (traverser), plus de 400 traboules relient les rues du Vieux Lyon et de la Croix-Rousse à travers des cours Renaissance pour protéger les étoffes de soie de la pluie.",
        "en": "From Latin 'trans ambulare' (to walk through), over 400 hidden traboule passages connect streets in Vieux Lyon and Croix-Rousse through Renaissance courtyards to shield silk bolts from rain.",
        "facts": [
            "La Longue Traboule (54 Rue Saint-Jean to 27 Rue du Bœuf) crosses four separate buildings.",
            "Cour des Voraces in Croix-Rousse features a dramatic six-story open stone staircase.",
            "Cinema was invented in Lyon in 1895 by Auguste & Louis Lumière on Rue du Premier-Film.",
        ],
    },
    "Architecture & Fresques | Architecture": {
        "fr": "Classée au patrimoine mondial de l'UNESCO, Lyon superpose amphithéâtres romains, tours Renaissance italiennes, avenues haussmanniennes et l'architecture futuriste de la Confluence.",
        "en": "A UNESCO World Heritage site, Lyon layers Roman amphitheaters, Italianate Renaissance spiral towers, Haussmannian boulevards, and futuristic glass structures at La Confluence.",
        "facts": [
            "Basilique Notre-Dame de Fourvière: Romano-Byzantine landmark nicknamed the 'upside-down elephant'.",
            "Mur des Canuts: Europe's largest trompe-l'œil mural (1,200 m²) in Croix-Rousse.",
            "Musée des Confluences: Crystal-and-steel cloud at the meeting of the Rhône and Saône rivers.",
        ],
    },
    "Bouchons Lyonnais | Top Gastronomy": {
        "fr": "Sacrée 'Capitale mondiale de la gastronomie' en 1935, Lyon perpétue l'art des authentiques Bouchons Lyonnais aux nappes à carreaux rouges et blancs.",
        "en": "Crowned 'World Capital of Gastronomy' in 1935, Lyon celebrates convivial heritage cuisine inside certified Bouchons Lyonnais with red-and-white checkered tablecloths.",
        "facts": [
            "Café Comptoir Abel (Est. 1928) — Iconic Quenelle de Brochet in creamy crayfish Nantua sauce.",
            "Daniel et Denise — Run by MOF Chef Joseph Viola; renowned for World-Champion Pâté-Croûte.",
            "Les Halles de Lyon Paul Bocuse — Indoor culinary temple for Saint-Marcellin & Rosette de Lyon.",
        ],
    },
    "Fête des Lumières | Festivals": {
        "fr": "Chaque 8 décembre depuis 1852, les Lyonnais illuminent leurs fenêtres de lumignons colorés et la ville devient une galerie monumentale de projections lumineuses.",
        "en": "Every December 8th since 1852, residents place lit 'lumignon' candles on windowsills while Lyon transforms into a city-wide festival of monumental light projections.",
        "facts": [
            "Place des Terreaux & Fourvière host world-renowned 3D architectural light mapping.",
            "Nuits de Fourvière (June–July): Music, dance, and theater inside the Roman amphitheater.",
            "Nuits Sonores (May): Electronic music & digital arts festival across industrial landmarks.",
        ],
    },
}

# LOGIC: Iconic Lyon Landmark Photo Cards (No hardcoded Explorer GPS coordinates)
LYON_LANDMARKS = [
    {
        "name_fr": "Basilique Notre-Dame de Fourvière",
        "name_en": "Basilica of Notre-Dame de Fourvière",
        "district": "Fourvière (5e)",
        "desc_fr": "Chef-d'œuvre romano-byzantin dominant la colline qui prie avec vue panoramique sur Lyon.",
        "desc_en": "Romano-Byzantine masterpiece crowning the 'hill that prays' with sweeping views over Lyon.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Basilique_Notre-Dame_de_Fourvi%C3%A8re_Lyon.jpg/800px-Basilique_Notre-Dame_de_Fourvi%C3%A8re_Lyon.jpg",
    },
    {
        "name_fr": "Cour des Voraces & Traboules",
        "name_en": "Cour des Voraces & Secret Traboules",
        "district": "Croix-Rousse / Vieux Lyon",
        "desc_fr": "Passages couverts historiques des soyeux Canuts et haut lieu de la Résistance.",
        "desc_en": "Historic covered passageways of the Canut silk weavers and French Resistance.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Cour_des_Voraces_Lyon.jpg/800px-Cour_des_Voraces_Lyon.jpg",
    },
    {
        "name_fr": "Place Bellecour & Presqu'île",
        "name_en": "Bellecour Square & The Peninsula",
        "district": "Presqu'île (2e)",
        "desc_fr": "Cœur monumental entre Rhône et Saône autour de la statue équestre de Louis XIV.",
        "desc_en": "Monumental pedestrian heart between the Rhône and Saône rivers around Louis XIV.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Place_Bellecour_Lyon_2019.jpg/800px-Place_Bellecour_Lyon_2019.jpg",
    },
    {
        "name_fr": "Musée des Confluences",
        "name_en": "Confluences Science Museum",
        "district": "La Confluence (2e)",
        "desc_fr": "Architecture de cristal et d'acier à la jonction exacte du Rhône et de la Saône.",
        "desc_en": "Crystal-and-steel architecture poised at the exact confluence of the Rhône and Saône.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Mus%C3%A9e_des_Confluences_-_Lyon.jpg/800px-Mus%C3%A9e_des_Confluences_-_Lyon.jpg",
    },
    {
        "name_fr": "Parc de la Tête d'Or",
        "name_en": "Golden Head Park & Botanical Conservatory",
        "district": "6e Arrondissement",
        "desc_fr": "Plus grand parc urbain de France avec son lac, sa roseraie et ses serres monumentales.",
        "desc_en": "France's largest urban park featuring a boating lake, rose garden, and 19th-century glasshouses.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Serres_du_parc_de_la_T%C3%AAte_d%27Or.jpg/800px-Serres_du_parc_de_la_T%C3%AAte_d%27Or.jpg",
    },
    {
        "name_fr": "Théâtre Antique de Lugdunum",
        "name_en": "Ancient Roman Theatre of Lugdunum",
        "district": "Fourvière (5e)",
        "desc_fr": "Construit en 15 av. J.-C. sous Auguste, cœur de la capitale romaine des Trois Gaules.",
        "desc_en": "Built in 15 BC under Emperor Augustus, heart of the Roman capital of the Three Gauls.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Th%C3%A9%C3%A2tre_antique_de_Fourvi%C3%A8re_Lyon.jpg/800px-Th%C3%A9%C3%A2tre_antique_de_Fourvi%C3%A8re_Lyon.jpg",
    },
]

# LOGIC: 3 Real-Life Photo Quests (200 pts each — Unlocked when live mobile GPS verifies Lyon, France)
REAL_LIFE_QUESTS = [
    {
        "id": "Q01",
        "title_fr": "Le Passage Secret des Canuts",
        "title_en": "Locate a Hidden Traboule Passage",
        "desc_fr": "Trouvez une traboule authentique dans le Vieux Lyon (ex: 54 Rue Saint-Jean) ou la Croix-Rousse, capturez une photo de sa cour intérieure et consignez votre position GPS.",
        "desc_en": "Locate an authentic hidden Traboule passage in Vieux Lyon (e.g., 54 Rue Saint-Jean) or Croix-Rousse, capture a photo of its courtyard, and log your live GPS location.",
        "points": QUEST_POINTS,
    },
    {
        "id": "Q02",
        "title_fr": "Panorama depuis la Colline qui Prie",
        "title_en": "Fourvière Esplanade Skyline Capture",
        "desc_fr": "Montez sur l'esplanade de Fourvière, photographiez les toits de Lyon et la Presqu'île, puis validez votre relevé GPS.",
        "desc_en": "Stand on the Fourvière esplanade, capture a photo overlooking Lyon's rooftops and the Presqu'île, and log your live GPS coordinates.",
        "points": QUEST_POINTS,
    },
    {
        "id": "Q03",
        "title_fr": "L'Étreinte du Rhône et de la Saône",
        "title_en": "The Confluence River Tip Expedition",
        "desc_fr": "Rejoignez la pointe sud de la Presqu'île derrière le Musée des Confluences, photographiez la rencontre des deux fleuves et consignez votre GPS.",
        "desc_en": "Reach the southern tip of the Presqu'île behind Musée des Confluences, capture the merging of both rivers, and log your live GPS.",
        "points": QUEST_POINTS,
    },
]

# LOGIC: Real-World Lyon Coupon Store Catalog
COUPON_CATALOG = [
    {
        "id": "CPN-BOUCHON-01",
        "partner": "Bouchon Lyonnais Daniel et Denise",
        "category": "Gastronomie / Dining",
        "offer_fr": "Apéritif Kir Lyonnais + Pâté-Croûte Champion du Monde offert pour tout menu",
        "offer_en": "Complimentary Kir Lyonnais Aperitif & World-Champion Pâté-Croûte with any set menu",
        "cost": 150,
        "district": "Saint-Jean / Créqui",
    },
    {
        "id": "CPN-CHOCO-02",
        "partner": "Maison Bernachon Chocolatier",
        "category": "Chocolaterie / Artisan",
        "offer_fr": "Un Palet d'Or signature & dégustation de chocolat chaud rue Franklin",
        "offer_en": "Signature Palet d'Or gold-leaf truffle & hot chocolate tasting on Rue Franklin",
        "cost": 100,
        "district": "Presqu'île (2e)",
    },
    {
        "id": "CPN-PRALINE-03",
        "partner": "Boulangerie Pralus Vieux Lyon",
        "category": "Pâtisserie / Bakery",
        "offer_fr": "Une Praluline individuelle aux pralines roses de Lyon offerte",
        "offer_en": "One freshly baked individual Praluline pink-praline brioche",
        "cost": 80,
        "district": "Rue Saint-Jean (5e)",
    },
    {
        "id": "CPN-MUSEE-04",
        "partner": "Musée Cinéma et Miniature",
        "category": "Culture & Musées",
        "offer_fr": "Entrée Coupe-File Explorer (-30%) dans la Maison des Avocats",
        "offer_en": "30% Off Skip-the-Line Explorer Admission inside the historic Maison des Avocats",
        "cost": 200,
        "district": "Vieux Lyon (5e)",
    },
    {
        "id": "CPN-SOIE-05",
        "partner": "Atelier de Soierie Croix-Rousse",
        "category": "Artisanat / Silk",
        "offer_fr": "Démonstration privée sur métier Jacquard + Carré de soie pochette (-25%)",
        "offer_en": "Private Jacquard loom weaving demo + 25% off a hand-printed Lyon silk pocket square",
        "cost": 250,
        "district": "Croix-Rousse (1er)",
    },
    {
        "id": "CPN-HOTEL-06",
        "partner": "Hôtel Cour des Loges Lyon",
        "category": "Hôtellerie / Boutique Stay",
        "offer_fr": "Surclassement Renaissance & Accès Spa Romain pour un séjour de 2 nuits",
        "offer_en": "Renaissance Suite Upgrade & Roman Thermal Baths access on a 2-night stay",
        "cost": 600,
        "district": "Rue du Bœuf (5e)",
    },
]


# ==============================================================================
# 3. PYDANTIC STRUCTURED OUTPUT SCHEMA (STRICT LYON-ONLY AI RIDDLES)
# ==============================================================================

class LyonRiddleItem(BaseModel):
    """# LOGIC: Structured schema for each AI-generated Lyon riddle."""
    id: str = Field(description="Unique identifier from R01 to R12")
    spot: str = Field(description="Specific Lyon landmark, district, traboule, or historical topic")
    question_fr: str = Field(description="Challenging riddle or trivia question in French")
    question_en: str = Field(description="English translation of the riddle or trivia question")
    options: List[str] = Field(description="4 distinct multiple-choice answer options")
    answer: str = Field(description="Exact text matching the correct option from options")
    hint: str = Field(description="Helpful clue in English grounded in Lyon history or geography")


class LyonRiddleCollection(BaseModel):
    """# LOGIC: Top-level JSON response schema enforcing 12 Lyon-only riddles."""
    riddles: List[LyonRiddleItem] = Field(
        description="Exactly 12 unique, challenging riddles and trivia questions exclusively about Lyon, France."
    )


# ==============================================================================
# 4. SQLITE DATABASE PERSISTENCE (`explorer_lyon.db`)
# ==============================================================================

def init_db() -> None:
    """
    # LOGIC: Auto-initialize `explorer_lyon.db` with `explorer_profile` and
    `diary_entries` tables on app startup.
    """
    os.makedirs(PHOTO_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS explorer_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            explorer_name TEXT NOT NULL DEFAULT 'Explorer',
            total_points INTEGER NOT NULL DEFAULT 0,
            current_tier TEXT NOT NULL DEFAULT 'Rookie Explorer',
            solved_riddles TEXT NOT NULL DEFAULT '[]',
            solved_quests TEXT NOT NULL DEFAULT '[]',
            redeemed_coupons TEXT NOT NULL DEFAULT '[]'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            lyon_spot TEXT NOT NULL,
            diary_text TEXT NOT NULL,
            image_path TEXT,
            album_theme TEXT NOT NULL DEFAULT 'Vintage Map',
            album_font TEXT NOT NULL DEFAULT 'Playfair Display'
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM explorer_profile WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO explorer_profile
            (id, explorer_name, total_points, current_tier, solved_riddles, solved_quests, redeemed_coupons)
            VALUES (1, 'Explorer', 0, 'Rookie Explorer', '[]', '[]', '[]')
            """
        )

    conn.commit()
    conn.close()


def calculate_tier(total_points: int) -> Dict[str, Any]:
    """# LOGIC: Calculate Explorer Tier rank from total earned points."""
    current = EXPLORER_TIERS[0]
    next_tier = None
    for idx, tier in enumerate(EXPLORER_TIERS):
        if total_points >= tier["min_pts"]:
            current = tier
            next_tier = EXPLORER_TIERS[idx + 1] if idx + 1 < len(EXPLORER_TIERS) else None
    return {"current": current, "next": next_tier}


def load_explorer_profile() -> Dict[str, Any]:
    """# LOGIC: Load saved Explorer profile stats and achievements from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM explorer_profile WHERE id = 1").fetchone()
    conn.close()

    solved_riddles = json.loads(row["solved_riddles"] or "[]")
    solved_quests = json.loads(row["solved_quests"] or "[]")
    redeemed_coupons = json.loads(row["redeemed_coupons"] or "[]")
    total_points = int(row["total_points"])
    spent_points = sum(int(c.get("cost", 0)) for c in redeemed_coupons)
    tier_info = calculate_tier(total_points)

    return {
        "explorer_name": row["explorer_name"],
        "total_points": total_points,
        "spent_points": spent_points,
        "available_points": max(0, total_points - spent_points),
        "current_tier": tier_info["current"]["name"],
        "tier_fr": tier_info["current"]["fr"],
        "tier_badge": tier_info["current"]["badge"],
        "next_tier": tier_info["next"],
        "solved_riddles": solved_riddles,
        "solved_quests": solved_quests,
        "redeemed_coupons": redeemed_coupons,
    }


def save_explorer_profile(
    explorer_name: str,
    total_points: int,
    solved_riddles: List[str],
    solved_quests: List[str],
    redeemed_coupons: List[Dict[str, Any]],
) -> None:
    """# LOGIC: Persist Explorer profile updates to `explorer_profile` in SQLite."""
    tier_name = calculate_tier(total_points)["current"]["name"]
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        UPDATE explorer_profile
        SET explorer_name = ?, total_points = ?, current_tier = ?,
            solved_riddles = ?, solved_quests = ?, redeemed_coupons = ?
        WHERE id = 1
        """,
        (
            explorer_name.strip() or "Explorer",
            total_points,
            tier_name,
            json.dumps(solved_riddles, ensure_ascii=False),
            json.dumps(solved_quests, ensure_ascii=False),
            json.dumps(redeemed_coupons, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def insert_diary_entry(
    entry_date: str,
    lyon_spot: str,
    diary_text: str,
    image_path: Optional[str],
    album_theme: str,
    album_font: str,
) -> None:
    """# LOGIC: Insert a dated travel diary entry into SQLite `diary_entries`."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO diary_entries (entry_date, lyon_spot, diary_text, image_path, album_theme, album_font)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entry_date, lyon_spot, diary_text, image_path, album_theme, album_font),
    )
    conn.commit()
    conn.close()


def load_diary_entries() -> List[Dict[str, Any]]:
    """# LOGIC: Retrieve all saved diary entries ordered from newest to oldest."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM diary_entries ORDER BY entry_date DESC, id DESC").fetchall()]
    conn.close()
    return rows


def delete_diary_entry(entry_id: int) -> None:
    """# LOGIC: Delete a specific diary entry by ID from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ==============================================================================
# 5. NOMINATIM REVERSE-GEOCODING & LYON PROXIMITY VERIFICATION
# ==============================================================================

def reverse_geocode_coordinates(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    # LOGIC: Reverse-geocode real mobile GPS `(latitude, longitude)` using `Nominatim`
    to fetch the Explorer's real neighborhood/district, city, and country, and verify
    whether their live coordinates are inside Lyon, France.
    """
    try:
        geolocator = Nominatim(user_agent="explorer_quest_lyon_streamlit_app")
        location = geolocator.reverse((latitude, longitude), exactly_one=True, language="en", timeout=10)
        address = location.raw.get("address", {}) if location and location.raw else {}
    except Exception:
        address = {}

    district = (
        address.get("suburb")
        or address.get("neighbourhood")
        or address.get("city_district")
        or address.get("quarter")
        or address.get("borough")
        or ""
    )
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
        or f"Lat {latitude:.4f}°, Lon {longitude:.4f}°"
    )
    country = address.get("country") or ""
    country_code = (address.get("country_code") or "").lower()

    # LOGIC: Format "[District/City, Country]" cleanly
    if district and country and district.lower() != city.lower():
        place_label = f"{district} / {city}, {country}"
    elif country:
        place_label = f"{city}, {country}"
    else:
        place_label = city

    # LOGIC: Verify whether live GPS coordinates are inside Lyon, France
    in_lyon_bounds = (45.6500 <= latitude <= 45.8800) and (4.7200 <= longitude <= 5.0200)
    in_lyon_admin = ("lyon" in city.lower() or "lyon" in str(address).lower()) and (
        country_code == "fr" or "france" in country.lower()
    )

    return {
        "district": district,
        "city": city,
        "country": country,
        "place_label": place_label,
        "is_in_lyon": bool(in_lyon_bounds and in_lyon_admin),
    }


# ==============================================================================
# 6. STRICT LYON-ONLY GOOGLE GEMINI AI RIDDLE GENERATOR (`google-genai`)
# ==============================================================================

def generate_lyon_riddles(api_key: str) -> List[Dict[str, Any]]:
    """
    # LOGIC: Strict Lyon-Only AI Riddle Generator using `google-genai` (`gemini-2.5-flash`)
    with `system_instruction` and Structured JSON Output (`response_mime_type="application/json"`).
    Contains ZERO default/hardcoded riddles.
    """
    client = genai.Client(api_key=api_key.strip())

    strict_system_instruction = (
        "You are an ancient secret-keeper who ONLY possesses knowledge about Lyon, France "
        "(its history, traboules, gastronomy, geography, and landmarks). You have zero knowledge "
        "of any other city or topic. Generate exactly 12 unique, challenging riddles and trivia "
        "questions exclusively about Lyon."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Generate exactly 12 unique, challenging riddles and trivia questions exclusively about "
            "Lyon, France, including 4 multiple-choice options, the exact correct answer, and a helpful hint."
        ),
        config=types.GenerateContentConfig(
            system_instruction=strict_system_instruction,
            response_mime_type="application/json",
            response_schema=LyonRiddleCollection,
            temperature=0.75,
        ),
    )

    if response.parsed and getattr(response.parsed, "riddles", None):
        riddles_list = [r.model_dump() for r in response.parsed.riddles][:12]
    else:
        riddles_list = json.loads(response.text).get("riddles", [])[:12]

    batch_id = uuid.uuid4().hex[:4].upper()
    for idx, item in enumerate(riddles_list, start=1):
        item["id"] = f"LYON-{batch_id}-R{idx:02d}"

    return riddles_list


# ==============================================================================
# 7. REPORTLAB PDF ALBUM EXPORT ENGINE
# ==============================================================================

def safe_pdf_text(text: str) -> str:
    """# LOGIC: Normalize French typography characters for ReportLab Latin-1 Type1 fonts."""
    if not text:
        return ""
    replacements = {
        "œ": "oe",
        "Œ": "OE",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "…": "...",
        "•": "*",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_album_pdf(
    profile: Dict[str, Any],
    entries: List[Dict[str, Any]],
    default_theme_name: str,
    default_font_name: str,
) -> bytes:
    """
    # LOGIC: Render a formatted, multi-page styled PDF Travel Album using ReportLab
    with a custom Expedition Cover Page and per-entry Visual Themes, Custom Fonts,
    and embedded photographs.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4

    cover_theme = ALBUM_THEMES.get(default_theme_name, ALBUM_THEMES["Vintage Map"])
    cover_font = CUSTOM_FONTS.get(default_font_name, CUSTOM_FONTS["Playfair Display"])

    # Cover Page
    c.setFillColor(colors.HexColor(cover_theme["bg"]))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor(cover_theme["accent"]))
    c.setLineWidth(3)
    c.rect(28, 28, page_w - 56, page_h - 56, fill=0, stroke=1)
    c.setStrokeColor(colors.HexColor(cover_theme["secondary"]))
    c.setLineWidth(1)
    c.rect(36, 36, page_w - 72, page_h - 72, fill=0, stroke=1)

    c.setFillColor(colors.HexColor(cover_theme["accent"]))
    c.setFont(cover_font["pdf_body"], 11)
    c.drawCentredString(page_w / 2, page_h - 110, safe_pdf_text("EXPLORER QUEST : ÉDITION LYON"))

    c.setFillColor(colors.HexColor(cover_theme["text"]))
    c.setFont(cover_font["pdf_title"], 28)
    c.drawCentredString(page_w / 2, page_h - 160, safe_pdf_text("Carnet d'Expédition à Lyon"))

    c.setFillColor(colors.HexColor(cover_theme["accent"]))
    c.setFont(cover_font["pdf_body"], 14)
    c.drawCentredString(page_w / 2, page_h - 188, safe_pdf_text("Official Lyon Expedition Diary & Photo Album"))

    # Cover Summary Card
    c.setFillColor(colors.HexColor(cover_theme["card_bg"]))
    c.setStrokeColor(colors.HexColor(cover_theme["accent"]))
    c.setLineWidth(1.5)
    c.roundRect(80, page_h - 410, page_w - 160, 175, 10, fill=1, stroke=1)

    c.setFillColor(colors.HexColor(cover_theme["text"]))
    c.setFont(cover_font["pdf_title"], 16)
    c.drawCentredString(page_w / 2, page_h - 270, safe_pdf_text(f"Explorateur / Explorer : {profile['explorer_name']}"))
    c.setFont(cover_font["pdf_body"], 12)
    c.drawCentredString(page_w / 2, page_h - 300, safe_pdf_text(f"Rang / Tier : {profile['current_tier']} ({profile['tier_fr']})"))
    c.drawCentredString(page_w / 2, page_h - 328, safe_pdf_text(f"Points Cumulés / Total XP : {profile['total_points']} pts"))
    c.drawCentredString(
        page_w / 2,
        page_h - 356,
        safe_pdf_text(f"Énigmes Résolues : {len(profile['solved_riddles'])}   |   Quêtes Réelles : {len(profile['solved_quests'])}/3"),
    )
    c.drawCentredString(page_w / 2, page_h - 384, safe_pdf_text(f"Souvenirs Archivés / Diary Pages : {len(entries)}"))
    c.showPage()

    if not entries:
        c.setFillColor(colors.HexColor(cover_theme["bg"]))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(cover_theme["text"]))
        c.setFont(cover_font["pdf_title"], 18)
        c.drawCentredString(page_w / 2, page_h / 2 + 12, safe_pdf_text("Aucune entrée de journal pour le moment."))
        c.setFont(cover_font["pdf_body"], 13)
        c.drawCentredString(page_w / 2, page_h / 2 - 14, safe_pdf_text("No diary entries recorded yet, Explorer!"))
        c.showPage()
    else:
        for idx, entry in enumerate(entries, start=1):
            t_name = entry.get("album_theme") or default_theme_name
            f_name = entry.get("album_font") or default_font_name
            theme = ALBUM_THEMES.get(t_name, cover_theme)
            font_cfg = CUSTOM_FONTS.get(f_name, cover_font)

            c.setFillColor(colors.HexColor(theme["bg"]))
            c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

            margin = 36
            c.setFillColor(colors.HexColor(theme["card_bg"]))
            c.setStrokeColor(colors.HexColor(theme["accent"]))
            c.setLineWidth(2)
            c.roundRect(margin, margin, page_w - 2 * margin, page_h - 2 * margin, 12, fill=1, stroke=1)

            y_cursor = page_h - margin - 34
            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 10)
            c.drawString(
                margin + 24,
                y_cursor,
                safe_pdf_text(f"ENTRÉE #{idx:02d}  |  DATE : {entry['entry_date']}  |  THÈME : {t_name.upper()}"),
            )

            y_cursor -= 28
            c.setFillColor(colors.HexColor(theme["text"]))
            c.setFont(font_cfg["pdf_title"], 20)
            c.drawString(margin + 24, y_cursor, safe_pdf_text(entry["lyon_spot"]))

            y_cursor -= 18
            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 11)
            c.drawString(margin + 24, y_cursor, safe_pdf_text(f"Police / Font : {f_name}"))

            y_cursor -= 12
            c.setStrokeColor(colors.HexColor(theme["secondary"]))
            c.setLineWidth(1.2)
            c.line(margin + 24, y_cursor, page_w - margin - 24, y_cursor)
            y_cursor -= 18

            img_path = entry.get("image_path")
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    orig_w, orig_h = pil_img.size
                    max_w = page_w - 2 * margin - 48
                    max_h = 265
                    scale = min(max_w / orig_w, max_h / orig_h)
                    draw_w, draw_h = orig_w * scale, orig_h * scale
                    img_x = (page_w - draw_w) / 2
                    img_y = y_cursor - draw_h

                    c.setStrokeColor(colors.HexColor(theme["accent"]))
                    c.setLineWidth(1.5)
                    c.rect(img_x - 3, img_y - 3, draw_w + 6, draw_h + 6, fill=0, stroke=1)

                    img_buf = io.BytesIO()
                    pil_img.save(img_buf, format="JPEG", quality=88)
                    img_buf.seek(0)
                    c.drawImage(ImageReader(img_buf), img_x, img_y, width=draw_w, height=draw_h)
                    y_cursor = img_y - 24
                except Exception:
                    y_cursor -= 10

            c.setFillColor(colors.HexColor(theme["text"]))
            c.setFont(font_cfg["pdf_body"], 12)
            text_max_w = page_w - 2 * margin - 48
            for para in (entry.get("diary_text") or "").split("\n"):
                wrapped_lines = simpleSplit(safe_pdf_text(para), font_cfg["pdf_body"], 12, text_max_w)
                if not wrapped_lines:
                    y_cursor -= 14
                for line in wrapped_lines:
                    if y_cursor < margin + 45:
                        break
                    c.drawString(margin + 24, y_cursor, line)
                    y_cursor -= 18
                y_cursor -= 6

            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 9)
            c.drawCentredString(
                page_w / 2,
                margin + 16,
                safe_pdf_text(f"Explorer Quest: Lyon Edition  •  {profile['explorer_name']}  •  Page {idx}"),
            )
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# 8. UI EDITING HELPERS & DUAL-LANGUAGE COMPONENTS
# ==============================================================================

def inject_global_styles() -> None:
    """
    # UI EDITING: Load all 10 Custom Google Fonts and apply the Lyon Heritage
    color palette (Rhône Navy #14213D, Silk Crimson #9E2A2B, Parchment #FAF7F2).
    """
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Cinzel:wght@600;700&family=Lobster&family=Montserrat:wght@400;600;700&family=Oswald:wght@500;700&family=Pacifico&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Space+Grotesk:wght@400;600;700&family=Special+Elite&family=Syne:wght@600;700&display=swap" rel="stylesheet">

        <style>
            /* UI EDITING: Base Canvas & Typography */
            .stApp {
                background-color: #FAF7F2;
                color: #1B2432;
                font-family: 'Montserrat', sans-serif;
            }
            /* UI EDITING: Sidebar Command Deck */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #14213D 0%, #1D2D50 100%);
                color: #FAF7F2;
            }
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {
                color: #FAF7F2 !important;
            }
            section[data-testid="stSidebar"] input {
                color: #14213D !important;
                background-color: #FAF7F2 !important;
            }
            /* UI EDITING: Hero Banner */
            .lyon-hero {
                background: linear-gradient(135deg, #14213D 0%, #2B2D42 55%, #9E2A2B 100%);
                padding: 1.65rem 2rem;
                border-radius: 16px;
                border-bottom: 4px solid #D4A373;
                color: #FFFFFF;
                margin-bottom: 1.15rem;
                box-shadow: 0 10px 25px rgba(20, 33, 61, 0.18);
            }
            .lyon-hero-fr {
                font-family: 'Cinzel', serif;
                font-size: 2.05rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin: 0;
                color: #FFFFFF;
            }
            .lyon-hero-en {
                font-family: 'Montserrat', sans-serif;
                font-size: 0.96rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.13em;
                color: #F4D58D;
                margin-top: 0.25rem;
            }
            /* UI EDITING: Dual-Language Section Headers */
            .dual-header {
                border-left: 5px solid #9E2A2B;
                padding-left: 0.9rem;
                margin: 1.05rem 0 0.8rem 0;
            }
            .dual-header-fr {
                font-family: 'Playfair Display', serif;
                font-size: 1.42rem;
                font-weight: 700;
                color: #14213D;
                line-height: 1.2;
                margin: 0;
            }
            .dual-header-en {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.84rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #9E2A2B;
                margin-top: 0.16rem;
            }
            /* UI EDITING: Cards & Badges */
            .lyon-card {
                background: #FFFFFF;
                border: 1px solid #E5DEC9;
                border-radius: 14px;
                padding: 1.1rem;
                box-shadow: 0 4px 14px rgba(20, 33, 61, 0.06);
                margin-bottom: 0.95rem;
            }
            .badge-pill {
                display: inline-block;
                background: #14213D;
                color: #F4D58D;
                padding: 0.2rem 0.65rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .pts-pill {
                display: inline-block;
                background: #9E2A2B;
                color: #FFFFFF;
                padding: 0.2rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dual_header(fr_title: str, en_subtitle: str, dark_bg: bool = False) -> None:
    """
    # UI EDITING: Enforce Dual-Language UI Rule — French primary text above,
    English translation placed directly below as a subtitle.
    """
    fr_color = "#FFFFFF" if dark_bg else "#14213D"
    en_color = "#F4D58D" if dark_bg else "#9E2A2B"
    border_color = "#F4D58D" if dark_bg else "#9E2A2B"
    st.markdown(
        f"""
        <div class="dual-header" style="border-left-color: {border_color};">
            <div class="dual-header-fr" style="color: {fr_color};">{fr_title}</div>
            <div class="dual-header-en" style="color: {en_color};">{en_subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_file_to_base64(path: Optional[str]) -> Optional[str]:
    """# LOGIC: Encode local diary image as base64 data URI for Live Album Preview."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            raw = f.read()
        return f"data:image/jpeg;base64,{base64.b64encode(raw).decode('utf-8')}"
    except Exception:
        return None


def render_album_preview_card(
    entry_date: str,
    lyon_spot: str,
    diary_text: str,
    theme_name: str,
    font_name: str,
    image_b64: Optional[str] = None,
) -> None:
    """
    # UI EDITING: Render Live Album Studio preview card styled with the selected
    Album Visual Theme (1 of 10) and Custom Google Font (1 of 10).
    """
    theme = ALBUM_THEMES.get(theme_name, ALBUM_THEMES["Vintage Map"])
    font_css = CUSTOM_FONTS.get(font_name, CUSTOM_FONTS["Playfair Display"])["css"]

    img_html = ""
    if image_b64:
        img_html = f"""
        <div style="margin: 0.85rem 0; text-align: center;">
            <img src="{image_b64}" style="max-width: 100%; max-height: 280px; border-radius: 8px; border: 2px solid {theme['accent']}; object-fit: cover;" />
        </div>
        """

    safe_text = (diary_text or "Écrivez vos souvenirs de Lyon ici... / Write your Lyon memories here...").replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="
            background: {theme['bg']};
            padding: 1.35rem;
            border-radius: 14px;
            border: {theme['border']};
            box-shadow: 0 8px 22px rgba(0,0,0,0.12);
            margin-bottom: 1rem;
        ">
            <div style="
                background: {theme['card_bg']};
                color: {theme['text']};
                font-family: {font_css};
                padding: 1.35rem;
                border-radius: 10px;
                border: 1px solid {theme['secondary']};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; font-size: 0.82rem; color: {theme['accent']}; font-weight: 700; letter-spacing: 0.05em;">
                    <span>📍 {lyon_spot}</span>
                    <span>📅 {entry_date}  •  🎨 {theme_name} ({theme['tag']})</span>
                </div>
                <h3 style="margin: 0.55rem 0 0.15rem 0; color: {theme['text']}; font-family: {font_css}; font-size: 1.5rem;">
                    Carnet de Voyage — {lyon_spot}
                </h3>
                <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.09em; color: {theme['accent']}; margin-bottom: 0.75rem;">
                    Lyon Expedition Journal  •  Font: {font_name}
                </div>
                <hr style="border: none; border-top: 1px solid {theme['secondary']}; margin: 0.5rem 0;" />
                {img_html}
                <p style="font-size: 1.06rem; line-height: 1.65; color: {theme['text']}; margin-top: 0.65rem;">
                    {safe_text}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 9. MAIN STREAMLIT APPLICATION
# ==============================================================================

def main() -> None:
    # UI EDITING: Page Configuration & Styles
    st.set_page_config(
        page_title="Explorer Quest: Lyon Edition",
        page_icon="🦁",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_styles()

    # LOGIC: Auto-initialize SQLite database (`explorer_lyon.db`) on app startup
    init_db()

    # LOGIC: Initialize Session State (No hardcoded coordinates or default riddles)
    if "profile" not in st.session_state:
        st.session_state.profile = load_explorer_profile()
    if "diary_entries" not in st.session_state:
        st.session_state.diary_entries = load_diary_entries()
    if "riddles" not in st.session_state:
        st.session_state.riddles = []
    if "live_location" not in st.session_state:
        st.session_state.live_location = None
    if "geo_cache" not in st.session_state:
        st.session_state.geo_cache = {}

    profile = st.session_state.profile

    # --------------------------------------------------------------------------
    # SIDEBAR: EXPLORER COMMAND DECK & GEMINI API KEY
    # --------------------------------------------------------------------------
    with st.sidebar:
        render_dual_header("Tableau de l'Explorateur", "Explorer Command Deck", dark_bg=True)

        new_name = st.text_input(
            "Nom de l'Explorateur / Explorer Name",
            value=profile["explorer_name"],
        )
        if new_name.strip() and new_name.strip() != profile["explorer_name"]:
            save_explorer_profile(
                explorer_name=new_name.strip(),
                total_points=profile["total_points"],
                solved_riddles=profile["solved_riddles"],
                solved_quests=profile["solved_quests"],
                redeemed_coupons=profile["redeemed_coupons"],
            )
            st.session_state.profile = load_explorer_profile()
            profile = st.session_state.profile
            st.toast(f"Bienvenue, Explorer {profile['explorer_name']} ! | Welcome, Explorer!")

        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.08); padding: 1rem; border-radius: 12px; border: 1px solid #F4D58D; margin: 0.75rem 0;">
                <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #F4D58D;">
                    Rang Actuel / Current Tier
                </div>
                <div style="font-size: 1.25rem; font-weight: 700; margin: 0.2rem 0;">
                    {profile['tier_badge']} {profile['current_tier']}
                </div>
                <div style="font-size: 0.84rem; opacity: 0.9;">
                    {profile['tier_fr']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tier Progression Bar
        if profile["next_tier"]:
            nxt = profile["next_tier"]
            cur_min = calculate_tier(profile["total_points"])["current"]["min_pts"]
            span = max(1, nxt["min_pts"] - cur_min)
            st.progress(min(1.0, (profile["total_points"] - cur_min) / span))
            st.caption(f"Prochain rang / Next Tier: **{nxt['name']}** ({nxt['min_pts'] - profile['total_points']} pts restants)")
        else:
            st.progress(1.0)
            st.caption("Rang Maximum Atteint ! | Maximum Legend Tier!")

        sb_c1, sb_c2 = st.columns(2)
        sb_c1.metric("XP Total", f"{profile['total_points']} pts")
        sb_c2.metric("Solde / Wallet", f"{profile['available_points']} pts")

        sb_c3, sb_c4 = st.columns(2)
        sb_c3.metric("Énigmes / Riddles", f"{len(profile['solved_riddles'])}")
        sb_c4.metric("Quêtes / Quests", f"{len(profile['solved_quests'])}/3")

        st.markdown("---")
        render_dual_header("Clé API Google Gemini", "Gemini AI Configuration", dark_bg=True)
        gemini_api_key = st.text_input(
            "Clé API Gemini / Gemini API Key",
            value=os.environ.get("GEMINI_API_KEY", ""),
            type="password",
            help="Required to summon the 12 Lyon-only riddles from gemini-2.5-flash.",
        )

    # --------------------------------------------------------------------------
    # HERO BANNER (DUAL LANGUAGE FRENCH + ENGLISH)
    # --------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="lyon-hero">
            <div class="lyon-hero-fr">🦁 Explorer Quest : Édition Lyon</div>
            <div class="lyon-hero-en">Real Mobile GPS Expedition, Strict Lyon AI Riddles & Album Studio</div>
            <div style="margin-top: 0.65rem; font-size: 0.92rem; color: #F8F9FA;">
                Bienvenue, <strong>Explorer {profile['explorer_name']}</strong> ! Vérifiez votre position GPS mobile, résolvez les 12 énigmes de Lyon générées par IA et composez votre album souvenir.<br/>
                <em>Welcome, Explorer {profile['explorer_name']}! Verify your live mobile GPS, solve 12 AI-generated Lyon riddles, and craft your travel album.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # 5 MAIN NAVIGATION TABS
    # --------------------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🗺️ Guide Interactif & GPS | Location Hub",
            "🧩 Énigmes IA et Quêtes | AI Quests",
            "📔 Journal & Album PDF | Studio",
            "🎟️ Boutique de Coupons | Rewards",
            "🗄️ Profil & Base SQLite | Archives",
        ]
    )

    # ==========================================================================
    # TAB 1: LYON LOCATION HUB (REAL MOBILE GPS & GUIDE INTERACTIF)
    # ==========================================================================
    with tab1:
        render_dual_header(
            "Détection GPS Mobile en Temps Réel",
            "Real Mobile GPS & Live Reverse-Geocoding",
        )

        st.markdown(
            """
            <div class="lyon-card">
                <strong>📡 Capteur GPS Mobile / Live Device Geolocation :</strong><br/>
                Cliquez sur le bouton de géolocalisation ci-dessous pour autoriser le GPS de votre appareil et vérifier si vous vous trouvez à Lyon, France.<br/>
                <em>Tap the geolocation button below to authorize device GPS and verify whether you are currently in Lyon, France.</em>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # LOGIC: Render `streamlit_geolocation()` button widget in the Location Hub
        location = streamlit_geolocation()

        if location and location.get("latitude") is not None and location.get("longitude") is not None:
            lat = float(location["latitude"])
            lon = float(location["longitude"])
            cache_key = f"{lat:.5f},{lon:.5f}"

            if cache_key not in st.session_state.geo_cache:
                st.session_state.geo_cache[cache_key] = reverse_geocode_coordinates(lat, lon)

            geo_info = st.session_state.geo_cache[cache_key]
            st.session_state.live_location = {
                "lat": lat,
                "lon": lon,
                "place_label": geo_info["place_label"],
                "is_in_lyon": geo_info["is_in_lyon"],
            }

        # LOGIC: Display prominent `st.success` announcement banner & plot live GPS on `st.map()`
        if st.session_state.live_location is not None:
            live = st.session_state.live_location
            st.success(f"Explorer, your mobile GPS confirms you are currently in {live['place_label']}!")

            if live["is_in_lyon"]:
                st.info(
                    "🔓 **Lyon, France Verified!** Your live coordinates place you inside Lyon, France — all 3 Real-Life Lyon Photo Quests are now **UNLOCKED** in Tab 2!"
                )
            else:
                st.warning(
                    "🔒 **Outside Lyon, France:** Your live GPS confirms you are currently outside Lyon, France. Real-Life Photo Quests remain locked until you are in Lyon, France, though you can still generate & solve all 12 Lyon AI Riddles!"
                )

            st.caption(f"Coordonnées GPS en direct / Live Coordinates: **{live['lat']:.5f}°, {live['lon']:.5f}°**")
            st.map([{"lat": live["lat"], "lon": live["lon"]}], zoom=13)
        else:
            st.info("En attente du signal GPS mobile — appuyez sur le bouton GPS ci-dessus. | Awaiting mobile GPS fix — tap the geolocation button above.")

        st.markdown("---")
        render_dual_header(
            "Encyclopédie Culturelle de Lyon",
            "Lyon Cultural Dossier: History, Traboules, Architecture, Bouchons & Festivals",
        )
        topic_choice = st.selectbox(
            "Choisissez un thème culturel / Select a Lyon Cultural Topic",
            options=list(LYON_CULTURAL_TOPICS.keys()),
        )
        dossier = LYON_CULTURAL_TOPICS[topic_choice]
        st.markdown(
            f"""
            <div class="lyon-card">
                <p style="font-size: 1.04rem; color: #14213D; font-weight: 600; margin-bottom: 0.4rem;">
                    🇫🇷 {dossier['fr']}
                </p>
                <p style="font-size: 0.95rem; color: #4A5568; font-style: italic; margin-bottom: 0.85rem;">
                    🇬🇧 {dossier['en']}
                </p>
                <div style="font-weight: 700; color: #9E2A2B; margin-bottom: 0.35rem;">
                    Repères de l'Explorateur / Explorer Key Facts:
                </div>
                <ul style="margin: 0; padding-left: 1.25rem; color: #1B2432;">
                    {''.join(f'<li style="margin-bottom: 0.3rem;">{fact}</li>' for fact in dossier['facts'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_dual_header(
            "Les Incontournables de Lyon",
            "Interactive Photo Cards of Iconic Lyon Landmarks",
        )
        lm_cols = st.columns(3)
        for idx, lm in enumerate(LYON_LANDMARKS):
            with lm_cols[idx % 3]:
                fallback_svg = (
                    "data:image/svg+xml;utf8,"
                    "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='360'>"
                    "<rect width='100%' height='100%' fill='%2314213D'/>"
                    "<text x='50%' y='50%' fill='%23F4D58D' font-size='22' font-family='serif' text-anchor='middle'>"
                    f"{lm['name_fr'].replace('&', 'et')}"
                    "</text></svg>"
                )
                st.markdown(
                    f"""
                    <div class="lyon-card" style="padding: 0; overflow: hidden;">
                        <img src="{lm['image_url']}" onerror="this.onerror=null;this.src='{fallback_svg}';"
                             style="width: 100%; height: 180px; object-fit: cover; display: block;" />
                        <div style="padding: 1rem;">
                            <span class="badge-pill">{lm['district']}</span>
                            <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0.5rem 0 0.1rem 0;">
                                {lm['name_fr']}
                            </h4>
                            <div style="font-size: 0.78rem; text-transform: uppercase; color: #9E2A2B; font-weight: 700; margin-bottom: 0.5rem;">
                                {lm['name_en']}
                            </div>
                            <p style="font-size: 0.88rem; color: #1B2432; margin-bottom: 0.35rem;">{lm['desc_fr']}</p>
                            <p style="font-size: 0.82rem; color: #5C677D; font-style: italic; margin: 0;">{lm['desc_en']}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================================================
    # TAB 2: STRICT LYON-ONLY AI RIDDLES & GPS-GATED PHOTO QUESTS
    # ==========================================================================
    with tab2:
        render_dual_header(
            "Énigmes Historiques Exclusives à Lyon (IA Gemini)",
            "Strict Lyon-Only AI Riddle Generator — 12 Location-Bound Riddles (50 pts each)",
        )

        # LOGIC: Strict Lyon-Only AI Riddle Generator button (No default riddles exist)
        if st.button("✨ Generate Lyon Riddles | Générer les 12 Énigmes de Lyon", type="primary", use_container_width=True):
            if not gemini_api_key or not gemini_api_key.strip():
                st.error("Explorer, please enter your Google Gemini API key in the sidebar before generating Lyon riddles.")
            else:
                with st.spinner("Le Gardien des Secrets de Lyon prépare 12 énigmes uniques... | Summoning 12 exclusive Lyon riddles..."):
                    try:
                        st.session_state.riddles = generate_lyon_riddles(gemini_api_key)
                        st.success(f"12 unique Lyon riddles generated for Explorer {profile['explorer_name']}!")
                    except Exception as ex:
                        st.error(f"Gemini API Error: {ex}")

        if not st.session_state.riddles:
            st.markdown(
                """
                <div class="lyon-card" style="border-left: 5px solid #D4A373;">
                    <h4 style="color: #14213D; margin-top: 0;">🏛️ Aucune énigme chargée | Awaiting Gemini AI Generation</h4>
                    <p style="margin-bottom: 0.3rem;">
                        Aucune énigme par défaut n'est intégrée. Saisissez votre clé API Google Gemini dans la barre latérale et cliquez sur <strong>« Generate Lyon Riddles »</strong> pour invoquer 12 énigmes exclusivement consacrées à Lyon.
                    </p>
                    <p style="color: #4A5568; font-style: italic; margin-bottom: 0;">
                        No hardcoded default riddles exist. Enter your Google Gemini API key in the sidebar and click <strong>"Generate Lyon Riddles"</strong> above to summon 12 unique Lyon-only riddles.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            r_cols = st.columns(2)
            for idx, riddle in enumerate(st.session_state.riddles):
                rid = riddle["id"]
                is_solved = rid in profile["solved_riddles"]
                with r_cols[idx % 2]:
                    status_label = "✅ RÉSOLUE / SOLVED (+50 pts)" if is_solved else "🔒 À DÉCOUVRIR / 50 PTS"
                    st.markdown(
                        f"""
                        <div class="lyon-card" style="border-left: 4px solid {'#2D6A4F' if is_solved else '#9E2A2B'};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span class="badge-pill">📍 {riddle['spot']}</span>
                                <span class="pts-pill" style="background: {'#2D6A4F' if is_solved else '#9E2A2B'};">{status_label}</span>
                            </div>
                            <p style="font-weight: 600; color: #14213D; margin: 0.65rem 0 0.25rem 0;">
                                #{idx + 1}. {riddle['question_fr']}
                            </p>
                            <p style="font-size: 0.88rem; color: #4A5568; font-style: italic; margin-bottom: 0.3rem;">
                                {riddle['question_en']}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.expander(f"💡 Indice / Hint — Énigme #{idx + 1}"):
                        st.write(riddle.get("hint", "Explorez l'histoire de Lyon !"))

                    if is_solved:
                        st.success(f"Réponse validée / Verified Answer: **{riddle['answer']}**")
                    else:
                        options = riddle.get("options") or [riddle["answer"]]
                        chosen_opt = st.radio(
                            f"Choisissez votre réponse / Select answer #{idx + 1}",
                            options=options,
                            key=f"radio_{rid}",
                        )
                        if st.button(f"Valider / Submit #{idx + 1} (+50 pts)", key=f"sub_{rid}", use_container_width=True):
                            if chosen_opt.strip().lower() == riddle["answer"].strip().lower():
                                save_explorer_profile(
                                    explorer_name=profile["explorer_name"],
                                    total_points=profile["total_points"] + RIDDLE_POINTS,
                                    solved_riddles=profile["solved_riddles"] + [rid],
                                    solved_quests=profile["solved_quests"],
                                    redeemed_coupons=profile["redeemed_coupons"],
                                )
                                st.session_state.profile = load_explorer_profile()
                                st.balloons()
                                st.toast(f"Bravo Explorer ! +{RIDDLE_POINTS} pts ajoutés à votre profil !")
                                st.rerun()
                            else:
                                st.error("Réponse incorrecte, Explorer ! Consultez l'indice et réessayez. | Incorrect answer, Explorer!")

        st.markdown("---")
        render_dual_header(
            "Les 3 Quêtes Photo Réelles (200 pts — Haute Récompense)",
            "3 Real-Life Lyon Photo Quests (Unlocked via Live Lyon GPS)",
        )

        # LOGIC: Gate Real-Life Quests behind live Lyon, France GPS verification
        is_verified_in_lyon = bool(
            st.session_state.live_location and st.session_state.live_location.get("is_in_lyon")
        )
        if not is_verified_in_lyon:
            st.warning(
                "🔒 **Quêtes Réelles Verrouillées | Real-Life Quests Locked:** "
                "Explorer, use the mobile GPS widget in **Tab 1 (Guide Interactif & GPS)** to verify you are currently in **Lyon, France** and unlock these 3 high-reward (200 pts) photo quests."
            )

        for q_idx, quest in enumerate(REAL_LIFE_QUESTS, start=1):
            qid = quest["id"]
            q_solved = qid in profile["solved_quests"]
            st.markdown(
                f"""
                <div class="lyon-card" style="border-left: 5px solid {'#2D6A4F' if q_solved else '#D4A373'}; opacity: {'1.0' if is_verified_in_lyon else '0.7'};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0;">
                            Quête #{q_idx} : {quest['title_fr']}
                        </h4>
                        <span class="pts-pill" style="background: {'#2D6A4F' if q_solved else '#14213D'};">
                            {'✅ ACCOMPLIE / COMPLETED' if q_solved else f'🏆 +{quest["points"]} PTS'}
                        </span>
                    </div>
                    <div style="font-size: 0.84rem; text-transform: uppercase; color: #9E2A2B; font-weight: 700; margin-bottom: 0.5rem;">
                        {quest['title_en']}
                    </div>
                    <p style="color: #1B2432; margin-bottom: 0.25rem;">🇫🇷 {quest['desc_fr']}</p>
                    <p style="color: #4A5568; font-style: italic; font-size: 0.9rem; margin-bottom: 0;">🇬🇧 {quest['desc_en']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if q_solved:
                st.success(f"Quête #{q_idx} validée avec votre GPS à Lyon ! +200 pts attribués à Explorer {profile['explorer_name']}.")
            else:
                quest_photo = st.file_uploader(
                    f"Preuve Photo / Upload Quest Photo #{q_idx}",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"q_photo_{qid}",
                    disabled=not is_verified_in_lyon,
                )
                if st.button(
                    f"📸 Valider la Quête #{q_idx} avec GPS (+200 pts) | Complete Quest",
                    key=f"q_btn_{qid}",
                    disabled=not is_verified_in_lyon,
                ):
                    if quest_photo is None:
                        st.warning("Explorer, veuillez téléverser une photo preuve pour valider cette quête ! | Please upload a proof photo first!")
                    else:
                        saved_q_path = os.path.join(PHOTO_DIR, f"quest_{qid}_{uuid.uuid4().hex[:6]}.jpg")
                        Image.open(io.BytesIO(quest_photo.getvalue())).convert("RGB").save(saved_q_path, format="JPEG", quality=88)

                        save_explorer_profile(
                            explorer_name=profile["explorer_name"],
                            total_points=profile["total_points"] + QUEST_POINTS,
                            solved_riddles=profile["solved_riddles"],
                            solved_quests=profile["solved_quests"] + [qid],
                            redeemed_coupons=profile["redeemed_coupons"],
                        )
                        st.session_state.profile = load_explorer_profile()
                        live = st.session_state.live_location
                        st.balloons()
                        st.success(
                            f"🎉 +{QUEST_POINTS} pts ! Position GPS ({live['lat']:.4f}°, {live['lon']:.4f}° — {live['place_label']}) enregistrée pour Explorer {profile['explorer_name']} !"
                        )
                        st.rerun()

    # ==========================================================================
    # TAB 3: EXPLORER DIARY, ALBUM STUDIO & PDF EXPORT
    # ==========================================================================
    with tab3:
        render_dual_header(
            "Journal de l'Explorateur, Studio d'Album & Export PDF",
            "Explorer Diary, 10 Visual Themes, 10 Google Fonts & Formatted PDF Album Export",
        )

        studio_col1, studio_col2 = st.columns([1.05, 1.15])

        with studio_col1:
            st.markdown('<div class="lyon-card">', unsafe_allow_html=True)
            render_dual_header("Nouvelle Page de Journal", "Compose Diary Entry")

            entry_date_val = st.date_input("Date de l'étape / Entry Date", value=date.today())

            live_spot_default = (
                st.session_state.live_location["place_label"]
                if st.session_state.live_location
                else None
            )
            spot_options = ([live_spot_default] if live_spot_default else []) + [
                lm["name_fr"] for lm in LYON_LANDMARKS
            ] + [
                "Les Halles de Lyon Paul Bocuse",
                "La Croix-Rousse & Mur des Canuts",
                "Bouchon Lyonnais Traditionnel",
                "Autre lieu à Lyon / Custom Lyon Spot",
            ]
            selected_spot = st.selectbox("Lieu à Lyon / Lyon Spot Tag", options=spot_options)
            if "Autre lieu" in selected_spot:
                selected_spot = st.text_input("Nom du lieu / Custom Spot Name", value="Rue Saint-Jean, Vieux Lyon")

            theme_col, font_col = st.columns(2)
            chosen_theme = theme_col.selectbox(
                "Thème Visuel (10) / Album Theme",
                options=list(ALBUM_THEMES.keys()),
                index=0,
            )
            chosen_font = font_col.selectbox(
                "Police Google Fonts (10) / Custom Font",
                options=list(CUSTOM_FONTS.keys()),
                index=1,
            )
            st.caption(f"Style typographique : *{CUSTOM_FONTS[chosen_font]['vibe']}*")

            uploaded_diary_photo = st.file_uploader(
                "Photo Souvenir / Upload Lyon Photo",
                type=["jpg", "jpeg", "png", "webp"],
                key="diary_photo_uploader",
            )

            diary_narrative = st.text_area(
                "Récit de l'Explorateur / Travel Diary Narrative",
                height=145,
                placeholder="Aujourd'hui à Lyon, j'ai franchi une porte discrète du Vieux Lyon pour découvrir une cour Renaissance illuminée...",
            )

            if st.button("💾 Enregistrer dans l'Album SQLite | Save Diary Entry", type="primary", use_container_width=True):
                if not diary_narrative.strip():
                    st.warning("Explorer, écrivez quelques lignes dans votre journal avant d'enregistrer ! | Please write a diary entry before saving.")
                else:
                    saved_img_path = None
                    if uploaded_diary_photo is not None:
                        saved_img_path = os.path.join(
                            PHOTO_DIR,
                            f"diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg",
                        )
                        Image.open(io.BytesIO(uploaded_diary_photo.getvalue())).convert("RGB").save(
                            saved_img_path, format="JPEG", quality=90
                        )

                    insert_diary_entry(
                        entry_date=entry_date_val.strftime("%Y-%m-%d"),
                        lyon_spot=selected_spot,
                        diary_text=diary_narrative.strip(),
                        image_path=saved_img_path,
                        album_theme=chosen_theme,
                        album_font=chosen_font,
                    )
                    st.session_state.diary_entries = load_diary_entries()
                    st.toast("Page enregistrée dans votre album lyonnais ! | Diary entry saved to SQLite!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with studio_col2:
            render_dual_header("Aperçu en Direct de l'Album", "Live Album Studio Preview")
            preview_b64 = None
            if uploaded_diary_photo is not None:
                preview_b64 = f"data:image/jpeg;base64,{base64.b64encode(uploaded_diary_photo.getvalue()).decode('utf-8')}"

            render_album_preview_card(
                entry_date=entry_date_val.strftime("%Y-%m-%d"),
                lyon_spot=selected_spot,
                diary_text=diary_narrative,
                theme_name=chosen_theme,
                font_name=chosen_font,
                image_b64=preview_b64,
            )

            render_dual_header("Exportation PDF Haute Définition", "PDF Album Export Engine")
            pdf_bytes = generate_album_pdf(
                profile=profile,
                entries=st.session_state.diary_entries,
                default_theme_name=chosen_theme,
                default_font_name=chosen_font,
            )
            st.download_button(
                label="📥 Télécharger l'Album Photo & Journal (.PDF) | Download Styled PDF Album",
                data=pdf_bytes,
                file_name=f"Explorer_Quest_Lyon_{profile['explorer_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.markdown("---")
        render_dual_header(
            f"Pages Enregistrées dans l'Album ({len(st.session_state.diary_entries)})",
            "Saved Lyon Diary & Photo Archive",
        )
        if not st.session_state.diary_entries:
            st.info("Votre album est prêt, Explorer ! Ajoutez votre première photo et note de voyage ci-dessus. | Your album is ready, Explorer!")
        else:
            for item in st.session_state.diary_entries:
                img_uri = image_file_to_base64(item.get("image_path"))
                render_album_preview_card(
                    entry_date=item["entry_date"],
                    lyon_spot=item["lyon_spot"],
                    diary_text=item["diary_text"],
                    theme_name=item["album_theme"],
                    font_name=item["album_font"],
                    image_b64=img_uri,
                )
                if st.button(f"🗑️ Supprimer l'entrée #{item['id']} | Delete Entry", key=f"del_entry_{item['id']}"):
                    delete_diary_entry(item["id"])
                    st.session_state.diary_entries = load_diary_entries()
                    st.rerun()

    # ==========================================================================
    # TAB 4: REAL-WORLD COUPON STORE (BOUTIQUE DE COUPONS)
    # ==========================================================================
    with tab4:
        render_dual_header(
            "Boutique de Coupons Partenaires à Lyon",
            "Real-World Coupon Store — Redeem Explorer Points for Local Lyon Vouchers",
        )

        st.markdown(
            f"""
            <div class="lyon-card" style="background: #14213D; color: #FFFFFF;">
                <span style="font-size: 1.05rem;">
                    💰 Solde Disponible / Available Wallet : <strong style="color: #F4D58D; font-size: 1.25rem;">{profile['available_points']} pts</strong>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    🏅 XP Total (Rang / Tier) : <strong>{profile['total_points']} pts</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cpn_cols = st.columns(2)
        for idx, cpn in enumerate(COUPON_CATALOG):
            with cpn_cols[idx % 2]:
                can_afford = profile["available_points"] >= cpn["cost"]
                st.markdown(
                    f"""
                    <div class="lyon-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="badge-pill">{cpn['category']}</span>
                            <span class="pts-pill">{cpn['cost']} PTS</span>
                        </div>
                        <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0.6rem 0 0.15rem 0;">
                            {cpn['partner']}
                        </h4>
                        <div style="font-size: 0.78rem; color: #6C757D; margin-bottom: 0.5rem;">📍 {cpn['district']}</div>
                        <p style="font-weight: 600; color: #1B2432; margin-bottom: 0.25rem;">🇫🇷 {cpn['offer_fr']}</p>
                        <p style="font-size: 0.88rem; color: #4A5568; font-style: italic; margin-bottom: 0.4rem;">🇬🇧 {cpn['offer_en']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"🎟️ Échanger ({cpn['cost']} pts) | Redeem Voucher",
                    key=f"redeem_{cpn['id']}",
                    disabled=not can_afford,
                    use_container_width=True,
                ):
                    voucher_code = f"LYON-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
                    new_coupon_record = {
                        "coupon_id": cpn["id"],
                        "partner": cpn["partner"],
                        "offer_en": cpn["offer_en"],
                        "cost": cpn["cost"],
                        "code": voucher_code,
                        "redeemed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    save_explorer_profile(
                        explorer_name=profile["explorer_name"],
                        total_points=profile["total_points"],
                        solved_riddles=profile["solved_riddles"],
                        solved_quests=profile["solved_quests"],
                        redeemed_coupons=profile["redeemed_coupons"] + [new_coupon_record],
                    )
                    st.session_state.profile = load_explorer_profile()
                    st.balloons()
                    st.success(f"Coupon débloqué pour Explorer ! Code : **{voucher_code}**")
                    st.rerun()

        st.markdown("---")
        render_dual_header(
            f"Portefeuille de Coupons Actifs ({len(profile['redeemed_coupons'])})",
            "Explorer's Redeemed Lyon Voucher Wallet",
        )
        if not profile["redeemed_coupons"]:
            st.info("Aucun coupon échangé pour l'instant. Résolvez des énigmes pour gagner des points ! | No vouchers redeemed yet.")
        else:
            for v in reversed(profile["redeemed_coupons"]):
                st.markdown(
                    f"""
                    <div class="lyon-card" style="border-left: 5px solid #2D6A4F;">
                        <strong>🎟️ {v['partner']}</strong> — <code>{v['code']}</code><br/>
                        <span style="font-size: 0.9rem;">{v['offer_en']}</span><br/>
                        <span style="font-size: 0.78rem; color: #6C757D;">Échangé le / Redeemed: {v['redeemed_at']} ({v['cost']} pts)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================================================
    # TAB 5: SQLITE DATABASE PERSISTENCE INSPECTOR (PROFIL & JOURNAL)
    # ==========================================================================
    with tab5:
        render_dual_header(
            "Base de Données SQLite & Sauvegarde Automatique",
            f"SQLite Persistence Inspector (`{DB_PATH}`)",
        )
        st.write(
            f"Toutes vos statistiques d'Explorer, énigmes résolues, quêtes photo, coupons et pages d'album sont persistés automatiquement dans **`{DB_PATH}`**."
        )

        db_c1, db_c2 = st.columns(2)
        with db_c1:
            st.subheader("Table: `explorer_profile`")
            st.json(
                {
                    "explorer_name": profile["explorer_name"],
                    "total_points": profile["total_points"],
                    "available_points": profile["available_points"],
                    "current_tier": profile["current_tier"],
                    "solved_riddles": profile["solved_riddles"],
                    "solved_quests": profile["solved_quests"],
                    "redeemed_coupons_count": len(profile["redeemed_coupons"]),
                }
            )
        with db_c2:
            st.subheader("Table: `diary_entries`")
            st.json(st.session_state.diary_entries)

        st.markdown("---")
        if st.button("⚠️ Réinitialiser la Progression (Garder le Journal) | Reset Points & Quests"):
            save_explorer_profile(
                explorer_name=profile["explorer_name"],
                total_points=0,
                solved_riddles=[],
                solved_quests=[],
                redeemed_coupons=[],
            )
            st.session_state.profile = load_explorer_profile()
            st.toast("Progression réinitialisée pour une nouvelle expédition à Lyon !")
            st.rerun()


if __name__ == "__main__":
    main()