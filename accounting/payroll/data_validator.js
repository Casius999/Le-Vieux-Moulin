/**
 * Validateur de données pour le module de paie
 * Vérifie la cohérence et l'intégrité des données de présence et de paie
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const moment = require('moment');

/**
 * Classe de validation des données de paie
 * @extends EventEmitter
 */
class DataValidator extends EventEmitter {
  /**
   * Crée une instance du validateur de données
   * @param {Object} options - Options de configuration
   * @param {Object} [options.rules] - Règles de validation
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.rules = options.rules || {};
    this.logger = options.logger || console;
    
    this.logger.debug('DataValidator initialisé');
  }
  
  /**
   * Valide les données de présence des employés
   * @param {Object} attendanceData - Données de présence à valider
   * @returns {Object} Résultats de validation
   */
  validateAttendanceData(attendanceData) {
    this.logger.debug('Validation des données de présence');
    
    const warnings = [];
    const errors = [];
    
    // Vérifier que les données sont présentes
    if (!attendanceData || Object.keys(attendanceData).length === 0) {
      errors.push({
        code: 'EMPTY_DATA',
        message: 'Aucune donnée de présence à valider'
      });
      
      return { isValid: errors.length === 0, warnings, errors };
    }
    
    // Parcourir chaque employé
    for (const [employeeId, employeeData] of Object.entries(attendanceData)) {
      // Vérifier que les informations de base sont présentes
      if (!employeeData.info || !employeeData.info.employeeId) {
        errors.push({
          code: 'MISSING_EMPLOYEE_INFO',
          message: `Informations manquantes pour l'employé ${employeeId}`,
          employeeId
        });
        continue;
      }
      
      // Vérifier les périodes
      if (!employeeData.periods || employeeData.periods.length === 0) {
        warnings.push({
          code: 'NO_PERIODS',
          message: `Aucune période pour l'employé ${employeeId}`,
          employeeId,
          employee: employeeData.info
        });
        continue;
      }
      
      // Vérifier chaque période
      for (let i = 0; i < employeeData.periods.length; i++) {
        const period = employeeData.periods[i];
        
        // Valider les dates
        if (!period.start || !period.end) {
          errors.push({
            code: 'MISSING_PERIOD_DATES',
            message: `Dates manquantes pour une période de l'employé ${employeeId}`,
            employeeId,
            periodIndex: i
          });
          continue;
        }
        
        // Vérifier que la date de début est avant la date de fin
        if (period.start >= period.end) {
          errors.push({
            code: 'INVALID_PERIOD_DATES',
            message: `Période invalide: la date de début (${moment(period.start).format('DD/MM/YYYY HH:mm')}) est après la date de fin (${moment(period.end).format('DD/MM/YYYY HH:mm')})`,
            employeeId,
            employee: employeeData.info,
            periodIndex: i,
            period
          });
        }
        
        // Vérifier que la durée est cohérente avec les dates
        const calculatedDuration = (period.end - period.start) / (1000 * 60 * 60); // en heures
        const durationDiff = Math.abs(calculatedDuration - (period.duration || 0));
        
        if (durationDiff > 0.01) { // Tolérance de 0.01h (36 secondes)
          warnings.push({
            code: 'INCONSISTENT_DURATION',
            message: `Durée incohérente pour une période de l'employé ${employeeId}`,
            employeeId,
            employee: employeeData.info,
            periodIndex: i,
            period,
            calculatedDuration,
            difference: durationDiff
          });
        }
        
        // Vérifier les périodes excessivement longues
        if (this.rules.workingHours && calculatedDuration > this.rules.workingHours.maxDailyHours) {
          warnings.push({
            code: 'EXCESSIVE_DURATION',
            message: `Période de travail excessivement longue pour l'employé ${employeeId} (${calculatedDuration.toFixed(2)}h, max: ${this.rules.workingHours.maxDailyHours}h)`,
            employeeId,
            employee: employeeData.info,
            periodIndex: i,
            period,
            duration: calculatedDuration,
            maxAllowed: this.rules.workingHours.maxDailyHours
          });
        }
      }
      
      // Vérifier les chevauchements de périodes
      this._checkPeriodOverlaps(employeeId, employeeData, warnings, errors);
    }
    
    // Émettre les événements pour les avertissements et erreurs
    if (warnings.length > 0) {
      this.emit('validation:warning', {
        type: 'attendance',
        warnings
      });
    }
    
    if (errors.length > 0) {
      this.emit('validation:error', {
        type: 'attendance',
        errors
      });
    }
    
    return {
      isValid: errors.length === 0,
      warnings,
      errors
    };
  }
  
