import { useState } from 'react';
import styles from './Tools.module.scss';

import { SimulationTool } from './components/SimulationTool';
import TaxReportTool from './components/TaxReportTool';
import { BTCReportTool } from './components/BTCReportTool';

type Tool = {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
};

const TOOLS: Tool[] = [
  {
    id: 'simulation',
    title: 'APR Simulator',
    description: 'Simulate your APR and rank based on different COLS/eGLD amounts',
    icon: '🎯',
    color: '#62dbb8'
  },
  {
    id: 'tax-report',
    title: 'Tax Report',
    description: 'Generate a comprehensive yearly report of your staking rewards',
    icon: '📊',
    color: '#d33682'
  },
  {
    id: 'btc-report',
    title: 'BTC Strategy Report',
    description: 'AI-powered BTC market analysis based on 11 technical indicators',
    icon: '₿',
    color: '#f7931a'
  }
];

export const Tools = () => {
  const [activeTool, setActiveTool] = useState<string | null>(null);

  const handleToolClick = (toolId: string) => {
    setActiveTool(toolId);
  };

  const handleBack = () => {
    setActiveTool(null);
  };

  // If a tool is active, show that tool
  if (activeTool === 'simulation') {
    return <SimulationTool onBack={handleBack} />;
  }

  if (activeTool === 'tax-report') {
    return <TaxReportTool onBack={handleBack} />;
  }

  if (activeTool === 'btc-report') {
    return <BTCReportTool onBack={handleBack} />;
  }

  // Landing page with tool cards
  return (
    <div className={styles.tools}>
      <div className={styles.header}>
        <h2>🛠️ Tools</h2>
        <p>Useful tools for Colombia Staking users</p>
      </div>

      <div className={styles.grid}>
        {TOOLS.map((tool) => (
          <div
            key={tool.id}
            className={styles.card}
            onClick={() => handleToolClick(tool.id)}
            style={{ borderColor: tool.color }}
          >
            <div className={styles.cardIcon} style={{ backgroundColor: `${tool.color}20` }}>
              {tool.icon}
            </div>
            <div className={styles.cardContent}>
              <h3>{tool.title}</h3>
              <p>{tool.description}</p>
            </div>
            <div className={styles.cardArrow} style={{ color: tool.color }}>
              →
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
