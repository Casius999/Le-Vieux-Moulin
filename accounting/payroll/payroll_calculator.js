/**
 * Calculateur de paie pour le restaurant "Le Vieux Moulin"
 * Transforme les données de présence en éléments de paie (heures, primes, etc.)
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const moment = require('moment');

/**
 * Classe de calcul des éléments de paie
 * @extends EventEmitter
 */
class PayrollCalculator extends EventEmitter {
  /**
   * Crée une instance du calculateur de paie
   * @param {Object} options - Options de configuration
   * @param {Object} options.rules - Règles de paie
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.rules = options.rules || {};
    this.logger = options.logger || console;
    
    this.logger.debug('PayrollCalculator initialisé');
  }
  
  /**
   * Collecte les données de chiffre d'affaires pour les primes et commissions
   * @param {Object} options - Options de collecte
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données de chiffre d'affaires
   */
  async collectRevenueData({ startDate, endDate }) {
    this.logger.debug(`Collecte des données de chiffre d'affaires du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // NOTE: Dans une implémentation réelle, cela ferait un appel à l'API du système de caisse
      // Simulation pour le prototype
      return new Promise((resolve) => {
        setTimeout(() => {
          // Simuler des données de chiffre d'affaires
          const revenueData = {
            total: 42560.75,
            byDate: {
              '2025-04-01': { total: 2156.50, categories: { food: 1832.50, beverages: 324.00 }, serviceType: { dineIn: 1845.25, takeaway: 311.25 } },
              '2025-04-02': { total: 1942.25, categories: { food: 1623.75, beverages: 318.50 }, serviceType: { dineIn: 1654.75, takeaway: 287.50 } }
              // ... autres jours
            },
            byCategory: {
              food: 35280.45,
              beverages: 7280.30
            },
            byServiceType: {
              dineIn: 36250.40,
              takeaway: 6310.35
            }
          };
          
          resolve(revenueData);
        }, 200);
      });
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de chiffre d\'affaires:', error);
      throw error;
    }
  }
  
  /**
   * Collecte les données de pourboires
   * @param {Object} options - Options de collecte
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données de pourboires
   */
  async collectTipsData({ startDate, endDate }) {
    this.logger.debug(`Collecte des données de pourboires du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // NOTE: Dans une implémentation réelle, cela ferait un appel à l'API du système de caisse
      // Simulation pour le prototype
      return new Promise((resolve) => {
        setTimeout(() => {
          // Simuler des données de pourboires
          const tipsData = {
            total: 2845.30,
            byDate: {
              '2025-04-01': { total: 156.50, byMethod: { cash: 52.50, card: 104.00 } },
              '2025-04-02': { total: 142.25, byMethod: { cash: 48.75, card: 93.50 } }
              // ... autres jours
            },
            byMethod: {
              cash: 925.45,
              card: 1919.85
            }
          };
          
          resolve(tipsData);
        }, 200);
      });
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de pourboires:', error);
      throw error;
    }
  }
  
