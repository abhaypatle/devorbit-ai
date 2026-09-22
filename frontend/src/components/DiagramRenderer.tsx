interface DiagramProps {
  chart: string;
}

export default function DiagramRenderer({ chart }: DiagramProps) {
  const chartLower = String(chart || '').toLowerCase();

  const isServerless = 
    chartLower.includes('lambda') || 
    chartLower.includes('dynamodb') || 
    chartLower.includes('serverless') || 
    chartLower.includes('api gateway');

  const isContainer = 
    chartLower.includes('ecs') || 
    chartLower.includes('fargate') || 
    chartLower.includes('container') || 
    chartLower.includes('redis');

  return (
    <div style={{
      background: 'linear-gradient(135deg, #090d16 0%, #05070c 100%)',
      border: '1px solid rgba(0, 240, 255, 0.4)',
      borderRadius: '16px',
      padding: '24px',
      marginTop: '20px',
      boxShadow: '0 10px 30px rgba(0, 240, 255, 0.2)',
      overflowX: 'auto',
      perspective: '1000px'
    }}>
      <style>{`
        @keyframes flowAnimation {
          0% { stroke-dashoffset: 24; }
          100% { stroke-dashoffset: 0; }
        }
        .animated-flow {
          stroke-dasharray: 8, 4;
          animation: flowAnimation 1s linear infinite;
        }
        .node-3d {
          filter: drop-shadow(0px 8px 12px rgba(0,240,255,0.25));
          transition: transform 0.3s ease;
        }
        .node-3d:hover {
          transform: translateY(-4px);
        }
      `}</style>

      <h4 style={{ color: '#00f0ff', margin: '0 0 20px 0', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        🚀 3D Interactive Target Infrastructure & Live Traffic Flow
      </h4>
      <div className="diagram-legend" aria-label="Infrastructure node categories">
        <span><i className="legend-network" /> Networking</span>
        <span><i className="legend-compute" /> Compute</span>
        <span><i className="legend-database" /> Databases</span>
        <span><i className="legend-security" /> Security</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '10px' }}>
        {isServerless ? (
          /* 1. 3D ANIMATED SERVERLESS ARCHITECTURE */
          <svg width="600" height="420" viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad3d" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="100%" stopColor="#0f172a" />
              </linearGradient>
            </defs>

            {/* User Node */}
            <g className="node-3d">
              <rect x="235" y="10" width="130" height="45" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="37" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">👤 Users</text>
            </g>

            {/* Animated Flow Line 1 */}
            <path d="M 300 55 L 300 90" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            {/* API Gateway with AWS Icon */}
            <g className="node-3d">
              <rect x="210" y="90" width="180" height="50" rx="8" fill="url(#grad3d)" stroke="#a855f7" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/b/b9/AWS_Simple_Icons_AWS_Cloud.svg" x="220" y="100" height="30" width="30"/>
              <text x="310" y="120" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">API Gateway</text>
            </g>

            {/* Animated Flow Split */}
            <path d="M 270 140 L 180 190" stroke="#a855f7" strokeWidth="2.5" className="animated-flow"/>
            <path d="M 330 140 L 420 190" stroke="#a855f7" strokeWidth="2.5" className="animated-flow"/>

            {/* VPC Container Box 3D Effect */}
            <rect x="40" y="175" width="520" height="225" rx="12" fill="rgba(15, 23, 42, 0.4)" stroke="#334155" strokeWidth="2" strokeDasharray="6,6"/>
            <text x="65" y="198" fill="#94a3b8" fontSize="11" fontWeight="bold">AWS Cloud Region (Serverless Engine)</text>

            {/* Lambda 1 (Auth) */}
            <g className="node-3d">
              <rect x="80" y="215" width="200" height="60" rx="8" fill="url(#grad3d)" stroke="#10b981" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/5/5c/Amazon_Lambda_architecture_logo.png" x="90" y="227" height="35" width="35"/>
              <text x="190" y="243" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">AWS Lambda</text>
              <text x="190" y="260" fill="#94a3b8" fontSize="10" textAnchor="middle">Auth Microservice</text>
            </g>

            {/* Lambda 2 (API Core) */}
            <g className="node-3d">
              <rect x="320" y="215" width="200" height="60" rx="8" fill="url(#grad3d)" stroke="#10b981" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/5/5c/Amazon_Lambda_architecture_logo.png" x="330" y="227" height="35" width="35"/>
              <text x="430" y="243" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">AWS Lambda</text>
              <text x="430" y="260" fill="#94a3b8" fontSize="10" textAnchor="middle">Core Processing Engine</text>
            </g>

            {/* Animated Flow Line 2 */}
            <path d="M 180 275 L 180 320" stroke="#10b981" strokeWidth="2.5" className="animated-flow"/>
            <path d="M 430 275 L 430 320" stroke="#10b981" strokeWidth="2.5" className="animated-flow"/>

            {/* DynamoDB */}
            <g className="node-3d">
              <rect x="80" y="320" width="200" height="60" rx="8" fill="url(#grad3d)" stroke="#f59e0b" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/f/fd/DynamoDB.png" x="90" y="332" height="35" width="35"/>
              <text x="190" y="348" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">Amazon DynamoDB</text>
              <text x="190" y="365" fill="#f59e0b" fontSize="10" textAnchor="middle">NoSQL Database</text>
            </g>

            {/* S3 Storage */}
            <g className="node-3d">
              <rect x="320" y="320" width="200" height="60" rx="8" fill="url(#grad3d)" stroke="#3b82f6" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/b/bc/Amazon-S3-Logo.svg" x="330" y="332" height="35" width="35"/>
              <text x="430" y="348" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">Amazon S3</text>
              <text x="430" y="365" fill="#3b82f6" fontSize="10" textAnchor="middle">Object Store Bucket</text>
            </g>
          </svg>
        ) : isContainer ? (
          /* 2. 3D ANIMATED CONTAINER ARCHITECTURE */
          <svg width="600" height="420" viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad3d" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="100%" stopColor="#0f172a" />
              </linearGradient>
            </defs>

            <g className="node-3d">
              <rect x="235" y="10" width="130" height="45" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="37" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">👤 Traffic Source</text>
            </g>

            <path d="M 300 55 L 300 90" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            <g className="node-3d">
              <rect x="195" y="90" width="210" height="50" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="120" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">⚖️ Application Load Balancer</text>
            </g>

            <path d="M 250 140 L 180 190" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>
            <path d="M 350 140 L 420 190" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            <rect x="40" y="175" width="520" height="225" rx="12" fill="rgba(15, 23, 42, 0.4)" stroke="#3b82f6" strokeWidth="2"/>
            <text x="65" y="198" fill="#94a3b8" fontSize="11" fontWeight="bold">AWS ECS Cluster (Fargate Compute Tier)</text>

            <g className="node-3d">
              <rect x="70" y="215" width="220" height="65" rx="8" fill="url(#grad3d)" stroke="#3b82f6" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/4/4e/Docker_%28container_engine%29_logo.svg" x="80" y="230" height="35" width="35"/>
              <text x="190" y="245" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">AZ 1: ECS Task</text>
              <text x="190" y="262" fill="#3b82f6" fontSize="10" textAnchor="middle">🐳 App Container Instance</text>
            </g>

            <g className="node-3d">
              <rect x="310" y="215" width="220" height="65" rx="8" fill="url(#grad3d)" stroke="#3b82f6" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/4/4e/Docker_%28container_engine%29_logo.svg" x="320" y="230" height="35" width="35"/>
              <text x="430" y="245" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">AZ 2: ECS Task</text>
              <text x="430" y="262" fill="#3b82f6" fontSize="10" textAnchor="middle">🐳 App Container Instance</text>
            </g>

            <path d="M 180 280 L 180 320" stroke="#ef4444" strokeWidth="2.5" className="animated-flow"/>
            <path d="M 430 280 L 430 320" stroke="#ef4444" strokeWidth="2.5" className="animated-flow"/>

            <g className="node-3d">
              <rect x="140" y="320" width="320" height="60" rx="8" fill="url(#grad3d)" stroke="#ef4444" strokeWidth="2"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/6/6b/Redis_Logo.svg" x="155" y="332" height="35" width="35"/>
              <text x="310" y="348" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">ElastiCache Redis Cluster</text>
              <text x="310" y="365" fill="#ef4444" fontSize="10" textAnchor="middle">In-Memory Cache & Session State</text>
            </g>
          </svg>
        ) : (
          /* 3. 3D ANIMATED ENTERPRISE MULTI-AZ ARCHITECTURE WITH LOGOS */
          <svg width="600" height="480" viewBox="0 0 600 480" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="grad3d" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="100%" stopColor="#0f172a" />
              </linearGradient>
            </defs>

            <g className="node-3d">
              <rect x="240" y="10" width="120" height="40" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="35" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">👤 Users</text>
            </g>

            <path d="M 300 50 L 300 80" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            <g className="node-3d">
              <rect x="220" y="80" width="160" height="40" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="105" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">🌐 Route 53 DNS</text>
            </g>

            <path d="M 300 120 L 300 150" stroke="#f59e0b" strokeWidth="2.5" className="animated-flow"/>

            <g className="node-3d">
              <rect x="210" y="150" width="180" height="40" rx="8" fill="url(#grad3d)" stroke="#f59e0b" strokeWidth="2"/>
              <text x="300" y="175" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">🚪 Internet Gateway</text>
            </g>

            <path d="M 300 190 L 300 220" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            <g className="node-3d">
              <rect x="190" y="220" width="220" height="40" rx="8" fill="url(#grad3d)" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="245" fill="#fff" fontSize="12" textAnchor="middle" fontWeight="bold">⚖️ Application Load Balancer</text>
            </g>

            <path d="M 250 260 L 170 290" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>
            <path d="M 350 260 L 430 290" stroke="#00f0ff" strokeWidth="2.5" className="animated-flow"/>

            {/* VPC Grid Frame */}
            <rect x="40" y="275" width="520" height="190" rx="10" fill="rgba(15, 23, 42, 0.6)" stroke="#64748b" strokeWidth="2"/>
            <text x="300" y="292" fill="#94a3b8" fontSize="11" textAnchor="middle" fontWeight="bold">AWS Multi-AZ VPC Topography</text>

            {/* AZ 1 */}
            <rect x="60" y="300" width="220" height="80" rx="6" fill="rgba(30, 41, 59, 0.8)" stroke="#3b82f6" strokeWidth="1.5"/>
            <text x="170" y="318" fill="#cbd5e1" fontSize="10" textAnchor="middle" fontWeight="bold">AZ 1: us-east-1a</text>
            <g className="node-3d">
              <rect x="75" y="325" width="190" height="45" rx="6" fill="#0f172a" stroke="#00f0ff" strokeWidth="1.5"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/5/5c/Amazon_Lambda_architecture_logo.png" x="85" y="332" height="30" width="30"/>
              <text x="180" y="352" fill="#fff" fontSize="11" textAnchor="middle" fontWeight="bold">EC2 WebServer 1</text>
            </g>

            {/* AZ 2 */}
            <rect x="320" y="300" width="220" height="80" rx="6" fill="rgba(30, 41, 59, 0.8)" stroke="#3b82f6" strokeWidth="1.5"/>
            <text x="430" y="318" fill="#cbd5e1" fontSize="10" textAnchor="middle" fontWeight="bold">AZ 2: us-east-1b</text>
            <g className="node-3d">
              <rect x="335" y="325" width="190" height="45" rx="6" fill="#0f172a" stroke="#00f0ff" strokeWidth="1.5"/>
              <image href="https://upload.wikimedia.org/wikipedia/commons/5/5c/Amazon_Lambda_architecture_logo.png" x="345" y="332" height="30" width="30"/>
              <text x="440" y="352" fill="#fff" fontSize="11" textAnchor="middle" fontWeight="bold">EC2 WebServer 2</text>
            </g>

            <path d="M 170 380 L 170 405" stroke="#10b981" strokeWidth="2" className="animated-flow"/>
            <path d="M 430 380 L 430 405" stroke="#10b981" strokeWidth="2" className="animated-flow"/>

            {/* RDS DB Nodes */}
            <g className="node-3d">
              <rect x="75" y="405" width="190" height="45" rx="6" fill="url(#grad3d)" stroke="#10b981" strokeWidth="2"/>
              <text x="170" y="432" fill="#fff" fontSize="11" textAnchor="middle" fontWeight="bold">🗄️ RDS Master DB</text>
            </g>

            <g className="node-3d">
              <rect x="335" y="405" width="190" height="45" rx="6" fill="url(#grad3d)" stroke="#f59e0b" strokeWidth="2"/>
              <text x="440" y="432" fill="#fff" fontSize="11" textAnchor="middle" fontWeight="bold">🗄️ RDS Standby DB</text>
            </g>

            {/* Sync Line */}
            <path d="M 265 427 L 335 427" stroke="#f59e0b" strokeWidth="2" className="animated-flow"/>
            <text x="300" y="420" fill="#f59e0b" fontSize="9" textAnchor="middle">Sync</text>
          </svg>
        )}
      </div>
    </div>
  );
}