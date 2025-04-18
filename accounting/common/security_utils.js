/**
 * Utilitaires de sécurité pour le module de comptabilité
 * Ce module fournit les fonctionnalités pour sécuriser les données sensibles,
 * gérer l'authentification et protéger les informations financières.
 */

'use strict';

const crypto = require('crypto');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { ConfigManager } = require('./config_manager');

/**
 * Classe d'utilitaires de sécurité pour les données financières
 */
class SecurityUtils {
  /**
   * Crée une nouvelle instance des utilitaires de sécurité
   * @param {Object} options - Options de configuration
   * @param {Object} options.encryptionConfig - Configuration du chiffrement
   * @param {Object} options.authConfig - Configuration de l'authentification
   * @param {ConfigManager} options.configManager - Instance du gestionnaire de configuration
   */
  constructor(options = {}) {
    this.encryptionConfig = options.encryptionConfig || {};
    this.authConfig = options.authConfig || {};
    this.configManager = options.configManager || 
      (ConfigManager.getConfigManager ? ConfigManager.getConfigManager() : null);
    
    // Initialiser avec les configurations par défaut si nécessaire
    if (!this.encryptionConfig.algorithm) {
      this.encryptionConfig.algorithm = 'aes-256-gcm';
    }
    
    if (!this.encryptionConfig.secretKey) {
      // Récupérer depuis la configuration ou utiliser une valeur par défaut (pour le développement uniquement)
      this.encryptionConfig.secretKey = this.configManager ? 
        this.configManager.get('security.encryption.secretKey') : 
        process.env.ENCRYPTION_SECRET_KEY || 'default-dev-key-change-in-production';
    }
    
    if (!this.authConfig.jwtSecret) {
      // Récupérer depuis la configuration ou utiliser une valeur par défaut
      this.authConfig.jwtSecret = this.configManager ?
        this.configManager.get('security.auth.jwtSecret') :
        process.env.JWT_SECRET_KEY || 'default-jwt-key-change-in-production';
    }
    
    if (!this.authConfig.jwtExpiresIn) {
      this.authConfig.jwtExpiresIn = '1h'; // 1 heure par défaut
    }
  }
  
  /**
   * Chiffre une donnée sensible
   * @param {string} data - Donnée à chiffrer
   * @param {Object} options - Options de chiffrement
   * @returns {Object} - Donnée chiffrée avec IV et tag d'authentification
   */
  encrypt(data, options = {}) {
    try {
      // Valider les entrées
      if (!data) {
        throw new Error('Aucune donnée fournie pour le chiffrement');
      }
      
      // Générer un IV aléatoire
      const iv = crypto.randomBytes(16);
      
      // Créer le chiffreur
      const cipher = crypto.createCipheriv(
        options.algorithm || this.encryptionConfig.algorithm,
        Buffer.from(options.secretKey || this.encryptionConfig.secretKey),
        iv
      );
      
      // Chiffrer les données
      let encrypted = cipher.update(data, 'utf8', 'hex');
      encrypted += cipher.final('hex');
      
      // Récupérer le tag d'authentification pour AES-GCM
      const authTag = cipher.getAuthTag ? cipher.getAuthTag() : null;
      
      return {
        encrypted,
        iv: iv.toString('hex'),
        authTag: authTag ? authTag.toString('hex') : null,
        algorithm: options.algorithm || this.encryptionConfig.algorithm
      };
    } catch (error) {
      console.error('Erreur lors du chiffrement des données:', error);
      throw new Error(`Échec du chiffrement: ${error.message}`);
    }
  }
  
