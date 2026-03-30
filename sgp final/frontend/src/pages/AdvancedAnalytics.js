import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const AdvancedAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState({
    caseStats: [],
    processingTrends: [],
    userActivity: [],
    systemMetrics: {},
    complianceStats: {}
  });
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v2/analytics?range=${timeRange}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="loading-spinner"></div>
        <p>Loading analytics data...</p>
      </div>
    );
  }

  return (
    <div className="advanced-analytics">
      <div className="analytics-header">
        <h1>📊 Business Intelligence Dashboard</h1>
        <div className="time-range-selector">
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 3 Months</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon">📁</div>
          <div className="kpi-content">
            <h3>{analyticsData.caseStats.totalCases || 0}</h3>
            <p>Total Cases</p>
            <span className="kpi-trend positive">+{analyticsData.caseStats.newCases || 0} this period</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon">📄</div>
          <div className="kpi-content">
            <h3>{analyticsData.caseStats.totalDocuments || 0}</h3>
            <p>Documents Processed</p>
            <span className="kpi-trend positive">+{analyticsData.caseStats.newDocuments || 0} this period</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon">⚡</div>
          <div className="kpi-content">
            <h3>{analyticsData.systemMetrics.avgProcessingTime || 0}s</h3>
            <p>Avg Processing Time</p>
            <span className="kpi-trend negative">-12% vs last period</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon">✅</div>
          <div className="kpi-content">
            <h3>{analyticsData.complianceStats.complianceRate || 0}%</h3>
            <p>Compliance Rate</p>
            <span className="kpi-trend positive">+5% vs last period</span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        
        {/* Processing Trends */}
        <div className="chart-card">
          <h3>📈 Document Processing Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.processingTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="processed" stroke="#8884d8" strokeWidth={2} />
              <Line type="monotone" dataKey="failed" stroke="#ff7300" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Case Status Distribution */}
        <div className="chart-card">
          <h3>📊 Case Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData.caseStats.statusDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analyticsData.caseStats.statusDistribution?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* User Activity */}
        <div className="chart-card">
          <h3>👥 User Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.userActivity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="cases" fill="#8884d8" />
              <Bar dataKey="documents" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* System Performance */}
        <div className="chart-card">
          <h3>⚡ System Performance Metrics</h3>
          <div className="performance-metrics">
            <div className="metric">
              <label>CPU Usage</label>
              <div className="progress-bar">
                <div 
                  className="progress-fill cpu" 
                  style={{width: `${analyticsData.systemMetrics.cpuUsage || 0}%`}}
                ></div>
              </div>
              <span>{analyticsData.systemMetrics.cpuUsage || 0}%</span>
            </div>
            
            <div className="metric">
              <label>Memory Usage</label>
              <div className="progress-bar">
                <div 
                  className="progress-fill memory" 
                  style={{width: `${analyticsData.systemMetrics.memoryUsage || 0}%`}}
                ></div>
              </div>
              <span>{analyticsData.systemMetrics.memoryUsage || 0}%</span>
            </div>
            
            <div className="metric">
              <label>Disk Usage</label>
              <div className="progress-bar">
                <div 
                  className="progress-fill disk" 
                  style={{width: `${analyticsData.systemMetrics.diskUsage || 0}%`}}
                ></div>
              </div>
              <span>{analyticsData.systemMetrics.diskUsage || 0}%</span>
            </div>
          </div>
        </div>

        {/* Compliance Overview */}
        <div className="chart-card">
          <h3>🛡️ Compliance Overview</h3>
          <div className="compliance-grid">
            <div className="compliance-item">
              <h4>Critical Issues</h4>
              <span className="compliance-count critical">{analyticsData.complianceStats.critical || 0}</span>
            </div>
            <div className="compliance-item">
              <h4>Warnings</h4>
              <span className="compliance-count warning">{analyticsData.complianceStats.warnings || 0}</span>
            </div>
            <div className="compliance-item">
              <h4>Compliant</h4>
              <span className="compliance-count compliant">{analyticsData.complianceStats.compliant || 0}</span>
            </div>
            <div className="compliance-item">
              <h4>Pending Review</h4>
              <span className="compliance-count pending">{analyticsData.complianceStats.pending || 0}</span>
            </div>
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="chart-card full-width">
          <h3>📋 Recent System Activity</h3>
          <div className="activity-feed">
            {analyticsData.recentActivity?.map((activity, index) => (
              <div key={index} className="activity-item">
                <div className="activity-icon">{activity.icon}</div>
                <div className="activity-content">
                  <p>{activity.message}</p>
                  <span className="activity-time">{activity.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAnalytics;
