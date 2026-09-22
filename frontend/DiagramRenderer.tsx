import React from 'react';

interface DiagramProps {
  chart: string;
}

export default function DiagramRenderer({ chart }: DiagramProps) {
  const chartLower = chart.toLowerCase();

  // Prompt/Chart ke basis par exact dynamic SVG layout choose hoga
  let isServerless = chartLower.includes('lambda') || chartLower.includes('dynamodb') || chartLower.includes('api gateway');
  let isContainer = chartLower.includes('ecs') || chartLower.includes('fargate') || chartLower.includes('container');

  return (
    <div style={{
      background: 'rgba(10, 15, 26, 0.9)',
      border: '1px solid rgba(0, 240, 255, 0.4)',
      borderRadius: '12px',
      padding: '20px',
      marginTop: '16px',
      boxShadow: '0 0 20px rgba(0, 240, 255, 0.15)',
      overflowX: 'auto'
    }}>
      <h4 style={{ color: '#00f0ff', margin: '0 0 16px 0', fontSize: '15px' }}>
        📐 Live Target Infrastructure Diagram
      </h4>

      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
        {isServerless ? (
          /* 1. SERVERLESS FLOW SVG */
          <svg width="600" height="120" viewBox="0 0 600 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
            <text x="75" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">👤 User</text>

            <path d="M 130 60 L 170 60" stroke="#00f0ff" strokeWidth="2" markerEnd="url(#arrow)"/>

            <rect x="175" y="35" width="120" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
            <text x="235" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🚪 API Gateway</text>

            <path d="M 295 60 L 335 60" stroke="#00f0ff" strokeWidth="2"/>

            <rect x="340" y="35" width="120" height="50" rx="8" fill="#1e293b" stroke="#10b981" strokeWidth="2"/>
            <text x="400" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚡ AWS Lambda</text>

            <path d="M 460 60 L 495 60" stroke="#10b981" strokeWidth="2"/>

            <rect x="500" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#f59e0b" strokeWidth="2"/>
            <text x="555" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🗄️ DynamoDB</text>
          </svg>

        ) : isContainer ? (
          /* 2. CONTAINER FLOW SVG */
          <svg width="600" height="120" viewBox="0 0 600 120" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="35" width="100" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
            <text x="70" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">👤 User</text>

            <path d="M 120 60 L 160 60" stroke="#00f0ff" strokeWidth="2"/>

            <rect x="165" y="35" width="130" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
            <text x="230" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚖️ Load Balancer</text>

            <path d="M 295 60 L 335 60" stroke="#00f0ff" strokeWidth="2"/>

            <rect x="340" y="35" width="130" height="50" rx="8" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
            <text x="405" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🐳 ECS Fargate Task</text>

            <path d="M 470 60 L 505 60" stroke="#3b82f6" strokeWidth="2"/>

            <rect x="510" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#ef4444" strokeWidth="2"/>
            <text x="565" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚡ Redis Cache</text>
          </svg>

        ) : (
          /* 3. MULTI-AZ EC2/RDS FLOW SVG */
          <svg width="600" height="220" viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg">
            <rect x="240" y="10" width="120" height="35" rx="6" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
            <text x="300" y="32" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">🌐 Route 53 / ALB</text>

            <path d="M 270 45 L 200 80" stroke="#00f0ff" strokeWidth="2"/>
            <path d="M 330 45 L 400 80" stroke="#00f0ff" strokeWidth="2"/>

            <rect x="130" y="80" width="140" height="40" rx="6" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
            <text x="200" y="105" fill="#fff" fontSize="12" textAnchor="middle">AZ 1: EC2 WebServer</text>

            <rect x="330" y="80" width="140" height="40" rx="6" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
            <text x="400" y="105" fill="#fff" fontSize="12" textAnchor="middle">AZ 2: EC2 WebServer</text>

            <path d="M 200 120 L 200 155" stroke="#10b981" strokeWidth="2"/>
            <path d="M 400 120 L 400 155" stroke="#10b981" strokeWidth="2"/>

            <rect x="130" y="155" width="140" height="40" rx="6" fill="#1e293b" stroke="#10b981" strokeWidth="2"/>
            <text x="200" y="180" fill="#fff" fontSize="12" textAnchor="middle">RDS Master DB</text>

            <rect x="330" y="155" width="140" height="40" rx="6" fill="#1e293b" stroke="#f59e0b" strokeWidth="2"/>
            <text x="400" y="180" fill="#fff" fontSize="12" textAnchor="middle">RDS Standby DB</text>

            <path d="M 270 175 L 330 175" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4"/>
          </svg>
        )}
      </div>
    </div>
  );
}