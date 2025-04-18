/**
 * Exportateur de paie pour le restaurant "Le Vieux Moulin"
 * Génère des exports pour les logiciels de paie et des rapports de validation
 */

'use strict';

// Importation des dépendances
const { EventEmitter } = require('events');
const fs = require('fs').promises;
const path = require('path');
const moment = require('moment');
const csvStringify = require('csv-stringify/lib/sync');
const ExcelJS = require('exceljs');
const PDFDocument = require('pdfkit');

/**
 * Classe d'export des données de paie
 * @extends EventEmitter
 */
class PayrollExporter extends EventEmitter {
  /**
   * Crée une instance de l'exportateur de paie
   * @param {Object} options - Options de configuration
   * @param {Object} [options.securityUtils] - Utilitaires de sécurité
   * @param {Object} [options.logger] - Logger à utiliser
   */
  constructor(options = {}) {
    super();
    
    this.securityUtils = options.securityUtils;
    this.logger = options.logger || console;
    
    this.logger.debug('PayrollExporter initialisé');
  }
  
  /**
   * Exporte les données de paie vers un format spécifique
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie à exporter
   * @param {string} options.format - Format d'export ('csv', 'excel', 'sage', 'silae', 'adp', 'dsn')
   * @param {string} options.outputPath - Chemin de sortie du fichier
   * @param {Object} [options.metadata] - Métadonnées à inclure
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async exportPayrollData({ data, format, outputPath, metadata = {} }) {
    this.logger.debug(`Export des données de paie au format ${format} vers ${outputPath}`);
    
    try {
      // Sélectionner la méthode d'export en fonction du format
      let exportFunction;
      
      switch (format.toLowerCase()) {
        case 'csv':
          exportFunction = this._exportToCSV;
          break;
        case 'excel':
          exportFunction = this._exportToExcel;
          break;
        case 'sage':
          exportFunction = this._exportToSage;
          break;
        case 'silae':
          exportFunction = this._exportToSilae;
          break;
        case 'adp':
          exportFunction = this._exportToADP;
          break;
        case 'dsn':
          exportFunction = this._exportToDSN;
          break;
        default:
          throw new Error(`Format d'export non pris en charge: ${format}`);
      }
      
      // Effectuer l'export
      await exportFunction.call(this, { data, outputPath, metadata });
      
      // Émettre un événement d'export terminé
      this.emit('export:complete', {
        format,
        path: outputPath,
        employeeCount: Object.keys(data).length,
        metadata
      });
      
      return outputPath;
    } catch (error) {
      this.logger.error(`Erreur lors de l'export des données de paie au format ${format}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('export:error', {
        format,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Génère un rapport de validation pour le manager
   * @param {Object} options - Options de génération
   * @param {Object} options.validationResult - Résultats de validation
   * @param {Object} options.payrollData - Données de paie
   * @param {string} options.format - Format du rapport ('pdf', 'html', 'excel')
   * @param {string} options.outputPath - Chemin de sortie du fichier
   * @param {Object} [options.metadata] - Métadonnées à inclure
   * @returns {Promise<string>} Chemin du fichier généré
   */
  async generateValidationReport({ validationResult, payrollData, format, outputPath, metadata = {} }) {
    this.logger.debug(`Génération du rapport de validation au format ${format} vers ${outputPath}`);
    
    try {
      // Sélectionner la méthode de génération en fonction du format
      let generateFunction;
      
      switch (format.toLowerCase()) {
        case 'pdf':
          generateFunction = this._generateValidationPDF;
          break;
        case 'html':
          generateFunction = this._generateValidationHTML;
          break;
        case 'excel':
          generateFunction = this._generateValidationExcel;
          break;
        default:
          throw new Error(`Format de rapport non pris en charge: ${format}`);
      }
      
      // Effectuer la génération
      await generateFunction.call(this, { validationResult, payrollData, outputPath, metadata });
      
      // Émettre un événement de génération terminée
      this.emit('report:complete', {
        type: 'validation',
        format,
        path: outputPath,
        metadata
      });
      
      return outputPath;
    } catch (error) {
      this.logger.error(`Erreur lors de la génération du rapport de validation au format ${format}:`, error);
      
      // Émettre un événement d'erreur
      this.emit('report:error', {
        type: 'validation',
        format,
        error: error.message,
        details: error
      });
      
      throw error;
    }
  }
  
