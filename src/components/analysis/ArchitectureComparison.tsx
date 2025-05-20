import React, { useState, useMemo } from 'react';
import { Architecture } from '../../types/architecture';

interface Metric {
  name: string;
  value: number;
  description?: string;
}

interface PerformanceMetrics {
  [key: string]: Metric[];
}

interface ArchitectureComparisonProps {
  configurations: {
    id: string;
    name: string;
    architecture: Architecture;
    metrics?: Metric[];
  }[];
  metrics: PerformanceMetrics;
  onSelectConfiguration?: (configId: string) => void;
}

const ArchitectureComparison: React.FC<ArchitectureComparisonProps> = ({
  configurations,
  metrics,
  onSelectConfiguration
}) => {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'nodes' | 'connections' | 'metric'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showDetails, setShowDetails] = useState<string | null>(null);

  // List of available metrics
  const availableMetrics = useMemo(() => {
    const allMetrics: string[] = [];
    Object.values(metrics).forEach(configMetrics => {
      configMetrics.forEach(metric => {
        if (!allMetrics.includes(metric.name)) {
          allMetrics.push(metric.name);
        }
      });
    });
    return allMetrics;
  }, [metrics]);

  // Sort configurations
  const sortedConfigurations = useMemo(() => {
    return [...configurations].sort((a, b) => {
      if (sortBy === 'name') {
        return sortOrder === 'asc' 
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name);
      } else if (sortBy === 'nodes') {
        return sortOrder === 'asc'
          ? a.architecture.nodes.length - b.architecture.nodes.length
          : b.architecture.nodes.length - a.architecture.nodes.length;
      } else if (sortBy === 'connections') {
        return sortOrder === 'asc'
          ? a.architecture.connections.length - b.architecture.connections.length
          : b.architecture.connections.length - a.architecture.connections.length;
      } else if (sortBy === 'metric' && selectedMetric) {
        const aMetrics = metrics[a.id] || [];
        const bMetrics = metrics[b.id] || [];
        const aMetric = aMetrics.find(m => m.name === selectedMetric)?.value || 0;
        const bMetric = bMetrics.find(m => m.name === selectedMetric)?.value || 0;
        return sortOrder === 'asc' ? aMetric - bMetric : bMetric - aMetric;
      }
      return 0;
    });
  }, [configurations, sortBy, sortOrder, selectedMetric, metrics]);

  // Toggle sort order
  const toggleSort = (key: 'name' | 'nodes' | 'connections' | 'metric') => {
    if (sortBy === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortOrder('asc');
    }
  };

  // Get node type counts
  const getNodeTypeCounts = (architecture: Architecture) => {
    const counts: Record<string, number> = {};
    architecture.nodes.forEach(node => {
      const type = node.type || 'default';
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  };

  // Get connection type counts
  const getConnectionTypeCounts = (architecture: Architecture) => {
    const counts: Record<string, number> = {};
    architecture.connections.forEach(conn => {
      const type = conn.type || 'default';
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  };

  // Get metric value by name
  const getMetricValue = (configId: string, metricName: string) => {
    const configMetrics = metrics[configId] || [];
    const metric = configMetrics.find(m => m.name === metricName);
    return metric ? metric.value : null;
  };

  // Format metric value
  const formatMetricValue = (value: number | null) => {
    if (value === null) return '-';
    return value.toFixed(2);
  };

  // Get highest and lowest metric values
  const getMetricExtremes = (metricName: string) => {
    const values = configurations
      .map(config => getMetricValue(config.id, metricName))
      .filter(v => v !== null) as number[];
    
    if (values.length === 0) return { min: null, max: null };
    
    return {
      min: Math.min(...values),
      max: Math.max(...values)
    };
  };

  // Neon styles
  const neonTextStyle = 'text-cyan-300';
  const neonBorderStyle = 'border-cyan-500/30';
  
  return (
    <div className="space-y-6">
      <h2 className={`text-2xl font-semibold ${neonTextStyle}`} style={{ textShadow: '0 0 3px #06b6d4' }}>
        Architecture Comparison
      </h2>
      
      {/* Metric Selection */}
      <div className="flex space-x-4 items-center">
        <label htmlFor="metric-select" className={`text-sm ${neonTextStyle}`}>
          Compare by metric:
        </label>
        <select
          id="metric-select"
          value={selectedMetric || ''}
          onChange={(e) => setSelectedMetric(e.target.value || null)}
          className="bg-gray-800 border border-gray-700 text-gray-100 text-sm rounded-lg focus:ring-cyan-500 focus:border-cyan-500 block p-2"
        >
          <option value="">Select a metric</option>
          {availableMetrics.map(metric => (
            <option key={metric} value={metric}>{metric}</option>
          ))}
        </select>
      </div>
      
      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-300">
          <thead className="text-xs uppercase bg-gray-800 text-gray-400">
            <tr>
              <th 
                scope="col" 
                className="px-6 py-3 cursor-pointer"
                onClick={() => toggleSort('name')}
              >
                <div className="flex items-center">
                  Configuration
                  {sortBy === 'name' && (
                    <span className="ml-1">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 cursor-pointer"
                onClick={() => toggleSort('nodes')}
              >
                <div className="flex items-center">
                  Nodes
                  {sortBy === 'nodes' && (
                    <span className="ml-1">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 cursor-pointer"
                onClick={() => toggleSort('connections')}
              >
                <div className="flex items-center">
                  Connections
                  {sortBy === 'connections' && (
                    <span className="ml-1">
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
              {selectedMetric && (
                <th 
                  scope="col" 
                  className="px-6 py-3 cursor-pointer"
                  onClick={() => toggleSort('metric')}
                >
                  <div className="flex items-center">
                    {selectedMetric}
                    {sortBy === 'metric' && (
                      <span className="ml-1">
                        {sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              )}
              <th scope="col" className="px-6 py-3">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedConfigurations.map(config => {
              const nodeCount = config.architecture.nodes.length;
              const connectionCount = config.architecture.connections.length;
              const metricValue = selectedMetric ? getMetricValue(config.id, selectedMetric) : null;
              const { min: minMetric, max: maxMetric } = selectedMetric ? getMetricExtremes(selectedMetric) : { min: null, max: null };
              
              // Determine if this is best or worst for the selected metric
              const isBest = metricValue !== null && maxMetric !== null && metricValue === maxMetric;
              const isWorst = metricValue !== null && minMetric !== null && metricValue === minMetric;
              
              return (
                <React.Fragment key={config.id}>
                  <tr className="bg-gray-900 border-b border-gray-800 hover:bg-gray-800">
                    <th scope="row" className="px-6 py-4 font-medium whitespace-nowrap text-white">
                      {config.name}
                    </th>
                    <td className="px-6 py-4">
                      {nodeCount}
                    </td>
                    <td className="px-6 py-4">
                      {connectionCount}
                    </td>
                    {selectedMetric && (
                      <td className={`px-6 py-4 ${isBest ? 'text-green-400' : isWorst ? 'text-red-400' : ''}`}>
                        {formatMetricValue(metricValue)}
                      </td>
                    )}
                    <td className="px-6 py-4 text-right">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setShowDetails(showDetails === config.id ? null : config.id)}
                          className="text-cyan-500 hover:text-cyan-400"
                        >
                          {showDetails === config.id ? 'Hide' : 'Details'}
                        </button>
                        {onSelectConfiguration && (
                          <button
                            onClick={() => onSelectConfiguration(config.id)}
                            className="text-emerald-500 hover:text-emerald-400"
                          >
                            Load
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  
                  {/* Details Row */}
                  {showDetails === config.id && (
                    <tr className="bg-gray-800/30">
                      <td colSpan={selectedMetric ? 5 : 4} className="px-6 py-4">
                        <div className="grid grid-cols-3 gap-4">
                          {/* Node Types */}
                          <div>
                            <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>Node Types</h4>
                            <div className="space-y-1 text-xs">
                              {Object.entries(getNodeTypeCounts(config.architecture)).map(([type, count]) => (
                                <div key={type} className="flex justify-between">
                                  <span>{type}:</span>
                                  <span>{count}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          {/* Connection Types */}
                          <div>
                            <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>Connection Types</h4>
                            <div className="space-y-1 text-xs">
                              {Object.entries(getConnectionTypeCounts(config.architecture)).map(([type, count]) => (
                                <div key={type} className="flex justify-between">
                                  <span>{type}:</span>
                                  <span>{count}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          {/* Metrics */}
                          <div>
                            <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>All Metrics</h4>
                            <div className="space-y-1 text-xs">
                              {(metrics[config.id] || []).map(metric => (
                                <div key={metric.name} className="flex justify-between">
                                  <span>{metric.name}:</span>
                                  <span>{metric.value.toFixed(2)}</span>
                                </div>
                              ))}
                              {(!metrics[config.id] || metrics[config.id].length === 0) && (
                                <div className="text-gray-500">No metrics available</div>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {/* Visualization */}
      {selectedMetric && (
        <div className="border border-cyan-500/20 rounded p-4">
          <h3 className={`text-lg font-medium ${neonTextStyle} mb-4`}>Metric Comparison: {selectedMetric}</h3>
          
          <div className="space-y-3">
            {sortedConfigurations.map(config => {
              const metricValue = getMetricValue(config.id, selectedMetric);
              const { max: maxMetric } = getMetricExtremes(selectedMetric);
              
              if (metricValue === null || maxMetric === null) return null;
              
              const percentage = (metricValue / maxMetric) * 100;
              
              // Determine color based on value compared to others
              const getBarColor = () => {
                if (metricValue === maxMetric) return 'bg-green-500';
                if (percentage > 75) return 'bg-green-600';
                if (percentage > 50) return 'bg-cyan-600';
                if (percentage > 25) return 'bg-yellow-600';
                return 'bg-red-600';
              };
              
              return (
                <div key={config.id} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>{config.name}</span>
                    <span>{metricValue.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2.5">
                    <div 
                      className={`${getBarColor()} h-2.5 rounded-full`} 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ArchitectureComparison;