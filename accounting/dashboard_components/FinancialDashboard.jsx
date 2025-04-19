/**
 * Composant de tableau de bord financier pour Le Vieux Moulin
 * 
 * Ce composant React fournit une interface utilisateur interactive pour
 * visualiser les données financières et comptables du restaurant.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';

/**
 * Composant principal du tableau de bord financier
 * @param {Object} props - Propriétés du composant
 * @param {string} props.apiBaseUrl - URL de base de l'API comptabilité
 * @param {Object} props.initialData - Données initiales (optionnel)
 * @param {function} props.onDataLoad - Callback après chargement des données
 * @param {string} props.timeRange - Période à afficher (day, week, month, year)
 * @param {array} props.metrics - Métriques à afficher
 */
const FinancialDashboard = ({
  apiBaseUrl = '/api/accounting',
  initialData = null,
  onDataLoad = () => {},
  timeRange = 'month',
  metrics = ['revenue', 'costs', 'margins']
}) => {
  // État pour stocker les données financières
  const [financialData, setFinancialData] = useState(initialData || {
    revenue: [],
    costs: [],
    margins: [],
    cashflow: [],
    loading: true,
    error: null
  });
  
  // État pour les filtres et options d'affichage
  const [filters, setFilters] = useState({
    timeRange: timeRange,
    comparison: 'previous', // 'previous', 'target', 'forecast'
    showForecast: true,
    groupBy: 'day', // 'day', 'week', 'month'
    selectedCategory: 'all'
  });
  
  // État pour les KPIs principaux
  const [kpis, setKpis] = useState({
    dailyRevenue: 0,
    weeklyRevenue: 0,
    monthlyRevenue: 0,
    grossMargin: 0,
    netMargin: 0,
    cashOnHand: 0
  });
  
  // Effet pour charger les données financières
  useEffect(() => {
    // Éviter le chargement si des données initiales sont fournies
    if (initialData) {
      setFinancialData({
        ...initialData,
        loading: false
      });
      onDataLoad(initialData);
      return;
    }
    
    const fetchFinancialData = async () => {
      try {
        setFinancialData(prev => ({ ...prev, loading: true, error: null }));
        
        // Calculer la période basée sur le timeRange
        const endDate = new Date();
        let startDate;
        
        switch (filters.timeRange) {
          case 'day':
            startDate = new Date();
            startDate.setHours(0, 0, 0, 0);
            break;
          case 'week':
            startDate = new Date();
            startDate.setDate(startDate.getDate() - 7);
            break;
          case 'month':
            startDate = new Date();
            startDate.setMonth(startDate.getMonth() - 1);
            break;
          case 'year':
            startDate = new Date();
            startDate.setFullYear(startDate.getFullYear() - 1);
            break;
          default:
            startDate = new Date();
            startDate.setMonth(startDate.getMonth() - 1);
        }
        
        // Appel à l'API pour récupérer les données financières
        const response = await fetch(`${apiBaseUrl}/financial_tracking/data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            startDate: startDate.toISOString(),
            endDate: endDate.toISOString(),
            metrics: metrics,
            groupBy: filters.groupBy
          })
        });
        
        if (!response.ok) {
          throw new Error(`Erreur API: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Mise à jour des données
        setFinancialData({
          ...data,
          loading: false,
          error: null
        });
        
        // Calculer les KPIs
        calculateKPIs(data);
        
        // Callback
        onDataLoad(data);
        
      } catch (error) {
        console.error('Erreur lors du chargement des données financières', error);
        setFinancialData(prev => ({
          ...prev,
          loading: false,
          error: error.message || 'Erreur de chargement des données'
        }));
      }
    };
    
    fetchFinancialData();
  }, [apiBaseUrl, filters.timeRange, filters.groupBy, metrics, initialData, onDataLoad]);
  
  // Calcul des KPIs basé sur les données
  const calculateKPIs = (data) => {
    if (!data.revenue || data.revenue.length === 0) return;
    
    // Calculer le revenu quotidien (dernier jour)
    const dailyRevenue = data.revenue[data.revenue.length - 1]?.value || 0;
    
    // Calculer le revenu hebdomadaire (7 derniers jours)
    const lastWeekData = data.revenue.slice(-7);
    const weeklyRevenue = lastWeekData.reduce((sum, item) => sum + item.value, 0);
    
    // Calculer le revenu mensuel (30 derniers jours)
    const lastMonthData = data.revenue.slice(-30);
    const monthlyRevenue = lastMonthData.reduce((sum, item) => sum + item.value, 0);
    
    // Calculer la marge brute (si les données de marge sont disponibles)
    let grossMargin = 0;
    if (data.margins && data.margins.length > 0) {
      // Moyenne des marges sur la période
      const marginValues = data.margins.map(item => item.value);
      grossMargin = marginValues.reduce((sum, value) => sum + value, 0) / marginValues.length;
    } else if (data.revenue && data.costs) {
      // Calculer à partir des revenus et coûts
      const totalRevenue = data.revenue.reduce((sum, item) => sum + item.value, 0);
      const totalCosts = data.costs.reduce((sum, item) => sum + item.value, 0);
      grossMargin = totalRevenue > 0 ? ((totalRevenue - totalCosts) / totalRevenue) * 100 : 0;
    }
    
    // Calculer la marge nette (estimation)
    const netMargin = grossMargin * 0.7; // Simplification pour l'exemple
    
    // Flux de trésorerie (si disponible)
    let cashOnHand = 0;
    if (data.cashflow && data.cashflow.length > 0) {
      cashOnHand = data.cashflow[data.cashflow.length - 1]?.value || 0;
    }
    
    // Mise à jour des KPIs
    setKpis({
      dailyRevenue,
      weeklyRevenue,
      monthlyRevenue,
      grossMargin,
      netMargin,
      cashOnHand
    });
  };
  
  // Préparation des données pour les graphiques avec mémorisation
  const chartData = useMemo(() => {
    if (!financialData || financialData.loading) return [];
    
    // Préparer les données de séries temporelles
    const timeSeriesData = [];
    
    // Déterminer la longueur maximale des séries
    const maxLength = Math.max(
      financialData.revenue?.length || 0,
      financialData.costs?.length || 0,
      financialData.margins?.length || 0,
      financialData.cashflow?.length || 0
    );
    
    // Fusionner les séries par date
    for (let i = 0; i < maxLength; i++) {
      const dataPoint = {
        date: null
      };
      
      // Ajouter les métriques disponibles
      if (financialData.revenue && i < financialData.revenue.length) {
        dataPoint.date = financialData.revenue[i].date;
        dataPoint.revenue = financialData.revenue[i].value;
      }
      
      if (financialData.costs && i < financialData.costs.length) {
        if (!dataPoint.date) dataPoint.date = financialData.costs[i].date;
        dataPoint.costs = financialData.costs[i].value;
      }
      
      if (financialData.margins && i < financialData.margins.length) {
        if (!dataPoint.date) dataPoint.date = financialData.margins[i].date;
        dataPoint.margins = financialData.margins[i].value;
      }
      
      if (financialData.cashflow && i < financialData.cashflow.length) {
        if (!dataPoint.date) dataPoint.date = financialData.cashflow[i].date;
        dataPoint.cashflow = financialData.cashflow[i].value;
      }
      
      // Formater la date pour l'affichage
      if (dataPoint.date) {
        const date = new Date(dataPoint.date);
        dataPoint.formattedDate = formatDate(date, filters.groupBy);
      }
      
      timeSeriesData.push(dataPoint);
    }
    
    return timeSeriesData;
  }, [financialData, filters.groupBy]);
  
  // Formatage de date selon le niveau de regroupement
  const formatDate = (date, groupBy) => {
    if (!date) return '';
    
    const d = new Date(date);
    switch (groupBy) {
      case 'day':
        return `${d.getDate()}/${d.getMonth() + 1}`;
      case 'week':
        return `Sem ${getWeekNumber(d)}`;
      case 'month':
        return ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'][d.getMonth()];
      default:
        return `${d.getDate()}/${d.getMonth() + 1}`;
    }
  };
  
  // Obtenir le numéro de semaine
  const getWeekNumber = (date) => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  };
  
  // Changer de période d'affichage
  const handleTimeRangeChange = (range) => {
    setFilters(prev => ({ ...prev, timeRange: range }));
  };
  
  // Changer de mode de regroupement
  const handleGroupByChange = (groupBy) => {
    setFilters(prev => ({ ...prev, groupBy }));
  };
  
  // Basculer l'affichage des prévisions
  const toggleForecast = () => {
    setFilters(prev => ({ ...prev, showForecast: !prev.showForecast }));
  };
  
  // Personnalisation des couleurs pour les graphiques
  const COLORS = {
    revenue: '#4CAF50',
    costs: '#F44336',
    margins: '#2196F3',
    cashflow: '#FF9800',
    profit: '#8BC34A',
    loss: '#E91E63'
  };
  
  return (
    <div className="financial-dashboard">
      {/* Entête du tableau de bord */}
      <div className="dashboard-header">
        <h1>Tableau de Bord Financier - Le Vieux Moulin</h1>
        
        {/* Contrôles de filtrage */}
        <div className="dashboard-controls">
          <div className="time-range-controls">
            <button 
              className={filters.timeRange === 'day' ? 'active' : ''} 
              onClick={() => handleTimeRangeChange('day')}
            >
              Jour
            </button>
            <button 
              className={filters.timeRange === 'week' ? 'active' : ''} 
              onClick={() => handleTimeRangeChange('week')}
            >
              Semaine
            </button>
            <button 
              className={filters.timeRange === 'month' ? 'active' : ''} 
              onClick={() => handleTimeRangeChange('month')}
            >
              Mois
            </button>
            <button 
              className={filters.timeRange === 'year' ? 'active' : ''} 
              onClick={() => handleTimeRangeChange('year')}
            >
              Année
            </button>
          </div>
          
          <div className="group-by-controls">
            <label>Grouper par:</label>
            <select 
              value={filters.groupBy} 
              onChange={(e) => handleGroupByChange(e.target.value)}
            >
              <option value="day">Jour</option>
              <option value="week">Semaine</option>
              <option value="month">Mois</option>
            </select>
          </div>
          
          <div className="forecast-controls">
            <label>
              <input 
                type="checkbox" 
                checked={filters.showForecast} 
                onChange={toggleForecast} 
              />
              Afficher les prévisions
            </label>
          </div>
        </div>
      </div>
      
      {/* Affichage des erreurs */}
      {financialData.error && (
        <div className="error-message">
          <p>Erreur: {financialData.error}</p>
          <button onClick={() => setFinancialData(prev => ({ ...prev, error: null }))}>
            Fermer
          </button>
        </div>
      )}
      
      {/* Indicateurs de chargement */}
      {financialData.loading && (
        <div className="loading-indicator">
          <p>Chargement des données financières...</p>
        </div>
      )}
      
      {/* Cartes KPI */}
      <div className="kpi-cards">
        <div className="kpi-card">
          <h3>CA Quotidien</h3>
          <div className="kpi-value">{kpis.dailyRevenue.toLocaleString('fr-FR')} €</div>
        </div>
        
        <div className="kpi-card">
          <h3>CA Hebdomadaire</h3>
          <div className="kpi-value">{kpis.weeklyRevenue.toLocaleString('fr-FR')} €</div>
        </div>
        
        <div className="kpi-card">
          <h3>CA Mensuel</h3>
          <div className="kpi-value">{kpis.monthlyRevenue.toLocaleString('fr-FR')} €</div>
        </div>
        
        <div className="kpi-card">
          <h3>Marge Brute</h3>
          <div className="kpi-value">{kpis.grossMargin.toFixed(2)} %</div>
        </div>
        
        <div className="kpi-card">
          <h3>Marge Nette</h3>
          <div className="kpi-value">{kpis.netMargin.toFixed(2)} %</div>
        </div>
        
        <div className="kpi-card">
          <h3>Trésorerie</h3>
          <div className="kpi-value">{kpis.cashOnHand.toLocaleString('fr-FR')} €</div>
        </div>
      </div>
      
      {/* Graphiques */}
      <div className="dashboard-charts">
        {/* Graphique d'évolution du chiffre d'affaires */}
        <div className="chart-container">
          <h2>Évolution du Chiffre d'Affaires</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formattedDate" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value.toLocaleString('fr-FR')} €`, 'CA']} />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="revenue" 
                name="Chiffre d'Affaires" 
                stroke={COLORS.revenue} 
                fill={COLORS.revenue} 
                fillOpacity={0.3}
              />
              {filters.showForecast && financialData.revenueForecast && (
                <Area 
                  type="monotone" 
                  dataKey="revenueForecast" 
                  name="Prévision CA" 
                  stroke={COLORS.revenue} 
                  strokeDasharray="5 5"
                  fill={COLORS.revenue} 
                  fillOpacity={0.1}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Graphique de CA vs Coûts */}
        <div className="chart-container">
          <h2>CA vs Coûts</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formattedDate" />
              <YAxis />
              <Tooltip 
                formatter={(value) => [`${value.toLocaleString('fr-FR')} €`]} 
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Bar 
                dataKey="revenue" 
                name="Chiffre d'Affaires" 
                fill={COLORS.revenue} 
              />
              <Bar 
                dataKey="costs" 
                name="Coûts" 
                fill={COLORS.costs} 
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* Graphique des marges */}
        <div className="chart-container">
          <h2>Évolution des Marges</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formattedDate" />
              <YAxis />
              <Tooltip 
                formatter={(value) => [`${value.toFixed(2)} %`]} 
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="margins" 
                name="Marge" 
                stroke={COLORS.margins} 
                activeDot={{ r: 8 }} 
              />
              {filters.showForecast && financialData.marginsForecast && (
                <Line 
                  type="monotone" 
                  dataKey="marginsForecast" 
                  name="Prévision Marge" 
                  stroke={COLORS.margins} 
                  strokeDasharray="5 5"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Répartition des coûts (Graphique en camembert) */}
        {financialData.costBreakdown && (
          <div className="chart-container">
            <h2>Répartition des Coûts</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={financialData.costBreakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="category"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {financialData.costBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.category] || `#${Math.floor(Math.random()*16777215).toString(16)}`} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value.toLocaleString('fr-FR')} €`]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      
      {/* Section alertes et recommandations */}
      {financialData.alerts && financialData.alerts.length > 0 && (
        <div className="alerts-section">
          <h2>Alertes et Recommandations</h2>
          <ul className="alerts-list">
            {financialData.alerts.map((alert, index) => (
              <li key={index} className={`alert-item alert-${alert.severity}`}>
                <div className="alert-header">
                  <span className="alert-icon">
                    {alert.severity === 'critical' ? '🔴' : 
                     alert.severity === 'warning' ? '🟠' : 
                     alert.severity === 'info' ? 'ℹ️' : '✅'}
                  </span>
                  <h3>{alert.title}</h3>
                </div>
                <p>{alert.message}</p>
                {alert.recommendation && (
                  <div className="alert-recommendation">
                    <strong>Recommandation:</strong> {alert.recommendation}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Pied de page */}
      <div className="dashboard-footer">
        <p>
          Données mises à jour le: {new Date().toLocaleString('fr-FR')}
          {financialData.dataTimestamp && ` - Source: ${new Date(financialData.dataTimestamp).toLocaleString('fr-FR')}`}
        </p>
        <p>
          Module de comptabilité avancé - Le Vieux Moulin © 2025
        </p>
      </div>
    </div>
  );
};

export default FinancialDashboard;