  /**
   * Exporte les données de paie au format CSV
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToCSV({ data, outputPath, metadata }) {
    // Préparer les données pour le CSV
    const csvRows = [];
    
    // En-tête du CSV
    const headers = [
      'Matricule',
      'Nom',
      'Prénom',
      'Poste',
      'Heures régulières',
      'Heures supplémentaires',
      'Heures de nuit',
      'Total des heures',
      'Prime de service',
      'Pourboires',
      'Indemnité repas',
      'Indemnité transport',
      'Bonus',
      'Commission',
      'Divers ajouts',
      'Divers déductions'
    ];
    
    csvRows.push(headers);
    
    // Ajouter les données de chaque employé
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      const row = [
        employeeId,
        info.lastName || '',
        info.firstName || '',
        info.position || '',
        hours.regular || 0,
        hours.overtime || 0,
        hours.night || 0,
        hours.total || 0,
        variables.service_charge || 0,
        variables.tips || 0,
        variables.meal_allowance || 0,
        variables.transport_allowance || 0,
        variables.bonus || 0,
        variables.commission || 0,
        variables.sundry_additions || 0,
        variables.sundry_deductions || 0
      ];
      
      csvRows.push(row);
    }
    
    // Générer la chaîne CSV
    const csvContent = csvStringify(csvRows, {
      delimiter: ';', // Délimiteur pour compatibilité française
      header: false,  // L'en-tête est déjà incluse
      quoted: true    // Mettre les valeurs entre guillemets
    });
    
    // Ajouter des métadonnées en commentaire
    const metadataLines = [
      `# Export de paie - Le Vieux Moulin`,
      `# Date d'export: ${moment().format('DD/MM/YYYY HH:mm:ss')}`,
      `# Période: ${moment(metadata.startDate).format('DD/MM/YYYY')} - ${moment(metadata.endDate).format('DD/MM/YYYY')}`,
      `# Nombre d'employés: ${Object.keys(data).length}`,
      `#`
    ];
    
    // Combiner les métadonnées et le contenu CSV
    const fileContent = [...metadataLines, csvContent].join('\n');
    
    // Écrire le fichier
    await fs.writeFile(outputPath, fileContent, 'utf8');
  }
  
  /**
   * Exporte les données de paie au format Excel
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToExcel({ data, outputPath, metadata }) {
    // Créer un nouveau classeur
    const workbook = new ExcelJS.Workbook();
    
    // Ajouter des propriétés au classeur
    workbook.creator = 'Le Vieux Moulin - Module de Paie';
    workbook.lastModifiedBy = 'Système automatisé';
    workbook.created = new Date();
    workbook.modified = new Date();
    
    // Créer une feuille pour les données de paie
    const payrollSheet = workbook.addWorksheet('Données de paie');
    
    // Définir les colonnes
    payrollSheet.columns = [
      { header: 'Matricule', key: 'id', width: 12 },
      { header: 'Nom', key: 'lastName', width: 20 },
      { header: 'Prénom', key: 'firstName', width: 20 },
      { header: 'Poste', key: 'position', width: 20 },
      { header: 'Heures régulières', key: 'regularHours', width: 15 },
      { header: 'Heures supplémentaires', key: 'overtimeHours', width: 15 },
      { header: 'Heures de nuit', key: 'nightHours', width: 15 },
      { header: 'Total des heures', key: 'totalHours', width: 15 },
      { header: 'Prime de service', key: 'serviceCharge', width: 15 },
      { header: 'Pourboires', key: 'tips', width: 15 },
      { header: 'Indemnité repas', key: 'mealAllowance', width: 15 },
      { header: 'Indemnité transport', key: 'transportAllowance', width: 15 },
      { header: 'Bonus', key: 'bonus', width: 15 },
      { header: 'Commission', key: 'commission', width: 15 },
      { header: 'Divers ajouts', key: 'sundryAdditions', width: 15 },
      { header: 'Divers déductions', key: 'sundryDeductions', width: 15 }
    ];
    
    // Mettre en forme l'en-tête
    payrollSheet.getRow(1).font = { bold: true };
    payrollSheet.getRow(1).alignment = { vertical: 'middle', horizontal: 'center' };
    
    // Ajouter les données de chaque employé
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      payrollSheet.addRow({
        id: employeeId,
        lastName: info.lastName || '',
        firstName: info.firstName || '',
        position: info.position || '',
        regularHours: hours.regular || 0,
        overtimeHours: hours.overtime || 0,
        nightHours: hours.night || 0,
        totalHours: hours.total || 0,
        serviceCharge: variables.service_charge || 0,
        tips: variables.tips || 0,
        mealAllowance: variables.meal_allowance || 0,
        transportAllowance: variables.transport_allowance || 0,
        bonus: variables.bonus || 0,
        commission: variables.commission || 0,
        sundryAdditions: variables.sundry_additions || 0,
        sundryDeductions: variables.sundry_deductions || 0
      });
    }
    
    // Ajouter une feuille de métadonnées
    const metadataSheet = workbook.addWorksheet('Métadonnées');
    
    metadataSheet.columns = [
      { header: 'Clé', key: 'key', width: 30 },
      { header: 'Valeur', key: 'value', width: 50 }
    ];
    
    metadataSheet.getRow(1).font = { bold: true };
    
    // Ajouter les métadonnées
    metadataSheet.addRow({ key: 'Nom de l\'entreprise', value: 'Le Vieux Moulin' });
    metadataSheet.addRow({ key: 'Date d\'export', value: moment().format('DD/MM/YYYY HH:mm:ss') });
    metadataSheet.addRow({ key: 'Période de début', value: metadata.startDate ? moment(metadata.startDate).format('DD/MM/YYYY') : '' });
    metadataSheet.addRow({ key: 'Période de fin', value: metadata.endDate ? moment(metadata.endDate).format('DD/MM/YYYY') : '' });
    metadataSheet.addRow({ key: 'Nombre d\'employés', value: Object.keys(data).length });
    metadataSheet.addRow({ key: 'Généré par', value: 'Module de paie automatisé' });
    
    // Créer une mise en forme conditionnelle pour les montants négatifs
    const conditionalFormatting = {
      type: 'cellIs',
      operator: 'lessThan',
      formulae: [0],
      style: { font: { color: { argb: 'FFFF0000' } } }
    };
    
    // Appliquer à toutes les colonnes numériques
    for (let col = 5; col <= 16; col++) {
      payrollSheet.getColumn(col).numFmt = '0.00';
      payrollSheet.getColumn(col).alignment = { horizontal: 'right' };
      payrollSheet.getColumn(col).eachCell({ includeEmpty: false }, (cell, rowNumber) => {
        if (rowNumber > 1) { // Exclure l'en-tête
          cell.numFmt = '0.00';
        }
      });
      
      // Ajouter le formatage conditionnel
      payrollSheet.addConditionalFormatting({
        ref: payrollSheet.getColumn(col).letter + '2:' + payrollSheet.getColumn(col).letter + (Object.keys(data).length + 1),
        ...conditionalFormatting
      });
    }
    
    // Enregistrer le classeur
    await workbook.xlsx.writeFile(outputPath);
  }
  
  /**
   * Exporte les données de paie au format Sage
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToSage({ data, outputPath, metadata }) {
    // Format spécifique pour Sage Paie
    const sageLines = [];
    
    // En-tête du fichier
    sageLines.push('SAGEP;1.0;UTF-8');
    sageLines.push('SIRET;12345678901234');
    sageLines.push(`PERIOD;${moment(metadata.startDate).format('YYYYMM')}`);
    
    // Ligne pour chaque employé
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      // Format spécifique pour chaque employé
      const employeeLine = [
        employeeId,
        info.lastName ? info.lastName.toUpperCase() : '',
        info.firstName || '',
        hours.regular ? hours.regular.toFixed(2) : '0.00',
        hours.overtime ? hours.overtime.toFixed(2) : '0.00',
        hours.night ? hours.night.toFixed(2) : '0.00',
        variables.service_charge ? variables.service_charge.toFixed(2) : '0.00',
        variables.tips ? variables.tips.toFixed(2) : '0.00',
        variables.meal_allowance ? variables.meal_allowance.toFixed(2) : '0.00',
        variables.transport_allowance ? variables.transport_allowance.toFixed(2) : '0.00',
        variables.bonus ? variables.bonus.toFixed(2) : '0.00',
        variables.commission ? variables.commission.toFixed(2) : '0.00',
        variables.sundry_additions ? variables.sundry_additions.toFixed(2) : '0.00',
        variables.sundry_deductions ? variables.sundry_deductions.toFixed(2) : '0.00'
      ].join(';');
      
      sageLines.push(`EMP;${employeeLine}`);
    }
    
    // Ligne de fin de fichier
    sageLines.push('END');
    
    // Écrire le fichier
    await fs.writeFile(outputPath, sageLines.join('\n'), 'utf8');
  }
  
  /**
   * Exporte les données de paie au format Silae
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToSilae({ data, outputPath, metadata }) {
    // Similaire au CSV mais avec un format spécifique pour Silae
    // Format simplifié pour l'exemple
    
    // Préparer les données pour le CSV
    const csvRows = [];
    
    // En-tête du CSV pour Silae
    const headers = [
      'MATRICULE',
      'NOM',
      'PRENOM',
      'QUALIFICATION',
      'CODE_01',
      'VALEUR_01',
      'CODE_02',
      'VALEUR_02',
      'CODE_03',
      'VALEUR_03',
      'CODE_04',
      'VALEUR_04',
      'CODE_05',
      'VALEUR_05',
      'CODE_06',
      'VALEUR_06',
      'CODE_07',
      'VALEUR_07',
      'CODE_08',
      'VALEUR_08'
    ];
    
    csvRows.push(headers);
    
    // Ajouter les données de chaque employé
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      const row = [
        employeeId,
        info.lastName || '',
        info.firstName || '',
        info.position || '',
        'HN', // Heures normales
        hours.regular || 0,
        'HS', // Heures supplémentaires
        hours.overtime || 0,
        'HN', // Heures de nuit
        hours.night || 0,
        'PS', // Prime de service
        variables.service_charge || 0,
        'PB', // Pourboires
        variables.tips || 0,
        'IR', // Indemnité repas
        variables.meal_allowance || 0,
        'IT', // Indemnité transport
        variables.transport_allowance || 0,
        'PM', // Prime mensuelle (bonus + commission)
        (variables.bonus || 0) + (variables.commission || 0)
      ];
      
      csvRows.push(row);
    }
    
    // Générer la chaîne CSV
    const csvContent = csvStringify(csvRows, {
      delimiter: ';',
      header: false,
      quoted: true
    });
    
    // Écrire le fichier
    await fs.writeFile(outputPath, csvContent, 'utf8');
  }
  
  /**
   * Exporte les données de paie au format ADP
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToADP({ data, outputPath, metadata }) {
    // Format XML pour ADP
    let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    xmlContent += `<ADPPayrollImport version="1.0">\n`;
    xmlContent += `  <Company>Le Vieux Moulin</Company>\n`;
    xmlContent += `  <Period>${moment(metadata.startDate).format('YYYYMM')}</Period>\n`;
    xmlContent += `  <GeneratedDate>${moment().format('YYYY-MM-DD HH:mm:ss')}</GeneratedDate>\n`;
    xmlContent += `  <Employees>\n`;
    
    // Ajouter chaque employé
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      xmlContent += `    <Employee>\n`;
      xmlContent += `      <ID>${this._escapeXml(employeeId)}</ID>\n`;
      xmlContent += `      <LastName>${this._escapeXml(info.lastName || '')}</LastName>\n`;
      xmlContent += `      <FirstName>${this._escapeXml(info.firstName || '')}</FirstName>\n`;
      xmlContent += `      <Position>${this._escapeXml(info.position || '')}</Position>\n`;
      xmlContent += `      <Hours>\n`;
      xmlContent += `        <Regular>${hours.regular || 0}</Regular>\n`;
      xmlContent += `        <Overtime>${hours.overtime || 0}</Overtime>\n`;
      xmlContent += `        <Night>${hours.night || 0}</Night>\n`;
      xmlContent += `      </Hours>\n`;
      xmlContent += `      <Variables>\n`;
      xmlContent += `        <ServiceCharge>${variables.service_charge || 0}</ServiceCharge>\n`;
      xmlContent += `        <Tips>${variables.tips || 0}</Tips>\n`;
      xmlContent += `        <MealAllowance>${variables.meal_allowance || 0}</MealAllowance>\n`;
      xmlContent += `        <TransportAllowance>${variables.transport_allowance || 0}</TransportAllowance>\n`;
      xmlContent += `        <Bonus>${variables.bonus || 0}</Bonus>\n`;
      xmlContent += `        <Commission>${variables.commission || 0}</Commission>\n`;
      xmlContent += `        <SundryAdditions>${variables.sundry_additions || 0}</SundryAdditions>\n`;
      xmlContent += `        <SundryDeductions>${variables.sundry_deductions || 0}</SundryDeductions>\n`;
      xmlContent += `      </Variables>\n`;
      xmlContent += `    </Employee>\n`;
    }
    
    xmlContent += `  </Employees>\n`;
    xmlContent += `</ADPPayrollImport>`;
    
    // Écrire le fichier
    await fs.writeFile(outputPath, xmlContent, 'utf8');
  }
  
  /**
   * Exporte les données de paie au format DSN
   * @param {Object} options - Options d'export
   * @param {Object} options.data - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _exportToDSN({ data, outputPath, metadata }) {
    // Format spécifique pour la DSN (Déclaration Sociale Nominative)
    // Ceci est une version très simplifiée du format DSN
    
    const dsnLines = [];
    
    // En-tête de la DSN
    dsnLines.push('S10.G00.00.001,01,1');
    dsnLines.push(`S10.G00.00.002,${moment().format('YYYYMMDD')}`);
    dsnLines.push('S10.G00.00.003,12,1');
    dsnLines.push('S10.G00.00.004,01');
    dsnLines.push('S10.G00.00.005,01');
    
    // Informations sur l'émetteur
    dsnLines.push('S10.G00.01.001,Le Vieux Moulin');
    dsnLines.push('S10.G00.01.002,12345678901234');
    dsnLines.push('S10.G00.01.003,1');
    dsnLines.push('S10.G00.01.004,01');
    
    // Informations sur l'établissement
    dsnLines.push('S10.G00.02.001,12345678901234');
    dsnLines.push('S10.G00.02.002,12345');
    dsnLines.push('S10.G00.02.005,Le Vieux Moulin');
    
    // Période de référence
    dsnLines.push(`S20.G00.05.001,${moment(metadata.startDate).format('YYYYMM')}`);
    dsnLines.push(`S20.G00.05.005,${moment(metadata.startDate).format('DD')}`);
    dsnLines.push(`S20.G00.05.006,${moment(metadata.endDate).format('DD')}`);
    
    // Informations sur chaque salarié
    for (const [employeeId, employeeData] of Object.entries(data)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      const variables = employeeData.variables || {};
      
      // Identification du salarié
      dsnLines.push(`S21.G00.30.001,${employeeId}`);
      dsnLines.push(`S21.G00.30.002,${info.lastName || ''}`);
      dsnLines.push(`S21.G00.30.003,${info.firstName || ''}`);
      
      // Contrat de travail
      dsnLines.push(`S21.G00.40.001,${employeeId}`);
      dsnLines.push('S21.G00.40.003,03');
      dsnLines.push('S21.G00.40.004,01');
      
      // Rémunérations
      dsnLines.push(`S21.G00.51.001,${employeeId}`);
      dsnLines.push('S21.G00.51.002,001');
      dsnLines.push(`S21.G00.51.005,${(hours.regular || 0) * 10}`); // Montant fictif
      
      // Heures
      dsnLines.push(`S21.G00.53.001,${employeeId}`);
      dsnLines.push('S21.G00.53.002,01');
      dsnLines.push(`S21.G00.53.003,${hours.regular || 0}`);
      
      if (hours.overtime && hours.overtime > 0) {
        dsnLines.push(`S21.G00.53.001,${employeeId}`);
        dsnLines.push('S21.G00.53.002,02');
        dsnLines.push(`S21.G00.53.003,${hours.overtime}`);
      }
    }
    
    // Fin de déclaration
    dsnLines.push('S90.G00.90.001,1');
    dsnLines.push(`S90.G00.90.002,${Object.keys(data).length}`);
    
    // Écrire le fichier
    await fs.writeFile(outputPath, dsnLines.join('\n'), 'utf8');
  }
  
  /**
   * Génère un rapport de validation au format PDF
   * @param {Object} options - Options de génération
   * @param {Object} options.validationResult - Résultats de validation
   * @param {Object} options.payrollData - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _generateValidationPDF({ validationResult, payrollData, outputPath, metadata }) {
    // Créer le document PDF
    const doc = new PDFDocument({
      autoFirstPage: true,
      bufferPages: true,
      margin: 50,
      size: 'A4'
    });
    
    // Créer le flux d'écriture
    const writeStream = fs.createWriteStream(outputPath);
    doc.pipe(writeStream);
    
    // Fonction d'aide pour ajouter du texte
    const addText = (text, options = {}) => {
      const defaults = { fontSize: 12, continued: false };
      const settings = { ...defaults, ...options };
      
      doc.fontSize(settings.fontSize);
      if (settings.font) doc.font(settings.font);
      if (settings.fillColor) doc.fillColor(settings.fillColor);
      
      return doc.text(text, {
        align: settings.align || 'left',
        continued: settings.continued
      });
    };
    
    // En-tête du document
    addText('Rapport de validation - Données de paie', { fontSize: 18, align: 'center' });
    doc.moveDown();
    addText(`Restaurant "Le Vieux Moulin"`, { fontSize: 14, align: 'center' });
    doc.moveDown();
    addText(`Période: ${moment(metadata.startDate).format('DD/MM/YYYY')} - ${moment(metadata.endDate).format('DD/MM/YYYY')}`, { align: 'center' });
    addText(`Généré le: ${moment().format('DD/MM/YYYY HH:mm')}`, { align: 'center' });
    doc.moveDown(2);
    
    // Résumé
    addText('RÉSUMÉ DE VALIDATION', { fontSize: 14 });
    doc.moveDown();
    
    const isValid = validationResult.isValid;
    addText(`Statut: ${isValid ? 'VALIDE' : 'INVALIDE'}`, { 
      fillColor: isValid ? '#007700' : '#CC0000',
      fontSize: 12
    });
    doc.moveDown();
    
    addText(`Total des avertissements: ${validationResult.summary.totalWarnings}`);
    addText(`Total des erreurs: ${validationResult.summary.totalErrors}`);
    doc.moveDown();
    
    // Détails par section
    if (validationResult.attendance) {
      addText('VALIDATION DES DONNÉES DE PRÉSENCE', { fontSize: 14 });
      doc.moveDown();
      
      if (validationResult.attendance.errors.length > 0) {
        addText('Erreurs:', { fontSize: 12, fillColor: '#CC0000' });
        doc.moveDown(0.5);
        
        validationResult.attendance.errors.forEach((error, index) => {
          addText(`${index + 1}. [${error.code}] ${error.message}`);
          if (error.employeeId) {
            addText(`   Employé: ${error.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      if (validationResult.attendance.warnings.length > 0) {
        addText('Avertissements:', { fontSize: 12, fillColor: '#FF6600' });
        doc.moveDown(0.5);
        
        validationResult.attendance.warnings.forEach((warning, index) => {
          addText(`${index + 1}. [${warning.code}] ${warning.message}`);
          if (warning.employeeId) {
            addText(`   Employé: ${warning.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      doc.moveDown();
    }
    
    if (validationResult.payroll) {
      addText('VALIDATION DES DONNÉES DE PAIE', { fontSize: 14 });
      doc.moveDown();
      
      if (validationResult.payroll.errors.length > 0) {
        addText('Erreurs:', { fontSize: 12, fillColor: '#CC0000' });
        doc.moveDown(0.5);
        
        validationResult.payroll.errors.forEach((error, index) => {
          addText(`${index + 1}. [${error.code}] ${error.message}`);
          if (error.employeeId) {
            addText(`   Employé: ${error.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      if (validationResult.payroll.warnings.length > 0) {
        addText('Avertissements:', { fontSize: 12, fillColor: '#FF6600' });
        doc.moveDown(0.5);
        
        validationResult.payroll.warnings.forEach((warning, index) => {
          addText(`${index + 1}. [${warning.code}] ${warning.message}`);
          if (warning.employeeId) {
            addText(`   Employé: ${warning.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      doc.moveDown();
    }
    
    if (validationResult.cross) {
      addText('VALIDATION CROISÉE', { fontSize: 14 });
      doc.moveDown();
      
      if (validationResult.cross.errors.length > 0) {
        addText('Erreurs:', { fontSize: 12, fillColor: '#CC0000' });
        doc.moveDown(0.5);
        
        validationResult.cross.errors.forEach((error, index) => {
          addText(`${index + 1}. [${error.code}] ${error.message}`);
          if (error.employeeId) {
            addText(`   Employé: ${error.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      if (validationResult.cross.warnings.length > 0) {
        addText('Avertissements:', { fontSize: 12, fillColor: '#FF6600' });
        doc.moveDown(0.5);
        
        validationResult.cross.warnings.forEach((warning, index) => {
          addText(`${index + 1}. [${warning.code}] ${warning.message}`);
          if (warning.employeeId) {
            addText(`   Employé: ${warning.employeeId}`);
          }
          doc.moveDown(0.5);
        });
      }
      
      doc.moveDown();
    }
    
    // Informations sur les données
    addText('INFORMATIONS SUR LES DONNÉES', { fontSize: 14 });
    doc.moveDown();
    
    const employeeCount = Object.keys(payrollData).length;
    addText(`Nombre d'employés: ${employeeCount}`);
    
    // Calcul de quelques statistiques
    let totalRegularHours = 0;
    let totalOvertimeHours = 0;
    let totalNightHours = 0;
    
    for (const employeeData of Object.values(payrollData)) {
      const hours = employeeData.hours || {};
      totalRegularHours += hours.regular || 0;
      totalOvertimeHours += hours.overtime || 0;
      totalNightHours += hours.night || 0;
    }
    
    addText(`Total des heures régulières: ${totalRegularHours.toFixed(2)}`);
    addText(`Total des heures supplémentaires: ${totalOvertimeHours.toFixed(2)}`);
    addText(`Total des heures de nuit: ${totalNightHours.toFixed(2)}`);
    
    // Pied de page
    const pageCount = doc.bufferedPageRange().count;
    for (let i = 0; i < pageCount; i++) {
      doc.switchToPage(i);
      doc.fontSize(10).text(
        `Page ${i + 1} sur ${pageCount}`,
        50,
        doc.page.height - 50,
        { align: 'center' }
      );
    }
    
    // Finaliser le document
    doc.end();
    
    // Attendre que le flux d'écriture soit terminé
    return new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
  }
  
  /**
   * Génère un rapport de validation au format HTML
   * @param {Object} options - Options de génération
   * @param {Object} options.validationResult - Résultats de validation
   * @param {Object} options.payrollData - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _generateValidationHTML({ validationResult, payrollData, outputPath, metadata }) {
    // Version simplifiée pour l'exemple
    let htmlContent = `
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de validation - Le Vieux Moulin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .valid { color: #28a745; }
        .invalid { color: #dc3545; }
        .section { margin-bottom: 30px; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
        .error { color: #dc3545; }
        .warning { color: #ffc107; }
        .issue { margin-bottom: 10px; padding-left: 20px; }
        .employee { font-style: italic; margin-left: 20px; }
        .footer { text-align: center; margin-top: 50px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Rapport de validation - Données de paie</h1>
        <h2>Restaurant "Le Vieux Moulin"</h2>
        <p>Période: ${moment(metadata.startDate).format('DD/MM/YYYY')} - ${moment(metadata.endDate).format('DD/MM/YYYY')}</p>
        <p>Généré le: ${moment().format('DD/MM/YYYY HH:mm')}</p>
    </div>
    
    <div class="summary">
        <h2>Résumé de validation</h2>
        <p>Statut: <span class="${validationResult.isValid ? 'valid' : 'invalid'}">${validationResult.isValid ? 'VALIDE' : 'INVALIDE'}</span></p>
        <p>Total des avertissements: ${validationResult.summary.totalWarnings}</p>
        <p>Total des erreurs: ${validationResult.summary.totalErrors}</p>
    </div>
`;
    
    // Section de validation des données de présence
    if (validationResult.attendance) {
      htmlContent += `
    <div class="section">
        <div class="section-title">Validation des données de présence</div>`;
        
      if (validationResult.attendance.errors.length > 0) {
        htmlContent += `
        <h3 class="error">Erreurs:</h3>
        <ul>`;
        
        validationResult.attendance.errors.forEach(error => {
          htmlContent += `
            <li class="issue">
                <strong>[${error.code}]</strong> ${error.message}
                ${error.employeeId ? `<div class="employee">Employé: ${error.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      if (validationResult.attendance.warnings.length > 0) {
        htmlContent += `
        <h3 class="warning">Avertissements:</h3>
        <ul>`;
        
        validationResult.attendance.warnings.forEach(warning => {
          htmlContent += `
            <li class="issue">
                <strong>[${warning.code}]</strong> ${warning.message}
                ${warning.employeeId ? `<div class="employee">Employé: ${warning.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      htmlContent += `
    </div>`;
    }
    
    // Section de validation des données de paie
    if (validationResult.payroll) {
      htmlContent += `
    <div class="section">
        <div class="section-title">Validation des données de paie</div>`;
        
      if (validationResult.payroll.errors.length > 0) {
        htmlContent += `
        <h3 class="error">Erreurs:</h3>
        <ul>`;
        
        validationResult.payroll.errors.forEach(error => {
          htmlContent += `
            <li class="issue">
                <strong>[${error.code}]</strong> ${error.message}
                ${error.employeeId ? `<div class="employee">Employé: ${error.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      if (validationResult.payroll.warnings.length > 0) {
        htmlContent += `
        <h3 class="warning">Avertissements:</h3>
        <ul>`;
        
        validationResult.payroll.warnings.forEach(warning => {
          htmlContent += `
            <li class="issue">
                <strong>[${warning.code}]</strong> ${warning.message}
                ${warning.employeeId ? `<div class="employee">Employé: ${warning.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      htmlContent += `
    </div>`;
    }
    
    // Section de validation croisée
    if (validationResult.cross) {
      htmlContent += `
    <div class="section">
        <div class="section-title">Validation croisée</div>`;
        
      if (validationResult.cross.errors.length > 0) {
        htmlContent += `
        <h3 class="error">Erreurs:</h3>
        <ul>`;
        
        validationResult.cross.errors.forEach(error => {
          htmlContent += `
            <li class="issue">
                <strong>[${error.code}]</strong> ${error.message}
                ${error.employeeId ? `<div class="employee">Employé: ${error.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      if (validationResult.cross.warnings.length > 0) {
        htmlContent += `
        <h3 class="warning">Avertissements:</h3>
        <ul>`;
        
        validationResult.cross.warnings.forEach(warning => {
          htmlContent += `
            <li class="issue">
                <strong>[${warning.code}]</strong> ${warning.message}
                ${warning.employeeId ? `<div class="employee">Employé: ${warning.employeeId}</div>` : ''}
            </li>`;
        });
        
        htmlContent += `
        </ul>`;
      }
      
      htmlContent += `
    </div>`;
    }
    
    // Informations sur les données
    const employeeCount = Object.keys(payrollData).length;
    let totalRegularHours = 0;
    let totalOvertimeHours = 0;
    let totalNightHours = 0;
    
    for (const employeeData of Object.values(payrollData)) {
      const hours = employeeData.hours || {};
      totalRegularHours += hours.regular || 0;
      totalOvertimeHours += hours.overtime || 0;
      totalNightHours += hours.night || 0;
    }
    
    htmlContent += `
    <div class="section">
        <div class="section-title">Informations sur les données</div>
        <p>Nombre d'employés: ${employeeCount}</p>
        <p>Total des heures régulières: ${totalRegularHours.toFixed(2)}</p>
        <p>Total des heures supplémentaires: ${totalOvertimeHours.toFixed(2)}</p>
        <p>Total des heures de nuit: ${totalNightHours.toFixed(2)}</p>
    </div>
    
    <div class="footer">
        <p>Ce rapport a été généré automatiquement par le module de paie du Restaurant "Le Vieux Moulin".</p>
    </div>
</body>
</html>`;
    
    // Écrire le fichier
    await fs.writeFile(outputPath, htmlContent, 'utf8');
  }
  
  /**
   * Génère un rapport de validation au format Excel
   * @param {Object} options - Options de génération
   * @param {Object} options.validationResult - Résultats de validation
   * @param {Object} options.payrollData - Données de paie
   * @param {string} options.outputPath - Chemin de sortie
   * @param {Object} options.metadata - Métadonnées
   * @returns {Promise<void>}
   * @private
   */
  async _generateValidationExcel({ validationResult, payrollData, outputPath, metadata }) {
    // Version simplifiée pour l'exemple
    const workbook = new ExcelJS.Workbook();
    
    // Propriétés du classeur
    workbook.creator = 'Le Vieux Moulin - Module de Paie';
    workbook.lastModifiedBy = 'Système automatisé';
    workbook.created = new Date();
    workbook.modified = new Date();
    
    // Feuille de résumé
    const summarySheet = workbook.addWorksheet('Résumé');
    
    summarySheet.columns = [
      { header: 'Propriété', key: 'property', width: 30 },
      { header: 'Valeur', key: 'value', width: 50 }
    ];
    
    summarySheet.getRow(1).font = { bold: true };
    
    // Ajouter les informations de résumé
    summarySheet.addRow({ property: 'Nom de l\'entreprise', value: 'Le Vieux Moulin' });
    summarySheet.addRow({ property: 'Période de début', value: moment(metadata.startDate).format('DD/MM/YYYY') });
    summarySheet.addRow({ property: 'Période de fin', value: moment(metadata.endDate).format('DD/MM/YYYY') });
    summarySheet.addRow({ property: 'Date de génération', value: moment().format('DD/MM/YYYY HH:mm:ss') });
    summarySheet.addRow({ property: 'Statut de validation', value: validationResult.isValid ? 'VALIDE' : 'INVALIDE' });
    summarySheet.addRow({ property: 'Total des avertissements', value: validationResult.summary.totalWarnings });
    summarySheet.addRow({ property: 'Total des erreurs', value: validationResult.summary.totalErrors });
    
    // Mise en forme conditionnelle pour le statut
    const statusCell = summarySheet.getCell('B5');
    if (validationResult.isValid) {
      statusCell.font = { color: { argb: 'FF00AA00' }, bold: true };
    } else {
      statusCell.font = { color: { argb: 'FFAA0000' }, bold: true };
    }
    
    // Feuille des erreurs
    const errorsSheet = workbook.addWorksheet('Erreurs');
    
    errorsSheet.columns = [
      { header: 'Type', key: 'type', width: 15 },
      { header: 'Code', key: 'code', width: 20 },
      { header: 'Message', key: 'message', width: 50 },
      { header: 'Employé', key: 'employee', width: 20 }
    ];
    
    errorsSheet.getRow(1).font = { bold: true };
    
    // Ajouter toutes les erreurs
    [
      ...validationResult.attendance?.errors.map(err => ({ ...err, type: 'Présence' })) || [],
      ...validationResult.payroll?.errors.map(err => ({ ...err, type: 'Paie' })) || [],
      ...validationResult.cross?.errors.map(err => ({ ...err, type: 'Croisé' })) || []
    ].forEach(error => {
      errorsSheet.addRow({
        type: error.type,
        code: error.code,
        message: error.message,
        employee: error.employeeId || ''
      });
    });
    
    // Feuille des avertissements
    const warningsSheet = workbook.addWorksheet('Avertissements');
    
    warningsSheet.columns = [
      { header: 'Type', key: 'type', width: 15 },
      { header: 'Code', key: 'code', width: 20 },
      { header: 'Message', key: 'message', width: 50 },
      { header: 'Employé', key: 'employee', width: 20 }
    ];
    
    warningsSheet.getRow(1).font = { bold: true };
    
    // Ajouter tous les avertissements
    [
      ...validationResult.attendance?.warnings.map(warn => ({ ...warn, type: 'Présence' })) || [],
      ...validationResult.payroll?.warnings.map(warn => ({ ...warn, type: 'Paie' })) || [],
      ...validationResult.cross?.warnings.map(warn => ({ ...warn, type: 'Croisé' })) || []
    ].forEach(warning => {
      warningsSheet.addRow({
        type: warning.type,
        code: warning.code,
        message: warning.message,
        employee: warning.employeeId || ''
      });
    });
    
    // Feuille des données
    const dataSheet = workbook.addWorksheet('Données');
    
    dataSheet.columns = [
      { header: 'Matricule', key: 'id', width: 15 },
      { header: 'Nom', key: 'lastName', width: 20 },
      { header: 'Prénom', key: 'firstName', width: 20 },
      { header: 'Poste', key: 'position', width: 20 },
      { header: 'Heures régulières', key: 'regularHours', width: 15 },
      { header: 'Heures supplémentaires', key: 'overtimeHours', width: 15 },
      { header: 'Heures de nuit', key: 'nightHours', width: 15 },
      { header: 'Total des heures', key: 'totalHours', width: 15 }
    ];
    
    dataSheet.getRow(1).font = { bold: true };
    
    // Ajouter les données de chaque employé
    for (const [employeeId, employeeData] of Object.entries(payrollData)) {
      const info = employeeData.info || {};
      const hours = employeeData.hours || {};
      
      dataSheet.addRow({
        id: employeeId,
        lastName: info.lastName || '',
        firstName: info.firstName || '',
        position: info.position || '',
        regularHours: hours.regular || 0,
        overtimeHours: hours.overtime || 0,
        nightHours: hours.night || 0,
        totalHours: hours.total || 0
      });
    }
    
    // Appliquer le formatage des nombres
    for (let col = 5; col <= 8; col++) {
      dataSheet.getColumn(col).numFmt = '0.00';
    }
    
    // Enregistrer le classeur
    await workbook.xlsx.writeFile(outputPath);
  }
  
  /**
   * Échappe les caractères spéciaux XML
   * @param {string} unsafe - Chaîne à échapper
   * @returns {string} Chaîne échappée
   * @private
   */
  _escapeXml(unsafe) {
    if (typeof unsafe !== 'string') {
      return '';
    }
    
    return unsafe.replace(/[<>&'"]/g, (c) => {
      switch (c) {
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '&': return '&amp;';
        case '\'': return '&apos;';
        case '"': return '&quot;';
        default: return c;
      }
    });
  }
}

// Exports
module.exports = {
  PayrollExporter
};