  /**
   * Déchiffre une donnée sensible
   * @param {Object} encryptedData - Donnée chiffrée
   * @param {string} encryptedData.encrypted - Texte chiffré
   * @param {string} encryptedData.iv - Vecteur d'initialisation
   * @param {string} encryptedData.authTag - Tag d'authentification (pour AES-GCM)
   * @param {string} encryptedData.algorithm - Algorithme utilisé
   * @param {Object} options - Options de déchiffrement
   * @returns {string} - Donnée déchiffrée
   */
  decrypt(encryptedData, options = {}) {
    try {
      // Valider les entrées
      if (!encryptedData || !encryptedData.encrypted || !encryptedData.iv) {
        throw new Error('Données chiffrées incomplètes');
      }
      
      // Créer le déchiffreur
      const decipher = crypto.createDecipheriv(
        encryptedData.algorithm || options.algorithm || this.encryptionConfig.algorithm,
        Buffer.from(options.secretKey || this.encryptionConfig.secretKey),
        Buffer.from(encryptedData.iv, 'hex')
      );
      
      // Définir le tag d'authentification pour AES-GCM
      if (encryptedData.authTag && decipher.setAuthTag) {
        decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
      }
      
      // Déchiffrer les données
      let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      
      return decrypted;
    } catch (error) {
      console.error('Erreur lors du déchiffrement des données:', error);
      throw new Error(`Échec du déchiffrement: ${error.message}`);
    }
  }
  
  /**
   * Hache un mot de passe pour stockage sécurisé
   * @param {string} password - Mot de passe en clair
   * @param {number} [saltRounds=10] - Nombre de tours de salage
   * @returns {Promise<string>} - Mot de passe haché
   */
  async hashPassword(password, saltRounds = 10) {
    try {
      return await bcrypt.hash(password, saltRounds);
    } catch (error) {
      console.error('Erreur lors du hachage du mot de passe:', error);
      throw new Error(`Échec du hachage: ${error.message}`);
    }
  }
  
  /**
   * Vérifie un mot de passe par rapport à sa version hachée
   * @param {string} password - Mot de passe en clair
   * @param {string} hashedPassword - Version hachée du mot de passe
   * @returns {Promise<boolean>} - Validité du mot de passe
   */
  async verifyPassword(password, hashedPassword) {
    try {
      return await bcrypt.compare(password, hashedPassword);
    } catch (error) {
      console.error('Erreur lors de la vérification du mot de passe:', error);
      throw new Error(`Échec de la vérification: ${error.message}`);
    }
  }
  
  /**
   * Génère un token JWT pour l'authentification
   * @param {Object} payload - Données à inclure dans le token
   * @param {Object} [options={}] - Options de génération du token
   * @returns {string} - Token JWT généré
   */
  generateJwtToken(payload, options = {}) {
    try {
      const secret = options.jwtSecret || this.authConfig.jwtSecret;
      const expiresIn = options.expiresIn || this.authConfig.jwtExpiresIn;
      
      return jwt.sign(payload, secret, { expiresIn });
    } catch (error) {
      console.error('Erreur lors de la génération du token JWT:', error);
      throw new Error(`Échec de la génération du token: ${error.message}`);
    }
  }
  
  /**
   * Vérifie et décode un token JWT
   * @param {string} token - Token JWT à vérifier
   * @param {Object} [options={}] - Options de vérification
   * @returns {Object} - Payload du token décodé
   */
  verifyJwtToken(token, options = {}) {
    try {
      const secret = options.jwtSecret || this.authConfig.jwtSecret;
      
      return jwt.verify(token, secret, options);
    } catch (error) {
      console.error('Erreur lors de la vérification du token JWT:', error);
      throw new Error(`Token invalide: ${error.message}`);
    }
  }
  
  /**
   * Génère une empreinte numérique (hash) d'un contenu
   * @param {string|Buffer} data - Données à hacher
   * @param {string} [algorithm='sha256'] - Algorithme de hachage
   * @returns {string} - Empreinte numérique en format hexadécimal
   */
  generateHash(data, algorithm = 'sha256') {
    try {
      const hash = crypto.createHash(algorithm);
      hash.update(data);
      return hash.digest('hex');
    } catch (error) {
      console.error('Erreur lors de la génération du hash:', error);
      throw new Error(`Échec de la génération du hash: ${error.message}`);
    }
  }
  
