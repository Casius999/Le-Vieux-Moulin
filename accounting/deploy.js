#!/usr/bin/env node

/**
 * Script de déploiement du module de comptabilité
 * 
 * Ce script permet de déployer le module de comptabilité dans un environnement
 * de production, en configurant automatiquement l'ensemble des ressources nécessaires.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const inquirer = require('inquirer');
const chalk = require('chalk');
const ora = require('ora');
const { AccountingModule } = require('./index');

// Configuration par défaut
const DEFAULT_CONFIG = {
  port: 3001,
  environment: 'production',
  database: {
    host: 'localhost',
    port: 5432,
    user: 'accounting',
    password: '',
    database: 'le_vieux_moulin_accounting'
  },
  security: {
    jwt_secret: '',
    jwt_expiration: '24h',
    encryption_key: ''
  },
  api: {
    cors_origins: ['http://localhost:3000', 'https://levieuxmoulin.example.com'],
    rate_limit: {
      window_ms: 15 * 60 * 1000, // 15 minutes
      max: 100 // Maximum 100 requêtes par fenêtre
    }
  },
  email: {
    service: 'smtp',
    host: 'smtp.example.com',
    port: 587,
    user: '',
    password: '',
    from: 'comptabilite@levieuxmoulin.example.com'
  }
};

// Options de déploiement
const deployOptions = {
  configPath: path.join(__dirname, 'config'),
  dataPath: path.join(__dirname, 'data'),
  logsPath: path.join(__dirname, 'logs'),
  environment: process.env.NODE_ENV || 'production',
  installDependencies: true,
  runMigrations: true,
  createDatabase: false,
  generateSecureKeys: true,
  configureBackups: true,
  setupLogging: true,
  createSystemdService: false,
  createNginxConfig: false,
  testAfterDeploy: true
};

/**
 * Point d'entrée principal
 */
async function main() {
  console.log(chalk.bold.blue('\n╔══════════════════════════════════════════════════════════╗'));
  console.log(chalk.bold.blue('║ Déploiement du Module de Comptabilité - Le Vieux Moulin    ║'));
  console.log(chalk.bold.blue('╚══════════════════════════════════════════════════════════╝\n'));
  
  try {
    // Vérifier les prérequis
    checkPrerequisites();
    
    // Demander les options de configuration
    const options = await promptConfigOptions();
    
    // Créer les répertoires nécessaires
    await createDirectories(options);
    
    // Générer la configuration
    await generateConfig(options);
    
    // Installer les dépendances si nécessaire
    if (options.installDependencies) {
      await installDependencies();
    }
    
    // Créer la base de données si nécessaire
    if (options.createDatabase) {
      await createDatabase(options);
    }
    
    // Exécuter les migrations
    if (options.runMigrations) {
      await runMigrations(options);
    }
    
    // Configurer les sauvegardes
    if (options.configureBackups) {
      await setupBackups(options);
    }
    
    // Configurer la journalisation
    if (options.setupLogging) {
      await setupLogging(options);
    }
    
    // Créer le service systemd si demandé
    if (options.createSystemdService) {
      await createSystemdService(options);
    }
    
    // Créer la configuration Nginx si demandée
    if (options.createNginxConfig) {
      await createNginxConfig(options);
    }
    
    // Tester le déploiement
    if (options.testAfterDeploy) {
      await testDeployment(options);
    }
    
    console.log(chalk.green.bold('\n✅ Déploiement réussi!'));
    console.log(chalk.green(`Le module de comptabilité a été déployé avec succès dans l'environnement ${options.environment}.`));
    console.log(chalk.green(`Documentation disponible à: http://localhost:${options.config.port}/api/docs`));
  } catch (error) {
    console.error(chalk.red.bold('\n❌ Erreur lors du déploiement:'));
    console.error(chalk.red(error.message));
    console.error(chalk.dim(error.stack));
    process.exit(1);
  }
}

