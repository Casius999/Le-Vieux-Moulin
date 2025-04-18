"""
Exporteur de rapports au format PDF.

Ce module est responsable de la conversion du contenu HTML généré
en documents PDF structurés et formatés.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional

import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image, PageBreak)

# Utiliser xhtml2pdf pour la conversion HTML -> PDF
import xhtml2pdf.pisa as pisa

# Configuration du logger
logger = structlog.get_logger(__name__)


class PDFExporter:
    """
    Exporteur de rapports au format PDF.
    
    Cette classe gère la conversion des contenus HTML en documents PDF
    en utilisant la bibliothèque xhtml2pdf pour le contenu principal
    et reportlab pour les éléments supplémentaires (en-têtes, pieds de page, etc.)
    """
    
    def __init__(self):
        """Initialise l'exporteur PDF."""
        # Styles pour les rapports
        self.styles = getSampleStyleSheet()
        
        # Ajouter des styles personnalisés
        self.styles.add(
            ParagraphStyle(
                name='Title',
                parent=self.styles['Title'],
                fontSize=16,
                spaceAfter=10,
                textColor=colors.darkblue
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Heading1',
                parent=self.styles['Heading1'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.darkblue
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Heading2',
                parent=self.styles['Heading2'],
                fontSize=12,
                spaceAfter=6,
                textColor=colors.darkblue
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Normal',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=4
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                name='Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.gray
            )
        )
    
    async def export(self, content: str, output_path: str, data: Optional[Dict] = None) -> str:
        """
        Exporte le contenu HTML en PDF.
        
        Args:
            content (str): Contenu HTML à convertir en PDF
            output_path (str): Chemin du fichier PDF de sortie
            data (Dict, optional): Données supplémentaires pour le rapport
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        logger.info("Génération du PDF", output_path=output_path)
        
        try:
            # Ajouter des styles CSS pour améliorer le rendu
            styled_content = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4; margin: 2cm; }}
                    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10pt; }}
                    h1 {{ color: #00205B; font-size: 16pt; margin-top: 0; }}
                    h2 {{ color: #00205B; font-size: 14pt; }}
                    h3 {{ color: #00205B; font-size: 12pt; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th {{ background-color: #E0E0E0; text-align: left; padding: 5px; }}
                    td {{ padding: 5px; }}
                    .border {{ border: 1px solid #CCCCCC; }}
                    .text-right {{ text-align: right; }}
                    .total {{ font-weight: bold; }}
                    .header {{ padding-bottom: 20px; border-bottom: 1px solid #CCCCCC; }}
                    .footer {{ text-align: center; font-size: 8pt; color: #666666; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Le Vieux Moulin - Rapport Financier</h1>
                    <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
                
                {content}
                
                <div class="footer">
                    <p>Le Vieux Moulin - {datetime.now().strftime('%Y')} - Tous droits réservés</p>
                </div>
            </body>
            </html>
            """
            
            # Créer un fichier temporaire pour le PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Convertir le HTML en PDF
            with open(temp_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    styled_content,
                    dest=pdf_file
                )
            
            # Vérifier si la conversion a réussi
            if pisa_status.err:
                logger.error("Erreur lors de la conversion HTML -> PDF", error=pisa_status.err)
                raise Exception(f"Erreur lors de la génération du PDF: {pisa_status.err}")
            
            # S'assurer que le répertoire de sortie existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Déplacer le fichier temporaire vers le chemin final
            if os.path.exists(output_path):
                os.remove(output_path)
            
            os.rename(temp_path, output_path)
            
            logger.info("PDF généré avec succès", output_path=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Erreur lors de la génération du PDF", error=str(e))
            raise
    
    def _generate_header(self, canvas, doc, data: Dict):
        """
        Génère l'en-tête du document PDF.
        
        Args:
            canvas: Canvas ReportLab
            doc: Document ReportLab
            data (Dict): Données du rapport
        """
        canvas.saveState()
        
        # Logo et titre
        # canvas.drawImage('path_to_logo', 30, doc.height + 30, width=100, height=50)
        
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.darkblue)
        canvas.drawString(30, doc.height + 10, "Le Vieux Moulin - Rapport Financier")
        
        # Informations du rapport
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(colors.black)
        
        report_type = data.get('report_type', 'financier').capitalize()
        period_start = data.get('period_start', datetime.now()).strftime('%d/%m/%Y')
        period_end = data.get('period_end', datetime.now()).strftime('%d/%m/%Y')
        
        canvas.drawString(30, doc.height - 10, f"Rapport {report_type}")
        canvas.drawString(30, doc.height - 25, f"Période: du {period_start} au {period_end}")
        canvas.drawString(30, doc.height - 40, f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        
        # Ligne de séparation
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(30, doc.height - 50, doc.width - 30, doc.height - 50)
        
        canvas.restoreState()
    
    def _generate_footer(self, canvas, doc, data: Dict):
        """
        Génère le pied de page du document PDF.
        
        Args:
            canvas: Canvas ReportLab
            doc: Document ReportLab
            data (Dict): Données du rapport
        """
        canvas.saveState()
        
        # Pied de page
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        
        # Numéro de page
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(doc.width - 30, 30, text)
        
        # Copyright
        canvas.drawString(30, 30, f"Le Vieux Moulin - {datetime.now().year} - Confidentiel")
        
        # Ligne de séparation
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(30, 40, doc.width - 30, 40)
        
        canvas.restoreState()