  /**
   * Génère une signature numérique pour un contenu
   * @param {string|Buffer} data - Données à signer
   * @param {string|Buffer} privateKey - Clé privée pour la signature
   * @param {Object} [options={}] - Options de signature
   * @returns {string} - Signature en format hexadécimal
   */
  signData(data, privateKey, options = {}) {
    try {
      const sign = crypto.createSign(options.algorithm || 'RSA-SHA256');
      sign.update(data);
      sign.end();
      return sign.sign(privateKey, 'hex');
    } catch (error) {
      console.error('Erreur lors de la signature des données:', error);
      throw new Error(`Échec de la signature: ${error.message}`);
    }
  }
  
  /**
   * Vérifie une signature numérique
   * @param {string|Buffer} data - Données originales
   * @param {string} signature - Signature à vérifier
   * @param {string|Buffer} publicKey - Clé publique pour la vérification
   * @param {Object} [options={}] - Options de vérification
   * @returns {boolean} - Validité de la signature
   */
  verifySignature(data, signature, publicKey, options = {}) {
    try {
      const verify = crypto.createVerify(options.algorithm || 'RSA-SHA256');
      verify.update(data);
      verify.end();
      return verify.verify(publicKey, signature, 'hex');
    } catch (error) {
      console.error('Erreur lors de la vérification de la signature:', error);
      throw new Error(`Échec de la vérification: ${error.message}`);
    }
  }
  
  /**
   * Anonymise des données personnelles sensibles
   * @param {Object} data - Données à anonymiser
   * @param {string[]} sensitiveFields - Liste des champs sensibles
   * @param {Object} [options={}] - Options d'anonymisation
   * @returns {Object} - Données anonymisées
   */
  anonymizeData(data, sensitiveFields, options = {}) {
    try {
      const anonymizedData = JSON.parse(JSON.stringify(data));
      
      for (const field of sensitiveFields) {
        const value = this._getNestedValue(anonymizedData, field);
        
        if (value !== undefined) {
          const anonymizedValue = this._anonymizeValue(value, options);
          this._setNestedValue(anonymizedData, field, anonymizedValue);
        }
      }
      
      return anonymizedData;
    } catch (error) {
      console.error('Erreur lors de l\'anonymisation des données:', error);
      throw new Error(`Échec de l'anonymisation: ${error.message}`);
    }
  }
  
  /**
   * Récupère une valeur imbriquée dans un objet
   * @param {Object} obj - Objet source
   * @param {string} path - Chemin d'accès (notation par points)
   * @returns {*} - Valeur récupérée
   * @private
   */
  _getNestedValue(obj, path) {
    return path.split('.').reduce((prev, curr) => {
      return prev ? prev[curr] : undefined;
    }, obj);
  }
  
  /**
   * Définit une valeur imbriquée dans un objet
   * @param {Object} obj - Objet à modifier
   * @param {string} path - Chemin d'accès (notation par points)
   * @param {*} value - Nouvelle valeur
   * @private
   */
  _setNestedValue(obj, path, value) {
    const parts = path.split('.');
    const last = parts.pop();
    
    const parent = parts.reduce((prev, curr) => {
      if (!prev[curr]) prev[curr] = {};
      return prev[curr];
    }, obj);
    
    parent[last] = value;
  }
  
  /**
   * Anonymise une valeur selon son type
   * @param {*} value - Valeur à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {*} - Valeur anonymisée
   * @private
   */
  _anonymizeValue(value, options) {
    if (typeof value === 'string') {
      if (this._isEmailLike(value)) {
        return this._anonymizeEmail(value, options);
      } else if (this._isPhoneLike(value)) {
        return this._anonymizePhone(value, options);
      } else if (this._isAddressLike(value)) {
        return this._anonymizeAddress(value, options);
      } else {
        return this._anonymizeString(value, options);
      }
    } else if (typeof value === 'number') {
      return this._anonymizeNumber(value, options);
    } else if (Array.isArray(value)) {
      return value.map(item => this._anonymizeValue(item, options));
    }
    
    return value;
  }
  