/**
 * Vérifie les prérequis système
 */
function checkPrerequisites() {
  const spinner = ora('Vérification des prérequis...').start();
  
  try {
    // Vérifier la version de Node.js
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0]);
    
    if (majorVersion < 16) {
      spinner.fail();
      throw new Error(`Node.js 16 ou supérieur est requis. Version actuelle: ${nodeVersion}`);
    }
    
    // Vérifier si npm est installé
    try {
      execSync('npm --version', { stdio: 'ignore' });
    } catch (error) {
      spinner.fail();
      throw new Error('npm n\'est pas installé ou n\'est pas accessible');
    }
    
    // Vérifier les permissions
    const currentDir = __dirname;
    try {
      fs.accessSync(currentDir, fs.constants.W_OK);
    } catch (error) {
      spinner.fail();
      throw new Error(`Permissions d'écriture manquantes pour ${currentDir}`);
    }
    
    spinner.succeed('Prérequis validés');
  } catch (error) {
    spinner.fail(`Échec de la vérification des prérequis: ${error.message}`);
    throw error;
  }
}

/**
 * Demande les options de configuration à l'utilisateur
 */
async function promptConfigOptions() {
  console.log(chalk.cyan.bold('\n📋 Configuration du déploiement\n'));
  
  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'environment',
      message: 'Environnement de déploiement:',
      default: deployOptions.environment,
      choices: ['development', 'test', 'staging', 'production']
    },
    {
      type: 'input',
      name: 'port',
      message: 'Port pour l\'API:',
      default: DEFAULT_CONFIG.port,
      validate: input => {
        const port = parseInt(input);
        return (!isNaN(port) && port > 0 && port < 65536) ? true : 'Veuillez entrer un port valide (1-65535)';
      }
    },
    {
      type: 'confirm',
      name: 'installDependencies',
      message: 'Installer les dépendances:',
      default: deployOptions.installDependencies
    },
    {
      type: 'confirm',
      name: 'createDatabase',
      message: 'Créer la base de données PostgreSQL:',
      default: deployOptions.createDatabase
    },
    {
      type: 'confirm',
      name: 'runMigrations',
      message: 'Exécuter les migrations de base de données:',
      default: deployOptions.runMigrations
    },
    {
      type: 'confirm',
      name: 'generateSecureKeys',
      message: 'Générer de nouvelles clés de sécurité:',
      default: deployOptions.generateSecureKeys
    },
    {
      type: 'confirm',
      name: 'configureBackups',
      message: 'Configurer les sauvegardes automatiques:',
      default: deployOptions.configureBackups
    },
    {
      type: 'confirm',
      name: 'createSystemdService',
      message: 'Créer un service systemd (Linux uniquement):',
      default: deployOptions.createSystemdService,
      when: () => process.platform === 'linux'
    },
    {
      type: 'confirm',
      name: 'createNginxConfig',
      message: 'Créer une configuration Nginx:',
      default: deployOptions.createNginxConfig
    }
  ]);
  
  // Intégrer les réponses dans les options
  const options = {
    ...deployOptions,
    ...answers,
    config: { ...DEFAULT_CONFIG }
  };
  
  // Mettre à jour la configuration avec les valeurs saisies
  options.config.port = parseInt(answers.port);
  options.config.environment = answers.environment;
  
  // Si on crée une base de données, demander plus d'informations
  if (options.createDatabase) {
    const dbAnswers = await inquirer.prompt([
      {
        type: 'input',
        name: 'db_host',
        message: 'Hôte de la base de données:',
        default: DEFAULT_CONFIG.database.host
      },
      {
        type: 'input',
        name: 'db_port',
        message: 'Port de la base de données:',
        default: DEFAULT_CONFIG.database.port
      },
      {
        type: 'input',
        name: 'db_user',
        message: 'Utilisateur de la base de données:',
        default: DEFAULT_CONFIG.database.user
      },
      {
        type: 'password',
        name: 'db_password',
        message: 'Mot de passe de la base de données:',
        mask: '*'
      },
      {
        type: 'input',
        name: 'db_name',
        message: 'Nom de la base de données:',
        default: DEFAULT_CONFIG.database.database
      }
    ]);
    
    // Mettre à jour la configuration de la base de données
    options.config.database = {
      host: dbAnswers.db_host,
      port: parseInt(dbAnswers.db_port),
      user: dbAnswers.db_user,
      password: dbAnswers.db_password,
      database: dbAnswers.db_name
    };
  }
  
  // Si on configure les emails, demander plus d'informations
  const emailAnswers = await inquirer.prompt([
    {
      type: 'confirm',
      name: 'configure_email',
      message: 'Configurer les emails pour les rapports:',
      default: true
    },
    {
      type: 'input',
      name: 'email_host',
      message: 'Serveur SMTP:',
      default: DEFAULT_CONFIG.email.host,
      when: answers => answers.configure_email
    },
    {
      type: 'input',
      name: 'email_port',
      message: 'Port SMTP:',
      default: DEFAULT_CONFIG.email.port,
      when: answers => answers.configure_email,
      validate: input => {
        const port = parseInt(input);
        return (!isNaN(port) && port > 0 && port < 65536) ? true : 'Veuillez entrer un port valide (1-65535)';
      }
    },
    {
      type: 'input',
      name: 'email_user',
      message: 'Utilisateur SMTP:',
      when: answers => answers.configure_email
    },
    {
      type: 'password',
      name: 'email_password',
      message: 'Mot de passe SMTP:',
      mask: '*',
      when: answers => answers.configure_email
    },
    {
      type: 'input',
      name: 'email_from',
      message: 'Adresse expéditeur:',
      default: DEFAULT_CONFIG.email.from,
      when: answers => answers.configure_email
    }
  ]);
  
  // Si les emails sont configurés, mettre à jour la configuration
  if (emailAnswers.configure_email) {
    options.config.email = {
      service: 'smtp',
      host: emailAnswers.email_host,
      port: parseInt(emailAnswers.email_port),
      user: emailAnswers.email_user,
      password: emailAnswers.email_password,
      from: emailAnswers.email_from
    };
  }
  
  return options;
}

