/**
 * Collecteur de données de présence pour le module de paie
 * Collecte et agrège les données de pointage, planning et congés des employés
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const moment = require('moment');

/**
 * Classe de collecte des données de présence des employés
 * @extends EventEmitter
 */
class AttendanceCollector extends EventEmitter {
  /**
   * Crée une instance du collecteur de données de présence
   * @param {Object} options - Options de configuration
   * @param {boolean} [options.includeValidatedDataOnly=true] - N'inclure que les données validées
   * @param {Object} [options.securityUtils] - Utilitaires de sécurité
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.includeValidatedDataOnly = options.includeValidatedDataOnly !== undefined ? 
      options.includeValidatedDataOnly : true;
    
    this.securityUtils = options.securityUtils;
    this.logger = options.logger || console;
    
    this.logger.debug('AttendanceCollector initialisé');
  }
  
  /**
   * Collecte les données de pointage des employés
   * @param {Object} options - Options de collecte
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données de pointage collectées
   */
  async collectTimeClockData({ startDate, endDate }) {
    this.logger.debug(`Collecte des données de pointage du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Appel à l'API du système de pointage
      const timeClockData = await this._fetchTimeClockData({
        startDate,
        endDate,
        includeValidatedOnly: this.includeValidatedDataOnly
      });
      
      // Formatage des données
      const formattedData = this._formatTimeClockData(timeClockData);
      
      // Structuration par employé
      const structuredData = this._structureDataByEmployee(formattedData);
      
      this.logger.debug(`${Object.keys(structuredData).length} employés trouvés dans les données de pointage`);
      
      // Émettre un événement pour notifier de la collecte
      this.emit('attendance:collected', {
        source: 'timeclock',
        employeeCount: Object.keys(structuredData).length,
        periodStart: startDate,
        periodEnd: endDate
      });
      
      return structuredData;
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de pointage:', error);
      this.emit('attendance:error', {
        source: 'timeclock',
        error: error.message,
        details: error
      });
      throw error;
    }
  }
  
  /**
   * Collecte les données de planning des employés
   * @param {Object} options - Options de collecte
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données de planning collectées
   */
  async collectScheduleData({ startDate, endDate }) {
    this.logger.debug(`Collecte des données de planning du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Appel à l'API du système de planning
      const scheduleData = await this._fetchScheduleData({
        startDate,
        endDate,
        includeValidatedOnly: this.includeValidatedDataOnly
      });
      
      // Formatage des données
      const formattedData = this._formatScheduleData(scheduleData);
      
      // Structuration par employé
      const structuredData = this._structureDataByEmployee(formattedData);
      
      this.logger.debug(`${Object.keys(structuredData).length} employés trouvés dans les données de planning`);
      
      // Émettre un événement pour notifier de la collecte
      this.emit('attendance:collected', {
        source: 'schedule',
        employeeCount: Object.keys(structuredData).length,
        periodStart: startDate,
        periodEnd: endDate
      });
      
      return structuredData;
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de planning:', error);
      this.emit('attendance:error', {
        source: 'schedule',
        error: error.message,
        details: error
      });
      throw error;
    }
  }
  
  /**
   * Collecte les données de congés et absences des employés
   * @param {Object} options - Options de collecte
   * @param {Date} options.startDate - Date de début
   * @param {Date} options.endDate - Date de fin
   * @returns {Promise<Object>} Données de congés collectées
   */
  async collectLeaveData({ startDate, endDate }) {
    this.logger.debug(`Collecte des données de congés du ${moment(startDate).format('DD/MM/YYYY')} au ${moment(endDate).format('DD/MM/YYYY')}`);
    
    try {
      // Appel à l'API du système de gestion des congés
      const leaveData = await this._fetchLeaveData({
        startDate,
        endDate,
        includeValidatedOnly: this.includeValidatedDataOnly
      });
      
      // Formatage des données
      const formattedData = this._formatLeaveData(leaveData);
      
      // Structuration par employé
      const structuredData = this._structureDataByEmployee(formattedData);
      
      this.logger.debug(`${Object.keys(structuredData).length} employés trouvés dans les données de congés`);
      
      // Émettre un événement pour notifier de la collecte
      this.emit('attendance:collected', {
        source: 'leave',
        employeeCount: Object.keys(structuredData).length,
        periodStart: startDate,
        periodEnd: endDate
      });
      
      return structuredData;
    } catch (error) {
      this.logger.error('Erreur lors de la collecte des données de congés:', error);
      this.emit('attendance:error', {
        source: 'leave',
        error: error.message,
        details: error
      });
      throw error;
    }
  }
  
