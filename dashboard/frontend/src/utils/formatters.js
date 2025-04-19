import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Formate un nombre avec séparateur de milliers et décimales
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @param {string} currency - Symbole de devise (optionnel)
 * @returns {string} Valeur formatée
 */
export const formatNumber = (value, decimals = 0, currency = '') => {
  if (value === null || value === undefined) return '-';
  
  const formattedValue = new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
  
  return currency ? `${formattedValue} ${currency}` : formattedValue;
};

/**
 * Formate un montant en devise (€)
 * @param {number} amount - Montant à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Montant formaté
 */
export const formatCurrency = (amount, decimals = 2) => {
  return formatNumber(amount, decimals, '€');
};

/**
 * Formate un pourcentage
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Pourcentage formaté
 */
export const formatPercent = (value, decimals = 1) => {
  return formatNumber(value, decimals, '%');
};

/**
 * Formate une date au format français
 * @param {string|Date} date - Date à formater
 * @param {string} formatString - Format de date (par défaut: dd/MM/yyyy)
 * @returns {string} Date formatée
 */
export const formatDate = (date, formatString = 'dd/MM/yyyy') => {
  if (!date) return '-';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString, { locale: fr });
  } catch (error) {
    console.error('Error formatting date:', error);
    return '-';
  }
};

/**
 * Formate une date et heure au format français
 * @param {string|Date} date - Date à formater
 * @returns {string} Date et heure formatées
 */
export const formatDateTime = (date) => {
  return formatDate(date, 'dd/MM/yyyy HH:mm');
};

/**
 * Formate un statut en texte lisible
 * @param {string} status - Statut à formater
 * @returns {string} Statut formaté
 */
export const formatStatus = (status) => {
  const statusMap = {
    'active': 'Actif',
    'inactive': 'Inactif',
    'pending': 'En attente',
    'completed': 'Terminé',
    'cancelled': 'Annulé',
    'error': 'Erreur',
    'warning': 'Avertissement',
    'success': 'Succès',
    'info': 'Information',
    'critical': 'Critique',
    'planned': 'Planifié'
  };
  
  return statusMap[status] || status;
};
