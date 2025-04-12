#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Traitement audio pour le module de commande vocale.

Ce module fournit des fonctions de traitement du signal audio pour améliorer
la qualité de la reconnaissance vocale, notamment en réduisant le bruit.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

import logging
import numpy as np
from typing import Any, Optional, Union

import speech_recognition as sr

from config import Config


class AudioProcessor:
    """Processeur de signal audio pour améliorer la reconnaissance vocale."""

    def __init__(self, config: Config):
        """Initialise le processeur audio avec la configuration spécifiée.

        Args:
            config (Config): Configuration du module.
        """
        self.logger = logging.getLogger("voice_command.audio_processor")
        self.config = config
        
        # Paramètres de traitement audio
        self.noise_reduction = config.get("speech_recognition.noise_suppression", True)
        self.noise_threshold = config.get("speech_recognition.noise_threshold", 0.05)

    def denoise(self, audio_data: sr.AudioData) -> sr.AudioData:
        """Applique une réduction de bruit à un échantillon audio.

        Args:
            audio_data (sr.AudioData): Données audio à traiter.

        Returns:
            sr.AudioData: Données audio traitées.
        """
        if not self.noise_reduction:
            return audio_data
            
        try:
            # Convertir l'objet AudioData en tableau numpy
            raw_data = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
            sample_rate = audio_data.sample_rate
            
            # Appliquer une réduction de bruit simple
            processed_data = self._spectral_subtraction(raw_data, sample_rate)
            
            # Reconvertir en objet AudioData
            processed_audio = sr.AudioData(
                processed_data.tobytes(),
                sample_rate=sample_rate,
                sample_width=audio_data.sample_width
            )
            
            return processed_audio
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la réduction du bruit: {str(e)}")
            # En cas d'erreur, retourner l'audio original
            return audio_data

    def _spectral_subtraction(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Implémente une réduction de bruit par soustraction spectrale.

        Args:
            audio_data (np.ndarray): Signal audio sous forme de tableau numpy.
            sample_rate (int): Fréquence d'échantillonnage en Hz.

        Returns:
            np.ndarray: Signal audio traité.
        """
        # Paramètres pour la soustraction spectrale
        frame_length = int(0.025 * sample_rate)  # 25ms
        frame_step = int(0.010 * sample_rate)    # 10ms
        
        # Assurer que la longueur du signal est suffisante
        if len(audio_data) < frame_length:
            return audio_data
        
        # Estimer le bruit à partir des premiers frames (supposés être du silence/bruit)
        noise_frames = min(10, max(1, int(0.1 * len(audio_data) / frame_length)))  # 10% ou max 10 frames
        noise_spectrum = self._estimate_noise(audio_data[:noise_frames * frame_length], frame_length, frame_step)
        
        # Traiter le signal par fenêtres
        processed_data = np.zeros_like(audio_data)
        for i in range(0, len(audio_data) - frame_length, frame_step):
            frame = audio_data[i:i+frame_length]
            
            # Appliquer une fenêtre de Hamming
            window = np.hamming(frame_length)
            windowed_frame = frame * window
            
            # Transformer dans le domaine fréquentiel
            spectrum = np.fft.rfft(windowed_frame)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Soustraire le spectre du bruit
            magnitude = np.maximum(magnitude - self.noise_threshold * noise_spectrum, 0)
            
            # Reconstruire le signal
            processed_spectrum = magnitude * np.exp(1j * phase)
            processed_frame = np.fft.irfft(processed_spectrum)
            
            # Ajouter au signal de sortie avec overlap-add
            processed_data[i:i+frame_length] += processed_frame * window
        
        # Normaliser le signal
        if np.max(np.abs(processed_data)) > 0:
            processed_data = processed_data * (np.max(np.abs(audio_data)) / np.max(np.abs(processed_data)))
        
        return processed_data.astype(np.int16)

    def _estimate_noise(self, noise_data: np.ndarray, frame_length: int, frame_step: int) -> np.ndarray:
        """Estime le spectre du bruit à partir d'un segment audio.

        Args:
            noise_data (np.ndarray): Segment audio contenant principalement du bruit.
            frame_length (int): Longueur de chaque frame en échantillons.
            frame_step (int): Décalage entre frames successifs en échantillons.

        Returns:
            np.ndarray: Estimation du spectre du bruit.
        """
        noise_spectrum = np.zeros(frame_length // 2 + 1)
        frame_count = 0
        
        # Calculer la moyenne du spectre sur plusieurs frames
        for i in range(0, len(noise_data) - frame_length, frame_step):
            frame = noise_data[i:i+frame_length]
            window = np.hamming(frame_length)
            windowed_frame = frame * window
            spectrum = np.abs(np.fft.rfft(windowed_frame))
            noise_spectrum += spectrum
            frame_count += 1
        
        if frame_count > 0:
            noise_spectrum /= frame_count
        
        return noise_spectrum