  /**
   * Fusionne les différentes sources de données de présence
   * @param {Object} options - Options de fusion
   * @param {Object} options.timeClockData - Données de pointage
   * @param {Object} options.scheduleData - Données de planning
   * @param {Object} options.leaveData - Données de congés
   * @returns {Object} Données fusionnées
   */
  mergeAttendanceData({ timeClockData, scheduleData, leaveData }) {
    this.logger.debug('Fusion des données de présence');
    
    try {
      // Obtenir la liste complète des employés
      const employees = this._getAllEmployees({ timeClockData, scheduleData, leaveData });
      
      const mergedData = {};
      
      // Pour chaque employé, fusionner les données
      for (const employeeId of employees) {
        const employeeData = {
          employeeId,
          // Récupérer les informations de l'employé (prioriser les sources les plus à jour)
          info: this._getEmployeeInfo(employeeId, { timeClockData, scheduleData, leaveData }),
          // Données de présence, fusionnées et nettoyées
          attendance: this._mergeEmployeeAttendance(employeeId, { timeClockData, scheduleData, leaveData }),
          // Métadonnées
          metadata: {
            sources: {
              timeClock: !!timeClockData?.[employeeId],
              schedule: !!scheduleData?.[employeeId],
              leave: !!leaveData?.[employeeId]
            },
            lastUpdated: new Date()
          }
        };
        
        mergedData[employeeId] = employeeData;
      }
      
      this.logger.debug(`Données fusionnées pour ${Object.keys(mergedData).length} employés`);
      
      return mergedData;
    } catch (error) {
      this.logger.error('Erreur lors de la fusion des données de présence:', error);
      throw error;
    }
  }
  
  /**
   * Récupère les données de pointage depuis l'API
   * @param {Object} options - Options de requête
   * @returns {Promise<Array>} Données de pointage
   * @private
   */
  async _fetchTimeClockData(options) {
    // NOTE: Dans une implémentation réelle, cela ferait un appel à l'API du système de pointage
    // Simulation pour le prototype
    return new Promise((resolve) => {
      setTimeout(() => {
        // Simuler des données de pointage
        const data = [
          {
            employeeId: 'EMP001',
            firstName: 'Jean',
            lastName: 'Dupont',
            position: 'Serveur',
            clockEvents: [
              { type: 'in', timestamp: new Date(2025, 3, 1, 10, 0), validated: true },
              { type: 'break_start', timestamp: new Date(2025, 3, 1, 14, 0), validated: true },
              { type: 'break_end', timestamp: new Date(2025, 3, 1, 14, 30), validated: true },
              { type: 'out', timestamp: new Date(2025, 3, 1, 18, 0), validated: true }
            ]
          },
          {
            employeeId: 'EMP002',
            firstName: 'Marie',
            lastName: 'Martin',
            position: 'Chef de rang',
            clockEvents: [
              { type: 'in', timestamp: new Date(2025, 3, 1, 9, 30), validated: true },
              { type: 'break_start', timestamp: new Date(2025, 3, 1, 13, 30), validated: true },
              { type: 'break_end', timestamp: new Date(2025, 3, 1, 14, 0), validated: true },
              { type: 'out', timestamp: new Date(2025, 3, 1, 17, 30), validated: true }
            ]
          }
        ];
        
        resolve(data);
      }, 200);
    });
  }
  