  /**
   * Valide les données de paie
   * @param {Object} payrollData - Données de paie à valider
   * @returns {Object} Résultats de validation
   */
  validatePayrollData(payrollData) {
    this.logger.debug('Validation des données de paie');
    
    const warnings = [];
    const errors = [];
    
    // Vérifier que les données sont présentes
    if (!payrollData || Object.keys(payrollData).length === 0) {
      errors.push({
        code: 'EMPTY_DATA',
        message: 'Aucune donnée de paie à valider'
      });
      
      return { isValid: errors.length === 0, warnings, errors };
    }
    
    // Parcourir chaque employé
    for (const [employeeId, employeeData] of Object.entries(payrollData)) {
      // Vérifier que les informations de base sont présentes
      if (!employeeData.info || !employeeData.info.employeeId) {
        errors.push({
          code: 'MISSING_EMPLOYEE_INFO',
          message: `Informations manquantes pour l'employé ${employeeId}`,
          employeeId
        });
        continue;
      }
      
      // Vérifier que les heures sont présentes
      if (!employeeData.hours) {
        errors.push({
          code: 'MISSING_HOURS',
          message: `Heures manquantes pour l'employé ${employeeId}`,
          employeeId,
          employee: employeeData.info
        });
      } else {
        // Vérifier les heures négatives
        if (employeeData.hours.regular < 0 || 
            employeeData.hours.overtime < 0 || 
            employeeData.hours.night < 0) {
          errors.push({
            code: 'NEGATIVE_HOURS',
            message: `Heures négatives détectées pour l'employé ${employeeId}`,
            employeeId,
            employee: employeeData.info,
            hours: employeeData.hours
          });
        }
        
        // Vérifier les heures excessives
        const totalHours = (employeeData.hours.regular || 0) + 
                         (employeeData.hours.overtime || 0) + 
                         (employeeData.hours.night || 0);
        
        if (this.rules.workingHours && 
            this.rules.workingHours.maxWeeklyHours && 
            totalHours > this.rules.workingHours.maxWeeklyHours) {
          warnings.push({
            code: 'EXCESSIVE_WEEKLY_HOURS',
            message: `Heures hebdomadaires excessives pour l'employé ${employeeId} (${totalHours.toFixed(2)}h, max: ${this.rules.workingHours.maxWeeklyHours}h)`,
            employeeId,
            employee: employeeData.info,
            hours: employeeData.hours,
            totalHours,
            maxAllowed: this.rules.workingHours.maxWeeklyHours
          });
        }
      }
      
      // Vérifier les variables de paie
      if (employeeData.variables) {
        for (const [variableKey, variableValue] of Object.entries(employeeData.variables)) {
          // Vérifier les valeurs négatives pour certaines variables
          if (['service_charge', 'bonus', 'commission'].includes(variableKey) && variableValue < 0) {
            warnings.push({
              code: 'NEGATIVE_VARIABLE',
              message: `Variable de paie négative (${variableKey}: ${variableValue}) pour l'employé ${employeeId}`,
              employeeId,
              employee: employeeData.info,
              variable: variableKey,
              value: variableValue
            });
          }
          
          // Vérifier les valeurs exceptionnellement élevées
          if (variableValue > 1000) { // Seuil arbitraire, à adapter
            warnings.push({
              code: 'HIGH_VARIABLE_VALUE',
              message: `Valeur élevée pour la variable ${variableKey} (${variableValue}) pour l'employé ${employeeId}`,
              employeeId,
              employee: employeeData.info,
              variable: variableKey,
              value: variableValue
            });
          }
        }
      }
    }
    
    // Émettre les événements pour les avertissements et erreurs
    if (warnings.length > 0) {
      this.emit('validation:warning', {
        type: 'payroll',
        warnings
      });
    }
    
    if (errors.length > 0) {
      this.emit('validation:error', {
        type: 'payroll',
        errors
      });
    }
    
    return {
      isValid: errors.length === 0,
      warnings,
      errors
    };
  }
  
  /**
   * Effectue une validation complète des données de paie
   * @param {Object} options - Options de validation
   * @param {Object} options.attendanceData - Données de présence
   * @param {Object} options.payrollData - Données de paie
   * @returns {Object} Résultats de validation
   */
  performFullValidation({ attendanceData, payrollData }) {
    this.logger.debug('Validation complète des données de paie');
    
    const attendanceValidation = this.validateAttendanceData(attendanceData);
    const payrollValidation = this.validatePayrollData(payrollData);
    
    // Effectuer des validations croisées entre les données de présence et de paie
    const crossValidation = this._performCrossValidation({ attendanceData, payrollData });
    
    // Fusionner les résultats
    const result = {
      isValid: attendanceValidation.isValid && payrollValidation.isValid && crossValidation.isValid,
      attendance: attendanceValidation,
      payroll: payrollValidation,
      cross: crossValidation,
      summary: {
        totalWarnings: attendanceValidation.warnings.length + 
                      payrollValidation.warnings.length + 
                      crossValidation.warnings.length,
        totalErrors: attendanceValidation.errors.length + 
                    payrollValidation.errors.length + 
                    crossValidation.errors.length
      }
    };
    
    return result;
  }
  