  /**
   * Calcule les heures à partir des données de présence
   * @param {Object} attendanceData - Données de présence
   * @returns {Promise<Object>} Heures calculées par employé
   */
  async calculateHours(attendanceData) {
    this.logger.debug('Calcul des heures à partir des données de présence');
    
    try {
      const hoursData = {};
      
      // Parcourir chaque employé
      for (const [employeeId, employeeData] of Object.entries(attendanceData)) {
        const periods = employeeData.periods || [];
        
        // Initialiser les compteurs
        const hours = {
          regular: 0,
          overtime: 0,
          night: 0,
          holiday: 0,
          leave: 0,
          break: 0,
          total: 0
        };
        
        // Calculer le total des heures par type
        for (const period of periods) {
          const duration = period.duration || 0;
          
          if (period.type === 'work') {
            // Vérifier si la période est de nuit
            let nightHours = 0;
            
            if (this.rules.workingHours && this.rules.workingHours.nightHours) {
              nightHours = this._calculateNightHours(period, this.rules.workingHours.nightHours);
            }
            
            // Ajouter aux compteurs
            hours.night += nightHours;
            hours.regular += (duration - nightHours);
            hours.total += duration;
          } else if (period.type === 'leave') {
            hours.leave += duration;
            hours.total += duration;
          } else if (period.type === 'break') {
            hours.break += duration;
            // Les pauses ne sont pas comptées dans le total
          }
        }
        
        // Calculer les heures supplémentaires
        if (this.rules.workingHours && this.rules.workingHours.regularHoursPerWeek) {
          const weeklyRegularHours = this.rules.workingHours.regularHoursPerWeek;
          
          if (hours.regular > weeklyRegularHours) {
            hours.overtime = hours.regular - weeklyRegularHours;
            hours.regular = weeklyRegularHours;
          }
        }
        
        // Arrondir les heures pour plus de lisibilité
        for (const [key, value] of Object.entries(hours)) {
          hours[key] = parseFloat(value.toFixed(2));
        }
        
        // Ajouter au résultat
        hoursData[employeeId] = {
          hours,
          metadata: {
            periodCount: periods.length,
            calculatedAt: new Date()
          }
        };
      }
      
      // Émettre un événement de calcul terminé
      this.emit('calculation:complete', {
        type: 'hours',
        employeeCount: Object.keys(hoursData).length
      });
      
      return hoursData;
    } catch (error) {
      this.logger.error('Erreur lors du calcul des heures:', error);
      
      // Émettre un événement d'erreur
      this.emit('calculation:error', {
        type: 'hours',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Calcule les variables de paie (primes, commissions, etc.)
   * @param {Object} options - Options de calcul
   * @param {Object} options.attendanceData - Données de présence
   * @param {Object} options.revenueData - Données de chiffre d'affaires
   * @param {Object} options.tipsData - Données de pourboires
   * @returns {Promise<Object>} Variables calculées par employé
   */
  async calculateVariables({ attendanceData, revenueData, tipsData }) {
    this.logger.debug('Calcul des variables de paie');
    
    try {
      const variablesData = {};
      
      // Calcul des pourboires par employé
      const tipsByEmployee = this._distributeTips(attendanceData, tipsData);
      
      // Parcourir chaque employé
      for (const [employeeId, employeeData] of Object.entries(attendanceData)) {
        // Initialiser les variables
        const variables = {
          service_charge: 0,          // Prime de service
          tips: tipsByEmployee[employeeId] || 0, // Pourboires
          meal_allowance: 0,          // Indemnité repas
          transport_allowance: 0,     // Indemnité transport
          bonus: 0,                   // Bonus
          commission: 0,              // Commission sur ventes
          sundry_additions: 0,        // Divers ajouts
          sundry_deductions: 0        // Divers déductions
        };
        
        // Calculer les indemnités repas
        if (this.rules.mealAllowance) {
          // Une indemnité repas par jour travaillé
          const workDays = this._countWorkDays(employeeData);
          variables.meal_allowance = workDays * this.rules.mealAllowance.value;
        }
        
        // Calculer les commissions sur ventes (exemple simplifié)
        // Dans un cas réel, cela dépendrait du rôle de l'employé et des ventes qu'il a réalisées
        if (employeeData.info && employeeData.info.position === 'Serveur' && revenueData) {
          variables.commission = revenueData.total * 0.01; // 1% du CA total
        }
        
        // Arrondir les variables pour plus de lisibilité
        for (const [key, value] of Object.entries(variables)) {
          variables[key] = parseFloat(value.toFixed(2));
        }
        
        // Ajouter au résultat
        variablesData[employeeId] = {
          variables,
          metadata: {
            calculatedAt: new Date()
          }
        };
      }
      
      // Émettre un événement de calcul terminé
      this.emit('calculation:complete', {
        type: 'variables',
        employeeCount: Object.keys(variablesData).length
      });
      
      return variablesData;
    } catch (error) {
      this.logger.error('Erreur lors du calcul des variables de paie:', error);
      
      // Émettre un événement d'erreur
      this.emit('calculation:error', {
        type: 'variables',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Construit les données de paie à partir des heures et variables calculées
   * @param {Object} options - Options de construction
   * @param {Object} options.hoursData - Données d'heures
   * @param {Object} options.variablesData - Données de variables
   * @returns {Object} Données de paie complètes
   */
  buildPayrollData({ hoursData, variablesData }) {
    this.logger.debug('Construction des données de paie');
    
    try {
      const payrollData = {};
      
      // Récupérer tous les identifiants d'employés uniques
      const employeeIds = new Set([
        ...Object.keys(hoursData || {}),
        ...Object.keys(variablesData || {})
      ]);
      
      // Construire les données pour chaque employé
      for (const employeeId of employeeIds) {
        // Récupérer les heures et variables
        const employeeHours = hoursData[employeeId]?.hours || {};
        const employeeVariables = variablesData[employeeId]?.variables || {};
        
        // Récupérer les informations de l'employé
        let employeeInfo = {
          employeeId
        };
        
        if (hoursData[employeeId] && hoursData[employeeId].employeeInfo) {
          employeeInfo = { ...employeeInfo, ...hoursData[employeeId].employeeInfo };
        } else if (variablesData[employeeId] && variablesData[employeeId].employeeInfo) {
          employeeInfo = { ...employeeInfo, ...variablesData[employeeId].employeeInfo };
        }
        
        // Construire les données de paie
        payrollData[employeeId] = {
          info: employeeInfo,
          hours: employeeHours,
          variables: employeeVariables,
          metadata: {
            generatedAt: new Date()
          }
        };
      }
      
      // Émettre un événement de construction terminée
      this.emit('calculation:complete', {
        type: 'payroll',
        employeeCount: Object.keys(payrollData).length
      });
      
      return payrollData;
    } catch (error) {
      this.logger.error('Erreur lors de la construction des données de paie:', error);
      
      // Émettre un événement d'erreur
      this.emit('calculation:error', {
        type: 'payroll',
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Calcule les heures de nuit pour une période
   * @param {Object} period - Période à analyser
   * @param {Object} nightHoursConfig - Configuration des heures de nuit
   * @returns {number} Nombre d'heures de nuit
   * @private
   */
  _calculateNightHours(period, nightHoursConfig) {
    // Convertir les heures de début et fin de période en moments
    const periodStart = moment(period.start);
    const periodEnd = moment(period.end);
    
    // Convertir les limites d'heures de nuit en moments
    const startTimeString = nightHoursConfig.start || '22:00';
    const endTimeString = nightHoursConfig.end || '07:00';
    
    // Fonction pour obtenir un moment à une heure spécifique
    const getTimeOnDay = (date, timeString) => {
      const [hours, minutes] = timeString.split(':').map(Number);
      return moment(date).hour(hours).minute(minutes).second(0);
    };
    
    // Pour chaque jour dans la période, calculer les heures de nuit
    let totalNightHours = 0;
    let currentDay = moment(periodStart).startOf('day');
    const lastDay = moment(periodEnd).startOf('day');
    
    while (currentDay.isSameOrBefore(lastDay, 'day')) {
      // Définir les limites de nuit pour ce jour
      const nightStart = getTimeOnDay(currentDay, startTimeString);
      let nightEnd;
      
      // Si l'heure de fin est avant l'heure de début, elle est le jour suivant
      if (endTimeString < startTimeString) {
        nightEnd = getTimeOnDay(moment(currentDay).add(1, 'day'), endTimeString);
      } else {
        nightEnd = getTimeOnDay(currentDay, endTimeString);
      }
      
      // Calculer l'intersection entre la période et les heures de nuit
      const intersectionStart = moment.max(periodStart, nightStart);
      const intersectionEnd = moment.min(periodEnd, nightEnd);
      
      // Si l'intersection est valide, ajouter les heures
      if (intersectionEnd.isAfter(intersectionStart)) {
        const nightHoursOnDay = intersectionEnd.diff(intersectionStart, 'hours', true);
        totalNightHours += nightHoursOnDay;
      }
      
      // Passer au jour suivant
      currentDay.add(1, 'day');
    }
    
    return totalNightHours;
  }
  
  /**
   * Compte le nombre de jours travaillés pour un employé
   * @param {Object} employeeData - Données de présence d'un employé
   * @returns {number} Nombre de jours travaillés
   * @private
   */
  _countWorkDays(employeeData) {
    const workDays = new Set();
    
    // Parcourir les périodes de type 'work'
    if (employeeData.periods) {
      for (const period of employeeData.periods) {
        if (period.type === 'work') {
          // Ajouter le jour au set (format YYYY-MM-DD)
          const day = moment(period.start).format('YYYY-MM-DD');
          workDays.add(day);
        }
      }
    }
    
    return workDays.size;
  }
  
  /**
   * Distribue les pourboires entre les employés
   * @param {Object} attendanceData - Données de présence
   * @param {Object} tipsData - Données de pourboires
   * @returns {Object} Pourboires par employé
   * @private
   */
  _distributeTips(attendanceData, tipsData) {
    const tipsByEmployee = {};
    
    // Vérifier que les données nécessaires sont présentes
    if (!attendanceData || !tipsData || !tipsData.total) {
      return tipsByEmployee;
    }
    
    // Si aucune règle de distribution n'est définie, distribuer également
    if (!this.rules.serviceTips || !this.rules.serviceTips.distributionMethod) {
      const eligibleEmployees = Object.keys(attendanceData).filter(employeeId => {
        const employee = attendanceData[employeeId];
        return employee && employee.periods && employee.periods.some(p => p.type === 'work');
      });
      
      if (eligibleEmployees.length === 0) {
        return tipsByEmployee;
      }
      
      const tipPerEmployee = tipsData.total / eligibleEmployees.length;
      
      for (const employeeId of eligibleEmployees) {
        tipsByEmployee[employeeId] = tipPerEmployee;
      }
      
      return tipsByEmployee;
    }
    
    // Distribution basée sur les points attribués aux rôles
    if (this.rules.serviceTips.distributionMethod === 'points' && this.rules.serviceTips.roles) {
      // Calculer le total des points
      let totalPoints = 0;
      const employeePoints = {};
      
      for (const [employeeId, employeeData] of Object.entries(attendanceData)) {
        if (employeeData.info && employeeData.info.position) {
          const role = employeeData.info.position.toLowerCase();
          let points = 0;
          
          // Chercher les points pour ce rôle
          for (const [roleName, rolePoints] of Object.entries(this.rules.serviceTips.roles)) {
            if (role.includes(roleName.toLowerCase())) {
              points = rolePoints;
              break;
            }
          }
          
          // Si aucun point trouvé, utiliser la valeur par défaut
          if (points === 0) {
            points = 5; // Valeur par défaut
          }
          
          // Ajuster les points en fonction du temps travaillé
          const workHours = this._calculateTotalWorkHours(employeeData);
          const adjustedPoints = points * workHours / 8; // Normaliser pour une journée de 8h
          
          employeePoints[employeeId] = adjustedPoints;
          totalPoints += adjustedPoints;
        }
      }
      
      // Distribuer les pourboires en fonction des points
      if (totalPoints > 0) {
        for (const [employeeId, points] of Object.entries(employeePoints)) {
          tipsByEmployee[employeeId] = (points / totalPoints) * tipsData.total;
        }
      }
    }
    
    return tipsByEmployee;
  }
  
  /**
   * Calcule le nombre total d'heures travaillées pour un employé
   * @param {Object} employeeData - Données de présence d'un employé
   * @returns {number} Nombre total d'heures travaillées
   * @private
   */
  _calculateTotalWorkHours(employeeData) {
    let totalHours = 0;
    
    // Parcourir les périodes de type 'work'
    if (employeeData.periods) {
      for (const period of employeeData.periods) {
        if (period.type === 'work') {
          totalHours += period.duration || 0;
        }
      }
    }
    
    return totalHours;
  }
}

// Exports
module.exports = {
  PayrollCalculator
};