  /**
   * Récupère les données de planning depuis l'API
   * @param {Object} options - Options de requête
   * @returns {Promise<Array>} Données de planning
   * @private
   */
  async _fetchScheduleData(options) {
    // NOTE: Dans une implémentation réelle, cela ferait un appel à l'API du système de planning
    // Simulation pour le prototype
    return new Promise((resolve) => {
      setTimeout(() => {
        // Simuler des données de planning
        const data = [
          {
            employeeId: 'EMP001',
            firstName: 'Jean',
            lastName: 'Dupont',
            position: 'Serveur',
            schedules: [
              { 
                date: new Date(2025, 3, 1),
                shifts: [
                  { start: new Date(2025, 3, 1, 10, 0), end: new Date(2025, 3, 1, 18, 0), role: 'Serveur', status: 'approved' }
                ]
              },
              { 
                date: new Date(2025, 3, 2),
                shifts: [
                  { start: new Date(2025, 3, 2, 10, 0), end: new Date(2025, 3, 2, 18, 0), role: 'Serveur', status: 'approved' }
                ]
              }
            ]
          },
          {
            employeeId: 'EMP002',
            firstName: 'Marie',
            lastName: 'Martin',
            position: 'Chef de rang',
            schedules: [
              { 
                date: new Date(2025, 3, 1),
                shifts: [
                  { start: new Date(2025, 3, 1, 9, 30), end: new Date(2025, 3, 1, 17, 30), role: 'Chef de rang', status: 'approved' }
                ]
              },
              { 
                date: new Date(2025, 3, 2),
                shifts: [
                  { start: new Date(2025, 3, 2, 9, 30), end: new Date(2025, 3, 2, 17, 30), role: 'Chef de rang', status: 'approved' }
                ]
              }
            ]
          }
        ];
        
        resolve(data);
      }, 200);
    });
  }
  
  /**
   * Récupère les données de congés depuis l'API
   * @param {Object} options - Options de requête
   * @returns {Promise<Array>} Données de congés
   * @private
   */
  async _fetchLeaveData(options) {
    // NOTE: Dans une implémentation réelle, cela ferait un appel à l'API du système de gestion des congés
    // Simulation pour le prototype
    return new Promise((resolve) => {
      setTimeout(() => {
        // Simuler des données de congés
        const data = [
          {
            employeeId: 'EMP001',
            firstName: 'Jean',
            lastName: 'Dupont',
            position: 'Serveur',
            leaves: [
              { 
                type: 'congé payé',
                start: new Date(2025, 3, 3),
                end: new Date(2025, 3, 5),
                status: 'approved',
                duration: 3
              }
            ]
          },
          {
            employeeId: 'EMP003',
            firstName: 'Paul',
            lastName: 'Dubois',
            position: 'Cuisinier',
            leaves: [
              { 
                type: 'maladie',
                start: new Date(2025, 3, 2),
                end: new Date(2025, 3, 2),
                status: 'approved',
                duration: 1
              }
            ]
          }
        ];
        
        resolve(data);
      }, 200);
    });
  }
  