/**
 * Crée les répertoires nécessaires
 */
async function createDirectories(options) {
  const spinner = ora('Création des répertoires...').start();
  
  try {
    // Créer les répertoires s'ils n'existent pas
    const directories = [
      options.configPath,
      options.dataPath,
      options.logsPath,
      path.join(options.logsPath, 'archives')
    ];
    
    for (const dir of directories) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }
    
    spinner.succeed('Répertoires créés avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la création des répertoires: ${error.message}`);
    throw error;
  }
}

/**
 * Génère les fichiers de configuration
 */
async function generateConfig(options) {
  const spinner = ora('Génération de la configuration...').start();
  
  try {
    // Générer des clés sécurisées si demandé
    if (options.generateSecureKeys) {
      const crypto = require('crypto');
      options.config.security.jwt_secret = crypto.randomBytes(32).toString('hex');
      options.config.security.encryption_key = crypto.randomBytes(32).toString('hex');
    }
    
    // Créer le fichier de configuration principal
    const configFile = path.join(options.configPath, `${options.environment}.json`);
    fs.writeFileSync(configFile, JSON.stringify(options.config, null, 2));
    
    // Créer un fichier .env pour les variables sensibles
    const envFile = path.join(__dirname, '.env');
    const envContent = [
      `NODE_ENV=${options.environment}`,
      `PORT=${options.config.port}`,
      `DB_HOST=${options.config.database.host}`,
      `DB_PORT=${options.config.database.port}`,
      `DB_USER=${options.config.database.user}`,
      `DB_PASSWORD=${options.config.database.password}`,
      `DB_NAME=${options.config.database.database}`,
      `JWT_SECRET=${options.config.security.jwt_secret}`,
      `ENCRYPTION_KEY=${options.config.security.encryption_key}`,
      options.config.email.user ? `EMAIL_USER=${options.config.email.user}` : '',
      options.config.email.password ? `EMAIL_PASSWORD=${options.config.email.password}` : ''
    ].filter(Boolean).join('\n');
    
    fs.writeFileSync(envFile, envContent);
    
    spinner.succeed('Configuration générée avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la génération de la configuration: ${error.message}`);
    throw error;
  }
}

/**
 * Installe les dépendances npm
 */
async function installDependencies() {
  const spinner = ora('Installation des dépendances...').start();
  
  try {
    execSync('npm install --production', { cwd: __dirname, stdio: 'pipe' });
    spinner.succeed('Dépendances installées avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de l'installation des dépendances: ${error.message}`);
    throw error;
  }
}

/**
 * Crée la base de données PostgreSQL
 */
async function createDatabase(options) {
  const spinner = ora('Création de la base de données...').start();
  
  try {
    // Charger le module pg
    const { Client } = require('pg');
    
    // Connexion à PostgreSQL sans spécifier de base de données
    const client = new Client({
      host: options.config.database.host,
      port: options.config.database.port,
      user: options.config.database.user,
      password: options.config.database.password,
      database: 'postgres' // Base par défaut pour la connexion initiale
    });
    
    await client.connect();
    
    // Vérifier si la base de données existe déjà
    const checkResult = await client.query(
      'SELECT 1 FROM pg_database WHERE datname = $1',
      [options.config.database.database]
    );
    
    if (checkResult.rowCount === 0) {
      // La base de données n'existe pas, il faut la créer
      await client.query(`CREATE DATABASE ${options.config.database.database}`);
      spinner.text = 'Base de données créée, création de l\'utilisateur...';
      
      // Créer un utilisateur si nécessaire et attribuer les droits
      try {
        await client.query(`CREATE USER ${options.config.database.user} WITH ENCRYPTED PASSWORD '${options.config.database.password}'`);
      } catch (userError) {
        // L'utilisateur existe peut-être déjà, on continue
      }
      
      await client.query(`GRANT ALL PRIVILEGES ON DATABASE ${options.config.database.database} TO ${options.config.database.user}`);
    }
    
    await client.end();
    spinner.succeed('Base de données configurée avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la création de la base de données: ${error.message}`);
    throw error;
  }
}

/**
 * Exécute les migrations de base de données
 */
async function runMigrations(options) {
  const spinner = ora('Exécution des migrations...').start();
  
  try {
    // Exécuter les migrations avec un script dédié
    execSync('node ./database/migrate.js', { 
      cwd: __dirname, 
      stdio: 'pipe',
      env: {
        ...process.env,
        DB_HOST: options.config.database.host,
        DB_PORT: options.config.database.port.toString(),
        DB_USER: options.config.database.user,
        DB_PASSWORD: options.config.database.password,
        DB_NAME: options.config.database.database
      }
    });
    
    spinner.succeed('Migrations exécutées avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de l'exécution des migrations: ${error.message}`);
    throw error;
  }
}

/**
 * Configure les sauvegardes automatiques
 */
async function setupBackups(options) {
  const spinner = ora('Configuration des sauvegardes...').start();
  
  try {
    // Créer le répertoire de sauvegarde
    const backupDir = path.join(options.dataPath, 'backups');
    if (!fs.existsSync(backupDir)) {
      fs.mkdirSync(backupDir, { recursive: true });
    }
    
    // Créer le script de sauvegarde
    const backupScript = path.join(__dirname, 'scripts', 'backup.sh');
    if (!fs.existsSync(path.dirname(backupScript))) {
      fs.mkdirSync(path.dirname(backupScript), { recursive: true });
    }
    
    const scriptContent = `#!/bin/bash
# Script de sauvegarde automatique pour Le Vieux Moulin - Module Comptabilité
# Généré le ${new Date().toISOString()}

# Variables
DB_HOST="${options.config.database.host}"
DB_PORT="${options.config.database.port}"
DB_USER="${options.config.database.user}"
DB_PASSWORD="${options.config.database.password}"
DB_NAME="${options.config.database.database}"
BACKUP_DIR="${backupDir}"
DATE=\`date +%Y-%m-%d_%H-%M-%S\`

# Créer le répertoire de sauvegarde si nécessaire
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -F c -b -v -f "$BACKUP_DIR/$DB_NAME-$DATE.backup" $DB_NAME

# Sauvegarde des fichiers de configuration
cp -r ${options.configPath} "$BACKUP_DIR/config-$DATE"

# Nettoyage des anciennes sauvegardes (garde les 7 dernières)
cd $BACKUP_DIR
ls -t *.backup | tail -n +8 | xargs -r rm
ls -td config-* | tail -n +8 | xargs -r rm -rf

echo "Sauvegarde terminée: $BACKUP_DIR/$DB_NAME-$DATE.backup"
`;
    
    fs.writeFileSync(backupScript, scriptContent);
    fs.chmodSync(backupScript, '755'); // Rendre le script exécutable
    
    // Configurer une tâche cron si on est sur Linux
    if (process.platform === 'linux') {
      // Créer le fichier de configuration cron
      const cronFile = path.join(__dirname, 'scripts', 'accounting-backup.cron');
      const cronContent = `# Sauvegarde automatique du module de comptabilité - Le Vieux Moulin
0 2 * * * ${backupScript} >> ${options.logsPath}/backup.log 2>&1
`;
      
      fs.writeFileSync(cronFile, cronContent);
      
      try {
        // Installer la tâche cron (nécessite des droits root)
        execSync(`sudo cp ${cronFile} /etc/cron.d/`);
        execSync(`sudo chmod 644 /etc/cron.d/$(basename ${cronFile})`);
      } catch (cronError) {
        spinner.warn('Impossible d\'installer la tâche cron automatiquement. Vous devrez l\'installer manuellement.');
      }
    } else {
      spinner.info('Les tâches cron ne sont configurées que sur Linux. Veuillez configurer les sauvegardes selon votre système.');
    }
    
    spinner.succeed('Sauvegardes configurées avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la configuration des sauvegardes: ${error.message}`);
    throw error;
  }
}

/**
 * Configure la journalisation
 */
async function setupLogging(options) {
  const spinner = ora('Configuration de la journalisation...').start();
  
  try {
    // Créer le fichier de configuration de log-rotate si on est sur Linux
    if (process.platform === 'linux') {
      const logRotateFile = path.join(__dirname, 'scripts', 'accounting-logs.conf');
      const logRotateContent = `${options.logsPath}/*.log {
  daily
  missingok
  rotate 14
  compress
  delaycompress
  notifempty
  create 0640 node node
  sharedscripts
  postrotate
    systemctl reload accounting-module.service > /dev/null 2>/dev/null || true
  endscript
}
`;
      
      fs.writeFileSync(logRotateFile, logRotateContent);
      
      try {
        // Installer la configuration logrotate (nécessite des droits root)
        execSync(`sudo cp ${logRotateFile} /etc/logrotate.d/`);
        execSync(`sudo chmod 644 /etc/logrotate.d/$(basename ${logRotateFile})`);
      } catch (logrotateError) {
        spinner.warn('Impossible d\'installer la configuration logrotate automatiquement. Vous devrez l\'installer manuellement.');
      }
    }
    
    spinner.succeed('Journalisation configurée avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la configuration de la journalisation: ${error.message}`);
    throw error;
  }
}

/**
 * Crée un service systemd (Linux uniquement)
 */
async function createSystemdService(options) {
  if (process.platform !== 'linux') {
    console.log(chalk.yellow('La création de service systemd n\'est disponible que sur Linux.'));
    return;
  }
  
  const spinner = ora('Création du service systemd...').start();
  
  try {
    const serviceFile = path.join(__dirname, 'scripts', 'accounting-module.service');
    const serviceContent = `[Unit]
Description=Module de comptabilité - Le Vieux Moulin
After=network.target postgresql.service

[Service]
Type=simple
User=node
WorkingDirectory=${__dirname}
ExecStart=/usr/bin/node ${__dirname}/index.js
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=accounting-module
Environment=NODE_ENV=${options.environment}
Environment=PORT=${options.config.port}

[Install]
WantedBy=multi-user.target
`;
    
    fs.writeFileSync(serviceFile, serviceContent);
    
    try {
      // Installer le service (nécessite des droits root)
      execSync(`sudo cp ${serviceFile} /etc/systemd/system/`);
      execSync('sudo systemctl daemon-reload');
      execSync('sudo systemctl enable accounting-module.service');
      execSync('sudo systemctl start accounting-module.service');
    } catch (serviceError) {
      spinner.warn('Impossible d\'installer le service systemd automatiquement. Vous devrez l\'installer manuellement.');
    }
    
    spinner.succeed('Service systemd créé avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la création du service systemd: ${error.message}`);
    throw error;
  }
}

/**
 * Crée une configuration Nginx
 */
async function createNginxConfig(options) {
  const spinner = ora('Création de la configuration Nginx...').start();
  
  try {
    const nginxFile = path.join(__dirname, 'scripts', 'accounting-nginx.conf');
    const nginxContent = `server {
    listen 80;
    server_name accounting.levieuxmoulin.example.com;

    location / {
        proxy_pass http://localhost:${options.config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/docs {
        proxy_pass http://localhost:${options.config.port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Configuré pour Let's Encrypt
    location ~ /.well-known {
        allow all;
        root /var/www/html;
    }
}
`;
    
    fs.writeFileSync(nginxFile, nginxContent);
    
    if (process.platform === 'linux') {
      try {
        // Installer la configuration Nginx (nécessite des droits root)
        execSync(`sudo cp ${nginxFile} /etc/nginx/sites-available/accounting-module`);
        execSync('sudo ln -sf /etc/nginx/sites-available/accounting-module /etc/nginx/sites-enabled/');
        execSync('sudo nginx -t'); // Tester la configuration
        execSync('sudo systemctl reload nginx');
      } catch (nginxError) {
        spinner.warn('Impossible d\'installer la configuration Nginx automatiquement. Vous devrez l\'installer manuellement.');
      }
    }
    
    spinner.succeed('Configuration Nginx créée avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors de la création de la configuration Nginx: ${error.message}`);
    throw error;
  }
}

/**
 * Teste le déploiement
 */
async function testDeployment(options) {
  const spinner = ora('Test du déploiement...').start();
  
  try {
    // Initialiser le module avec la configuration de test
    const accountingModule = new AccountingModule({
      configPath: options.configPath,
      environment: options.environment
    });
    
    // Démarrer le module temporairement pour vérifier qu'il fonctionne
    await accountingModule.start();
    
    // Vérifier la connexion à la base de données
    const dbConnections = accountingModule.connectionPool.getAvailablePools();
    if (dbConnections.length === 0) {
      throw new Error('Aucune connexion à la base de données disponible');
    }
    
    // Vérifier les composants critiques
    if (!accountingModule.dataCollector) {
      throw new Error('Le collecteur de données n\'est pas initialisé');
    }
    
    if (!accountingModule.reportGenerator) {
      throw new Error('Le générateur de rapports n\'est pas initialisé');
    }
    
    // Arrêter le module après les tests
    await accountingModule.stop();
    
    spinner.succeed('Déploiement testé avec succès');
  } catch (error) {
    spinner.fail(`Erreur lors du test de déploiement: ${error.message}`);
    throw error;
  }
}

// Exécuter le script
if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  main,
  deployOptions,
  DEFAULT_CONFIG
};
