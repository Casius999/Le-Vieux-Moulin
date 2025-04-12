#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'installation pour le module de commande vocale.

Ce script facilite l'installation et la configuration du module de commande
vocale pour le système de gestion intelligente Le Vieux Moulin.

Auteur: Équipe technique Le Vieux Moulin
Date de dernière modification: 2025-04-12
"""

from setuptools import setup, find_packages

setup(
    name="voice_command",
    version="1.0.0",
    description="Module de commande vocale pour Le Vieux Moulin",
    author="Équipe technique Le Vieux Moulin",
    author_email="tech@levieuxmoulin.fr",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyAudio>=0.2.13",
        "SpeechRecognition>=3.10.0",
        "websocket-client>=1.6.1",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "flask>=2.3.3",
        "flask-socketio>=5.3.4",
        "bootstrap-flask>=2.3.0",
        "python-dotenv>=1.0.0",
        "pytextdistance>=4.5.0",
        "pocketsphinx>=0.1.15"  # Pour la reconnaissance vocale hors-ligne
    ],
    entry_points={
        'console_scripts': [
            'voice-command=voice_command.app:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    python_requires=">=3.9",
)