  /**
   * Formate les données de pointage
   * @param {Array} rawData - Données brutes
   * @returns {Array} Données formatées
   * @private
   */
  _formatTimeClockData(rawData) {
    return rawData.map(employee => {
      // Transformer les événements en périodes d'activité
      const periods = [];
      let currentPeriod = null;
      
      for (const event of employee.clockEvents) {
        // Filtrer les données non validées si nécessaire
        if (this.includeValidatedDataOnly && !event.validated) {
          continue;
        }
        
        if (event.type === 'in') {
          // Début d'une nouvelle période
          currentPeriod = {
            start: event.timestamp,
            type: 'work',
            validated: event.validated
          };
        } else if (event.type === 'out' && currentPeriod) {
          // Fin de la période
          currentPeriod.end = event.timestamp;
          currentPeriod.duration = (currentPeriod.end - currentPeriod.start) / (1000 * 60 * 60); // en heures
          periods.push(currentPeriod);
          currentPeriod = null;
        } else if (event.type === 'break_start' && currentPeriod) {
          // Marquer la fin de la période de travail
          const workPeriod = { ...currentPeriod };
          workPeriod.end = event.timestamp;
          workPeriod.duration = (workPeriod.end - workPeriod.start) / (1000 * 60 * 60); // en heures
          periods.push(workPeriod);
          
          // Début d'une période de pause
          currentPeriod = {
            start: event.timestamp,
            type: 'break',
            validated: event.validated
          };
        } else if (event.type === 'break_end' && currentPeriod && currentPeriod.type === 'break') {
          // Fin de la période de pause
          currentPeriod.end = event.timestamp;
          currentPeriod.duration = (currentPeriod.end - currentPeriod.start) / (1000 * 60 * 60); // en heures
          periods.push(currentPeriod);
          
          // Début d'une nouvelle période de travail
          currentPeriod = {
            start: event.timestamp,
            type: 'work',
            validated: event.validated
          };
        }
      }
      
      return {
        ...employee,
        periods
      };
    });
  }
  
  /**
   * Formate les données de planning
   * @param {Array} rawData - Données brutes
   * @returns {Array} Données formatées
   * @private
   */
  _formatScheduleData(rawData) {
    return rawData.map(employee => {
      // Transformer les shifts en périodes d'activité
      const periods = [];
      
      for (const schedule of employee.schedules) {
        for (const shift of schedule.shifts) {
          // Filtrer les données non approuvées si nécessaire
          if (this.includeValidatedDataOnly && shift.status !== 'approved') {
            continue;
          }
          
          periods.push({
            start: shift.start,
            end: shift.end,
            type: 'scheduled',
            role: shift.role,
            duration: (shift.end - shift.start) / (1000 * 60 * 60), // en heures
            validated: shift.status === 'approved'
          });
        }
      }
      
      return {
        ...employee,
        periods
      };
    });
  }
  
  /**
   * Formate les données de congés
   * @param {Array} rawData - Données brutes
   * @returns {Array} Données formatées
   * @private
   */
  _formatLeaveData(rawData) {
    return rawData.map(employee => {
      // Transformer les congés en périodes d'absence
      const periods = [];
      
      for (const leave of employee.leaves) {
        // Filtrer les données non approuvées si nécessaire
        if (this.includeValidatedDataOnly && leave.status !== 'approved') {
          continue;
        }
        
        // Pour chaque jour de congé, créer une période d'absence
        const startDate = moment(leave.start);
        const endDate = moment(leave.end);
        let currentDate = startDate.clone();
        
        while (currentDate.isSameOrBefore(endDate, 'day')) {
          periods.push({
            start: currentDate.clone().hours(9).minutes(0).toDate(), // Début de journée standard
            end: currentDate.clone().hours(18).minutes(0).toDate(), // Fin de journée standard
            type: 'leave',
            leaveType: leave.type,
            duration: 9, // Journée standard de 9h
            validated: leave.status === 'approved'
          });
          
          currentDate.add(1, 'day');
        }
      }
      
      return {
        ...employee,
        periods
      };
    });
  }
  
  /**
   * Structure les données par employé
   * @param {Array} formattedData - Données formatées
   * @returns {Object} Données structurées par employé
   * @private
   */
  _structureDataByEmployee(formattedData) {
    const structuredData = {};
    
    for (const employee of formattedData) {
      structuredData[employee.employeeId] = {
        info: {
          employeeId: employee.employeeId,
          firstName: employee.firstName,
          lastName: employee.lastName,
          position: employee.position
        },
        periods: employee.periods || []
      };
    }
    
    return structuredData;
  }
  