  /**
   * Effectue des validations croisées entre les données de présence et de paie
   * @param {Object} options - Options de validation
   * @param {Object} options.attendanceData - Données de présence
   * @param {Object} options.payrollData - Données de paie
   * @returns {Object} Résultats de validation
   * @private
   */
  _performCrossValidation({ attendanceData, payrollData }) {
    const warnings = [];
    const errors = [];
    
    // Vérifier que tous les employés des données de paie sont présents dans les données de présence
    if (payrollData) {
      for (const employeeId of Object.keys(payrollData)) {
        if (!attendanceData || !attendanceData[employeeId]) {
          warnings.push({
            code: 'EMPLOYEE_NOT_IN_ATTENDANCE',
            message: `L'employé ${employeeId} est présent dans les données de paie mais pas dans les données de présence`,
            employeeId,
            employee: payrollData[employeeId].info
          });
        }
      }
    }
    
    // Vérifier la cohérence des heures entre les données de présence et de paie
    if (attendanceData && payrollData) {
      for (const employeeId of Object.keys(attendanceData)) {
        if (payrollData[employeeId]) {
          // Calculer le total des heures dans les données de présence
          const attendancePeriods = attendanceData[employeeId].periods || [];
          const attendanceHours = attendancePeriods.reduce((total, period) => {
            // Ne compter que les périodes de type 'work'
            if (period.type === 'work') {
              return total + (period.duration || 0);
            }
            return total;
          }, 0);
          
          // Récupérer le total des heures dans les données de paie
          const payrollHours = payrollData[employeeId].hours || {};
          const totalPayrollHours = (payrollHours.regular || 0) + 
                                   (payrollHours.overtime || 0) + 
                                   (payrollHours.night || 0);
          
          // Comparer les totaux avec une marge de tolérance
          const hoursDiff = Math.abs(attendanceHours - totalPayrollHours);
          if (hoursDiff > 0.5) { // Tolérance de 30 minutes
            warnings.push({
              code: 'HOURS_MISMATCH',
              message: `Incohérence des heures pour l'employé ${employeeId}: ${attendanceHours.toFixed(2)}h (présence) vs ${totalPayrollHours.toFixed(2)}h (paie)`,
              employeeId,
              employee: attendanceData[employeeId].info,
              attendanceHours,
              payrollHours: totalPayrollHours,
              difference: hoursDiff
            });
          }
        }
      }
    }
    
    return {
      isValid: errors.length === 0,
      warnings,
      errors
    };
  }
  
  /**
   * Vérifie les chevauchements dans les périodes d'un employé
   * @param {string} employeeId - Identifiant de l'employé
   * @param {Object} employeeData - Données de l'employé
   * @param {Array} warnings - Liste des avertissements à compléter
   * @param {Array} errors - Liste des erreurs à compléter
   * @private
   */
  _checkPeriodOverlaps(employeeId, employeeData, warnings, errors) {
    const periods = employeeData.periods || [];
    
    // Trier les périodes par date de début
    const sortedPeriods = [...periods].sort((a, b) => a.start - b.start);
    
    for (let i = 0; i < sortedPeriods.length - 1; i++) {
      const currentPeriod = sortedPeriods[i];
      const nextPeriod = sortedPeriods[i + 1];
      
      // Vérifier s'il y a chevauchement
      if (currentPeriod.end > nextPeriod.start) {
        // Si les deux périodes sont du même type, c'est probablement une erreur
        if (currentPeriod.type === nextPeriod.type) {
          errors.push({
            code: 'OVERLAPPING_PERIODS',
            message: `Périodes chevauchantes de même type pour l'employé ${employeeId}`,
            employeeId,
            employee: employeeData.info,
            periods: [currentPeriod, nextPeriod],
            overlap: {
              start: nextPeriod.start,
              end: currentPeriod.end,
              duration: (currentPeriod.end - nextPeriod.start) / (1000 * 60 * 60) // en heures
            }
          });
        } else {
          // Si les types sont différents, c'est peut-être intentionnel (ex: travail et pause)
          warnings.push({
            code: 'OVERLAPPING_DIFFERENT_PERIODS',
            message: `Périodes chevauchantes de types différents pour l'employé ${employeeId}`,
            employeeId,
            employee: employeeData.info,
            periods: [currentPeriod, nextPeriod],
            overlap: {
              start: nextPeriod.start,
              end: currentPeriod.end,
              duration: (currentPeriod.end - nextPeriod.start) / (1000 * 60 * 60) // en heures
            }
          });
        }
      }
    }
  }
}

// Exports
module.exports = {
  DataValidator
};
