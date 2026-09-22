import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
});

interface DiagramProps {
  chart: string;
}

export default function DiagramRenderer({ chart }: DiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;

    if (containerRef.current && chart) {
      containerRef.current.innerHTML = ''; // Clear previous SVG graph
      const uniqueId = `mermaid-svg-${Math.floor(Math.random() * 100000)}`;

      mermaid.render(uniqueId, chart)
        .then(({ svg }) => {
          if (isMounted && containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch((err) => {
          console.error("Mermaid Render Error:", err);
        });
    }

    return () => {
      isMounted = false;
    };
  }, [chart]);

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
      <h4 style={{ color: '#00f0ff', margin: '0 0 12px 0', fontSize: '15px' }}>
        📐 Live Target Infrastructure Diagram
      </h4>
      <div ref={containerRef} />
    </div>
  );
}