  /**
   * Obtient la liste complète des employés de toutes les sources
   * @param {Object} options - Options
   * @returns {Array} Liste des identifiants d'employés
   * @private
   */
  _getAllEmployees({ timeClockData, scheduleData, leaveData }) {
    const employeeSet = new Set();
    
    // Ajouter les employés des données de pointage
    if (timeClockData) {
      Object.keys(timeClockData).forEach(employeeId => employeeSet.add(employeeId));
    }
    
    // Ajouter les employés des données de planning
    if (scheduleData) {
      Object.keys(scheduleData).forEach(employeeId => employeeSet.add(employeeId));
    }
    
    // Ajouter les employés des données de congés
    if (leaveData) {
      Object.keys(leaveData).forEach(employeeId => employeeSet.add(employeeId));
    }
    
    return Array.from(employeeSet);
  }
  
  /**
   * Récupère les informations d'un employé (priorise les sources les plus complètes)
   * @param {string} employeeId - Identifiant de l'employé
   * @param {Object} options - Options
   * @returns {Object} Informations de l'employé
   * @private
   */
  _getEmployeeInfo(employeeId, { timeClockData, scheduleData, leaveData }) {
    // Chercher dans les différentes sources, par ordre de priorité
    const sources = [timeClockData, scheduleData, leaveData].filter(source => source && source[employeeId]);
    
    if (sources.length === 0) {
      return { employeeId, firstName: '', lastName: '', position: '' };
    }
    
    // Récupérer la première source disponible
    return sources[0][employeeId].info;
  }
  
  /**
   * Fusionne les données de présence d'un employé
   * @param {string} employeeId - Identifiant de l'employé
   * @param {Object} options - Options
   * @returns {Object} Données de présence fusionnées
   * @private
   */
  _mergeEmployeeAttendance(employeeId, { timeClockData, scheduleData, leaveData }) {
    // Initialiser avec un tableau vide
    let allPeriods = [];
    
    // Ajouter les périodes de pointage
    if (timeClockData && timeClockData[employeeId]) {
      allPeriods = allPeriods.concat(timeClockData[employeeId].periods.map(period => ({
        ...period,
        source: 'timeclock'
      })));
    }
    
    // Ajouter les périodes de planning
    if (scheduleData && scheduleData[employeeId]) {
      allPeriods = allPeriods.concat(scheduleData[employeeId].periods.map(period => ({
        ...period,
        source: 'schedule'
      })));
    }
    
    // Ajouter les périodes de congés
    if (leaveData && leaveData[employeeId]) {
      allPeriods = allPeriods.concat(leaveData[employeeId].periods.map(period => ({
        ...period,
        source: 'leave'
      })));
    }
    
    // Trier les périodes par date de début
    allPeriods.sort((a, b) => a.start - b.start);
    
    // Détecter et résoudre les chevauchements
    const mergedPeriods = this._resolveOverlaps(allPeriods);
    
    // Regrouper par jour
    const periodsByDay = this._groupPeriodsByDay(mergedPeriods);
    
    return {
      periods: mergedPeriods,
      periodsByDay
    };
  }
  
