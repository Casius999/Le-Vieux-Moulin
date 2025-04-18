#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service de notification pour informer les employés des plannings.

Ce module fournit une interface pour envoyer des notifications aux employés
concernant leurs plannings, modifications, et autres informations importantes.
"""

import logging
import smtplib
import json
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import requests
from requests.exceptions import RequestException

from ..config import NOTIFICATION_CONFIG
from ..models.schedule import Schedule
from ..models.shift import Shift
from ..models.employee import Employee

# Configurer le logger
logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Exception spécifique pour les erreurs de notification."""
    pass


class NotificationService:
    """
    Service pour envoyer des notifications aux employés.
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        test_mode: bool = False
    ):
        """
        Initialise le service de notification.
        
        Args:
            config: Configuration personnalisée (surcharge NOTIFICATION_CONFIG)
            test_mode: Si True, n'envoie pas réellement les notifications
        """
        # Charger la configuration
        self.config = NOTIFICATION_CONFIG.copy()
        if config:
            self.config.update(config)
            
        self.test_mode = test_mode
        self.enabled = self.config.get('enabled', True)
        
        # Configurer les canaux de notification
        self.email_enabled = self.config.get('email', {}).get('enabled', True)
        self.sms_enabled = self.config.get('sms', {}).get('enabled', False)
        
        # Variables pour le suivi
        self.last_error = None
        self.notification_history = []
    
    def notify_schedule_published(
        self,
        schedule: Schedule,
        employees: List[Employee],
        message: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Notifie les employés de la publication d'un nouveau planning.
        
        Args:
            schedule: Planning publié
            employees: Liste des employés concernés
            message: Message personnalisé (optionnel)
            
        Returns:
            Dictionnaire des notifications envoyées par employé
            
        Raises:
            NotificationError: En cas d'erreur d'envoi
        """
        if not self.enabled:
            logger.info("Service de notification désactivé, aucune notification envoyée")
            return {}
        
        # Message par défaut
        if not message:
            start_date = schedule.start_date.strftime('%d/%m/%Y')
            end_date = schedule.end_date.strftime('%d/%m/%Y')
            message = f"Le planning du {start_date} au {end_date} est maintenant disponible. Veuillez vérifier vos horaires."
        
        # Construire un dictionnaire employee_id -> Employee pour lookup rapide
        employee_dict = {employee.employee_id: employee for employee in employees}
        
        # Collecter les shifts par employé
        employee_shifts = {}
        for shift in schedule.shifts:
            if shift.employee_id and shift.employee_id in employee_dict:
                if shift.employee_id not in employee_shifts:
                    employee_shifts[shift.employee_id] = []
                employee_shifts[shift.employee_id].append(shift)
        
        # Notifier chaque employé avec ses shifts
        notification_results = {}
        
        for employee_id, shifts in employee_shifts.items():
            employee = employee_dict[employee_id]
            
            # Trier les shifts par date et heure
            shifts.sort(key=lambda s: (s.date, s.start_time))
            
            try:
                # Construire le contenu personnalisé pour cet employé
                content = self._build_schedule_content(employee, shifts, schedule)
                
                # Envoyer la notification
                channels = self._send_notification(
                    employee=employee,
                    subject=f"Nouveau planning: {start_date} au {end_date}",
                    message=message,
                    content=content,
                    schedule_id=schedule.schedule_id
                )
                
                notification_results[employee_id] = channels
                
            except Exception as e:
                logger.error(f"Erreur lors de la notification de l'employé {employee_id}: {str(e)}")
                notification_results[employee_id] = [f"Erreur: {str(e)}"]
                self.last_error = str(e)
        
        return notification_results
    
    def notify_schedule_update(
        self,
        schedule: Schedule,
        employees: List[Employee],
        updated_shifts: List[Shift],
        message: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Notifie les employés d'une mise à jour du planning.
        
        Args:
            schedule: Planning mis à jour
            employees: Liste des employés concernés
            updated_shifts: Liste des shifts modifiés
            message: Message personnalisé (optionnel)
            
        Returns:
            Dictionnaire des notifications envoyées par employé
            
        Raises:
            NotificationError: En cas d'erreur d'envoi
        """
        if not self.enabled:
            logger.info("Service de notification désactivé, aucune notification envoyée")
            return {}
        
        # Message par défaut
        if not message:
            start_date = schedule.start_date.strftime('%d/%m/%Y')
            end_date = schedule.end_date.strftime('%d/%m/%Y')
            message = f"Mise à jour du planning du {start_date} au {end_date}. Veuillez vérifier vos horaires."
        
        # Construire un dictionnaire employee_id -> Employee pour lookup rapide
        employee_dict = {employee.employee_id: employee for employee in employees}
        
        # Collecter les shifts mis à jour par employé
        employee_shifts = {}
        for shift in updated_shifts:
            if shift.employee_id and shift.employee_id in employee_dict:
                if shift.employee_id not in employee_shifts:
                    employee_shifts[shift.employee_id] = []
                employee_shifts[shift.employee_id].append(shift)
        
        # Notifier chaque employé concerné par les modifications
        notification_results = {}
        
        for employee_id, shifts in employee_shifts.items():
            employee = employee_dict[employee_id]
            
            # Trier les shifts par date et heure
            shifts.sort(key=lambda s: (s.date, s.start_time))
            
            try:
                # Construire le contenu personnalisé pour cet employé
                content = self._build_update_content(employee, shifts, schedule)
                
                # Envoyer la notification
                channels = self._send_notification(
                    employee=employee,
                    subject=f"Mise à jour du planning: {start_date} au {end_date}",
                    message=message,
                    content=content,
                    schedule_id=schedule.schedule_id
                )
                
                notification_results[employee_id] = channels
                
            except Exception as e:
                logger.error(f"Erreur lors de la notification de l'employé {employee_id}: {str(e)}")
                notification_results[employee_id] = [f"Erreur: {str(e)}"]
                self.last_error = str(e)
        
        return notification_results
    
    def notify_employee(
        self,
        employee: Employee,
        subject: str,
        message: str,
        content: Optional[str] = None,
        schedule_id: Optional[str] = None
    ) -> List[str]:
        """
        Envoie une notification personnalisée à un employé.
        
        Args:
            employee: Employé à notifier
            subject: Sujet de la notification
            message: Corps du message
            content: Contenu HTML (optionnel)
            schedule_id: ID du planning associé (optionnel)
            
        Returns:
            Liste des canaux de notification utilisés
            
        Raises:
            NotificationError: En cas d'erreur d'envoi
        """
        if not self.enabled:
            logger.info("Service de notification désactivé, aucune notification envoyée")
            return []
        
        try:
            return self._send_notification(
                employee=employee,
                subject=subject,
                message=message,
                content=content,
                schedule_id=schedule_id
            )
        except Exception as e:
            logger.error(f"Erreur lors de la notification de l'employé {employee.employee_id}: {str(e)}")
            self.last_error = str(e)
            raise NotificationError(f"Impossible d'envoyer la notification: {str(e)}")
    
    def notify_all_employees(
        self,
        employees: List[Employee],
        subject: str,
        message: str,
        content: Optional[str] = None,
        schedule_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Envoie une notification à tous les employés de la liste.
        
        Args:
            employees: Liste des employés à notifier
            subject: Sujet de la notification
            message: Corps du message
            content: Contenu HTML (optionnel)
            schedule_id: ID du planning associé (optionnel)
            
        Returns:
            Dictionnaire des notifications envoyées par employé
            
        Raises:
            NotificationError: En cas d'erreur d'envoi
        """
        if not self.enabled:
            logger.info("Service de notification désactivé, aucune notification envoyée")
            return {}
        
        notification_results = {}
        
        for employee in employees:
            try:
                channels = self._send_notification(
                    employee=employee,
                    subject=subject,
                    message=message,
                    content=content,
                    schedule_id=schedule_id
                )
                
                notification_results[employee.employee_id] = channels
                
            except Exception as e:
                logger.error(f"Erreur lors de la notification de l'employé {employee.employee_id}: {str(e)}")
                notification_results[employee.employee_id] = [f"Erreur: {str(e)}"]
                self.last_error = str(e)
        
        return notification_results
    
    def _send_notification(
        self,
        employee: Employee,
        subject: str,
        message: str,
        content: Optional[str] = None,
        schedule_id: Optional[str] = None
    ) -> List[str]:
        """
        Envoie une notification à un employé via tous les canaux disponibles.
        
        Args:
            employee: Employé à notifier
            subject: Sujet de la notification
            message: Corps du message
            content: Contenu HTML (optionnel)
            schedule_id: ID du planning associé (optionnel)
            
        Returns:
            Liste des canaux de notification utilisés
            
        Raises:
            NotificationError: En cas d'erreur d'envoi
        """
        channels_used = []
        
        # Enregistrer dans l'historique
        self.notification_history.append({
            'timestamp': datetime.now().isoformat(),
            'employee_id': employee.employee_id,
            'subject': subject,
            'message': message,
            'schedule_id': schedule_id
        })
        
        # En mode test, ne pas envoyer réellement
        if self.test_mode:
            logger.info(f"[TEST MODE] Notification à {employee.full_name} ({employee.email}): {subject}")
            return ["test"]
        
        # Envoi par email
        if self.email_enabled and hasattr(employee, 'email') and employee.email:
            try:
                self._send_email(
                    email=employee.email,
                    name=employee.full_name,
                    subject=subject,
                    message=message,
                    html_content=content
                )
                channels_used.append("email")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi d'email à {employee.email}: {str(e)}")
                # Ne pas arrêter, essayer les autres canaux
        
        # Envoi par SMS
        if self.sms_enabled and hasattr(employee, 'phone') and employee.phone:
            try:
                self._send_sms(
                    phone=employee.phone,
                    message=message
                )
                channels_used.append("sms")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de SMS à {employee.phone}: {str(e)}")
                # Ne pas arrêter, essayer les autres canaux
        
        # Si aucun canal n'a fonctionné
        if not channels_used:
            raise NotificationError("Aucun canal de notification disponible ou fonctionnel")
        
        return channels_used
    
    def _send_email(
        self,
        email: str,
        name: str,
        subject: str,
        message: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Envoie un email à un employé.
        
        Args:
            email: Adresse email du destinataire
            name: Nom du destinataire
            subject: Sujet de l'email
            message: Corps du message (texte)
            html_content: Corps du message (HTML, optionnel)
            
        Returns:
            True si l'email a été envoyé avec succès
            
        Raises:
            Exception: En cas d'erreur d'envoi
        """
        # Configuration email
        email_config = self.config.get('email', {})
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 587)
        smtp_user = email_config.get('smtp_user')
        smtp_password = email_config.get('smtp_password')
        from_address = email_config.get('from_address')
        subject_prefix = email_config.get('subject_prefix', '[Le Vieux Moulin] ')
        
        if not all([smtp_server, smtp_port, smtp_user, smtp_password, from_address]):
            raise ValueError("Configuration email incomplète")
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject_prefix + subject
        msg['From'] = from_address
        msg['To'] = email
        
        # Ajouter la version texte
        msg.attach(MIMEText(message, 'plain'))
        
        # Ajouter la version HTML si fournie
        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
        
        try:
            # Connexion au serveur SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            
            # Envoi de l'email
            server.sendmail(from_address, email, msg.as_string())
            server.quit()
            
            logger.info(f"Email envoyé à {name} ({email})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email: {str(e)}")
            raise
    
    def _send_sms(self, phone: str, message: str) -> bool:
        """
        Envoie un SMS à un employé.
        
        Args:
            phone: Numéro de téléphone du destinataire
            message: Corps du message
            
        Returns:
            True si le SMS a été envoyé avec succès
            
        Raises:
            Exception: En cas d'erreur d'envoi
        """
        # Configuration SMS
        sms_config = self.config.get('sms', {})
        sms_provider = sms_config.get('provider')
        account_id = sms_config.get('account_id')
        auth_token = sms_config.get('auth_token')
        from_number = sms_config.get('from_number')
        
        if not all([sms_provider, account_id, auth_token, from_number]):
            raise ValueError("Configuration SMS incomplète")
        
        # Selon le fournisseur SMS
        if sms_provider.lower() == 'twilio':
            return self._send_twilio_sms(account_id, auth_token, from_number, phone, message)
        else:
            raise ValueError(f"Fournisseur SMS non pris en charge: {sms_provider}")
    
    def _send_twilio_sms(
        self,
        account_id: str,
        auth_token: str,
        from_number: str,
        to_number: str,
        message: str
    ) -> bool:
        """
        Envoie un SMS via le fournisseur Twilio.
        
        Args:
            account_id: ID du compte Twilio
            auth_token: Token d'authentification Twilio
            from_number: Numéro d'expéditeur
            to_number: Numéro de destinataire
            message: Corps du message
            
        Returns:
            True si le SMS a été envoyé avec succès
            
        Raises:
            Exception: En cas d'erreur d'envoi
        """
        try:
            # Import retardé pour éviter la dépendance si non utilisé
            from twilio.rest import Client
            
            # Créer le client Twilio
            client = Client(account_id, auth_token)
            
            # Envoi du SMS
            sms = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"SMS envoyé à {to_number}, SID: {sms.sid}")
            return True
            
        except ImportError:
            logger.error("Module twilio non installé. Veuillez l'installer avec 'pip install twilio'")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de SMS: {str(e)}")
            raise
    
    def _build_schedule_content(
        self,
        employee: Employee,
        shifts: List[Shift],
        schedule: Schedule
    ) -> str:
        """
        Construit le contenu HTML pour la notification de planning.
        
        Args:
            employee: Employé concerné
            shifts: Liste des shifts de l'employé
            schedule: Planning complet
            
        Returns:
            Contenu HTML formaté
        """
        # En-tête
        start_date = schedule.start_date.strftime('%d/%m/%Y')
        end_date = schedule.end_date.strftime('%d/%m/%Y')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1, h2 {{ color: #2c5282; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <h1>Planning du {start_date} au {end_date}</h1>
            <p>Bonjour {employee.first_name},</p>
            <p>Voici votre planning pour la période du {start_date} au {end_date} :</p>
            
            <table>
                <tr>
                    <th>Date</th>
                    <th>Horaires</th>
                    <th>Poste</th>
                    <th>Lieu</th>
                </tr>
        """
        
        # Tableau des shifts
        for shift in shifts:
            date_str = shift.date.strftime('%A %d/%m/%Y')
            start_time_str = shift.start_time.strftime('%H:%M')
            end_time_str = shift.end_time.strftime('%H:%M')
            role_str = shift.role.value.capitalize().replace('_', ' ')
            location_str = shift.location.value.capitalize().replace('_', ' ')
            
            html += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{start_time_str} - {end_time_str}</td>
                    <td>{role_str}</td>
                    <td>{location_str}</td>
                </tr>
            """
        
        # Pied de page
        html += f"""
            </table>
            
            <p>Nombre total d'heures planifiées : {sum(shift.duration for shift in shifts):.1f} heures</p>
            
            <p>Pour toute question ou ajustement nécessaire, veuillez contacter le responsable des plannings.</p>
            
            <div class="footer">
                <p>Ce message a été généré automatiquement. Merci de ne pas y répondre directement.</p>
                <p>Le Vieux Moulin - Système de gestion des plannings</p>
                <p>ID du planning : {schedule.schedule_id}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_update_content(
        self,
        employee: Employee,
        shifts: List[Shift],
        schedule: Schedule
    ) -> str:
        """
        Construit le contenu HTML pour la notification de mise à jour de planning.
        
        Args:
            employee: Employé concerné
            shifts: Liste des shifts modifiés de l'employé
            schedule: Planning complet
            
        Returns:
            Contenu HTML formaté
        """
        # En-tête
        start_date = schedule.start_date.strftime('%d/%m/%Y')
        end_date = schedule.end_date.strftime('%d/%m/%Y')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1, h2 {{ color: #2c5282; }}
                .alert {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .highlight {{ background-color: #ffe6e6; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <h1>Mise à jour du planning</h1>
            
            <div class="alert">
                <strong>Attention :</strong> Des modifications ont été apportées à votre planning pour la période du {start_date} au {end_date}.
            </div>
            
            <p>Bonjour {employee.first_name},</p>
            <p>Voici les modifications apportées à votre planning :</p>
            
            <table>
                <tr>
                    <th>Date</th>
                    <th>Horaires</th>
                    <th>Poste</th>
                    <th>Lieu</th>
                    <th>Statut</th>
                </tr>
        """
        
        # Tableau des shifts modifiés
        for shift in shifts:
            date_str = shift.date.strftime('%A %d/%m/%Y')
            start_time_str = shift.start_time.strftime('%H:%M')
            end_time_str = shift.end_time.strftime('%H:%M')
            role_str = shift.role.value.capitalize().replace('_', ' ')
            location_str = shift.location.value.capitalize().replace('_', ' ')
            
            html += f"""
                <tr class="highlight">
                    <td>{date_str}</td>
                    <td>{start_time_str} - {end_time_str}</td>
                    <td>{role_str}</td>
                    <td>{location_str}</td>
                    <td>Modifié</td>
                </tr>
            """
        
        # Pied de page
        html += f"""
            </table>
            
            <p>Pour consulter votre planning complet et pour toute question, veuillez contacter le responsable des plannings.</p>
            
            <div class="footer">
                <p>Ce message a été généré automatiquement. Merci de ne pas y répondre directement.</p>
                <p>Le Vieux Moulin - Système de gestion des plannings</p>
                <p>ID du planning : {schedule.schedule_id}</p>
                <p>Date de la mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