  /**
   * Vérifie si une chaîne ressemble à un email
   * @param {string} value - Chaîne à vérifier
   * @returns {boolean} - Résultat de la vérification
   * @private
   */
  _isEmailLike(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }
  
  /**
   * Vérifie si une chaîne ressemble à un numéro de téléphone
   * @param {string} value - Chaîne à vérifier
   * @returns {boolean} - Résultat de la vérification
   * @private
   */
  _isPhoneLike(value) {
    return /^[+\d\s()-]{7,20}$/.test(value);
  }
  
  /**
   * Vérifie si une chaîne ressemble à une adresse
   * @param {string} value - Chaîne à vérifier
   * @returns {boolean} - Résultat de la vérification
   * @private
   */
  _isAddressLike(value) {
    // Heuristique simple: contient un numéro suivi d'un mot, et plus de 15 caractères
    return value.length > 15 && /\d+\s+\w+/.test(value);
  }
  
  /**
   * Anonymise une adresse email
   * @param {string} email - Email à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {string} - Email anonymisé
   * @private
   */
  _anonymizeEmail(email, options = {}) {
    const [local, domain] = email.split('@');
    const anonymizedLocal = local.slice(0, 1) + '*'.repeat(local.length - 1);
    return `${anonymizedLocal}@${domain}`;
  }
  
  /**
   * Anonymise un numéro de téléphone
   * @param {string} phone - Téléphone à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {string} - Téléphone anonymisé
   * @private
   */
  _anonymizePhone(phone, options = {}) {
    // Garder les 4 derniers chiffres, remplacer le reste par des *
    const digits = phone.replace(/\D/g, '');
    const visible = options.visibleDigits || 4;
    
    if (digits.length <= visible) {
      return '*'.repeat(digits.length);
    }
    
    return '*'.repeat(digits.length - visible) + digits.slice(-visible);
  }
  
  /**
   * Anonymise une adresse postale
   * @param {string} address - Adresse à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {string} - Adresse anonymisée
   * @private
   */
  _anonymizeAddress(address, options = {}) {
    // Version simple: garder le code postal et la ville
    const words = address.split(/\s+/);
    
    if (words.length <= 2) {
      return '*'.repeat(address.length);
    }
    
    // Anonymiser tous les mots sauf les deux derniers (supposés être CP et ville)
    const anonymizedParts = words.slice(0, -2).map(() => '***');
    return [...anonymizedParts, ...words.slice(-2)].join(' ');
  }
  
  /**
   * Anonymise une chaîne générique
   * @param {string} str - Chaîne à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {string} - Chaîne anonymisée
   * @private
   */
  _anonymizeString(str, options = {}) {
    if (str.length <= 1) return str;
    
    const keepStart = options.keepStart !== undefined ? options.keepStart : 1;
    const keepEnd = options.keepEnd !== undefined ? options.keepEnd : 1;
    
    if (str.length <= keepStart + keepEnd) {
      return '*'.repeat(str.length);
    }
    
    return str.slice(0, keepStart) + 
           '*'.repeat(str.length - keepStart - keepEnd) + 
           str.slice(-keepEnd);
  }
  
  /**
   * Anonymise un nombre
   * @param {number} num - Nombre à anonymiser
   * @param {Object} options - Options d'anonymisation
   * @returns {number} - Nombre anonymisé
   * @private
   */
  _anonymizeNumber(num, options = {}) {
    // Par défaut, arrondir à la dizaine supérieure
    const precision = options.precision || 10;
    return Math.ceil(num / precision) * precision;
  }
}

module.exports = { SecurityUtils };