  /**
   * Résout les chevauchements dans les périodes
   * @param {Array} periods - Périodes à vérifier
   * @returns {Array} Périodes sans chevauchement
   * @private
   */
  _resolveOverlaps(periods) {
    if (periods.length <= 1) {
      return periods;
    }
    
    // Trier par date de début
    const sortedPeriods = [...periods].sort((a, b) => a.start - b.start);
    const result = [sortedPeriods[0]];
    
    for (let i = 1; i < sortedPeriods.length; i++) {
      const currentPeriod = sortedPeriods[i];
      const lastPeriod = result[result.length - 1];
      
      // Vérifier s'il y a chevauchement
      if (currentPeriod.start < lastPeriod.end) {
        // Priorité basée sur le type de période
        const priorityOrder = {
          'leave': 3, // Plus haute priorité
          'work': 2,
          'break': 1,
          'scheduled': 0 // Plus basse priorité
        };
        
        const currentPriority = priorityOrder[currentPeriod.type] || 0;
        const lastPriority = priorityOrder[lastPeriod.type] || 0;
        
        if (currentPriority > lastPriority) {
          // La période actuelle a une priorité plus élevée
          
          // Si la période actuelle commence après le début de la dernière période
          if (currentPeriod.start > lastPeriod.start) {
            // Réduire la durée de la dernière période
            lastPeriod.end = currentPeriod.start;
            lastPeriod.duration = (lastPeriod.end - lastPeriod.start) / (1000 * 60 * 60);
            
            // Ajouter la période actuelle
            result.push(currentPeriod);
          } else {
            // Remplacer complètement la dernière période
            result[result.length - 1] = currentPeriod;
          }
        } else if (currentPriority === lastPriority) {
          // Même priorité, fusion ou extension selon le type
          if (currentPeriod.type === lastPeriod.type) {
            // Même type, étendre la période
            if (currentPeriod.end > lastPeriod.end) {
              lastPeriod.end = currentPeriod.end;
              lastPeriod.duration = (lastPeriod.end - lastPeriod.start) / (1000 * 60 * 60);
            }
          } else {
            // Types différents mais même priorité, la dernière ajoutée gagne
            // Tronquer à la fin de la période actuelle
            if (currentPeriod.end > lastPeriod.end) {
              currentPeriod.start = lastPeriod.end;
              currentPeriod.duration = (currentPeriod.end - currentPeriod.start) / (1000 * 60 * 60);
              
              if (currentPeriod.duration > 0) {
                result.push(currentPeriod);
              }
            }
          }
        } else {
          // La période actuelle a une priorité plus basse
          
          // Si la période actuelle se termine après la dernière période
          if (currentPeriod.end > lastPeriod.end) {
            // Tronquer le début de la période actuelle
            currentPeriod.start = lastPeriod.end;
            currentPeriod.duration = (currentPeriod.end - currentPeriod.start) / (1000 * 60 * 60);
            
            if (currentPeriod.duration > 0) {
              result.push(currentPeriod);
            }
          }
          // Sinon, la période actuelle est complètement incluse dans la dernière et est ignorée
        }
      } else {
        // Pas de chevauchement, ajouter simplement la période
        result.push(currentPeriod);
      }
    }
    
    return result;
  }
  
  /**
   * Regroupe les périodes par jour
   * @param {Array} periods - Périodes à regrouper
   * @returns {Object} Périodes regroupées par jour
   * @private
   */
  _groupPeriodsByDay(periods) {
    const periodsByDay = {};
    
    for (const period of periods) {
      const startDay = moment(period.start).format('YYYY-MM-DD');
      const endDay = moment(period.end).format('YYYY-MM-DD');
      
      // Si la période s'étend sur plusieurs jours, la diviser
      if (startDay === endDay) {
        // Période sur un seul jour
        if (!periodsByDay[startDay]) {
          periodsByDay[startDay] = [];
        }
        
        periodsByDay[startDay].push(period);
      } else {
        // Période sur plusieurs jours
        let currentDay = moment(period.start);
        const lastDay = moment(period.end);
        
        while (currentDay.isSameOrBefore(lastDay, 'day')) {
          const dayStr = currentDay.format('YYYY-MM-DD');
          if (!periodsByDay[dayStr]) {
            periodsByDay[dayStr] = [];
          }
          
          // Créer une période pour ce jour
          let dayStart, dayEnd;
          
          if (currentDay.isSame(moment(period.start), 'day')) {
            // Premier jour
            dayStart = period.start;
          } else {
            // Jours intermédiaires (début à minuit)
            dayStart = currentDay.clone().startOf('day').toDate();
          }
          
          if (currentDay.isSame(moment(period.end), 'day')) {
            // Dernier jour
            dayEnd = period.end;
          } else {
            // Jours intermédiaires (fin à 23:59:59)
            dayEnd = currentDay.clone().endOf('day').toDate();
          }
          
          periodsByDay[dayStr].push({
            ...period,
            start: dayStart,
            end: dayEnd,
            duration: (dayEnd - dayStart) / (1000 * 60 * 60) // en heures
          });
          
          // Passer au jour suivant
          currentDay.add(1, 'day');
        }
      }
    }
    
    return periodsByDay;
  }
}

// Exports
module.exports = {
  AttendanceCollector
};
