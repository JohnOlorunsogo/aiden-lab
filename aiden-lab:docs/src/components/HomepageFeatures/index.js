import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Real-Time Monitoring',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    ),
    description: (
      <>
        Event-driven file watching with millisecond response time. Monitor network traffic logs as they happen with instant processing and analysis.
      </>
    ),
  },
  {
    title: 'AI-Powered Analysis',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
      </svg>
    ),
    description: (
      <>
        Self-hosted LLM integration for intelligent root cause analysis. Get actionable solutions powered by advanced language models.
      </>
    ),
  },
  {
    title: 'Pattern Detection',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.35-4.35"/>
        <path d="M11 8v6"/>
        <path d="M8 11h6"/>
      </svg>
    ),
    description: (
      <>
        Automatically detect critical errors, warnings, and anomalies across network logs. Smart pattern matching for rapid issue identification.
      </>
    ),
  },
  {
    title: 'WebSocket Notifications',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
        <path d="M4 2C2.8 3.7 2 5.7 2 8"/>
        <path d="M22 8c0-2.3-.8-4.3-2-6"/>
      </svg>
    ),
    description: (
      <>
        Real-time WebSocket notifications for instant alert delivery. Stay informed of critical events as they occur with persistent connections.
      </>
    ),
  },
  {
    title: 'Dual Capture Modes',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"/>
        <polyline points="2 17 12 22 22 17"/>
        <polyline points="2 12 12 17 22 12"/>
      </svg>
    ),
    description: (
      <>
        Flexible packet capture with both active eNSP integration and passive file watching modes. Adapt to your network environment seamlessly.
      </>
    ),
  },
  {
    title: 'Deduplication',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        <path d="M6 8h8"/>
        <path d="M6 12h5"/>
      </svg>
    ),
    description: (
      <>
        Intelligent deduplication system with similarity scoring. Filter redundant alerts and focus on unique issues that matter most.
      </>
    ),
  },
];

function Feature({icon, title, description}) {
  return (
    <div className={clsx('col col--4', styles.featureCol)}>
      <div className={styles.featureCard}>
        <div className={styles.featureIconWrapper}>
          <div className={styles.featureIcon}>{icon}</div>
        </div>
        <h3 className={styles.featureTitle}>{title}</h3>
        <p className={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>Features</span>
          <h2 className={styles.sectionTitle}>Powerful Network Error Detection</h2>
          <p className={styles.sectionDescription}>
            Advanced tools and AI-driven insights for monitoring, analyzing, and resolving network issues
          </p>
        </div>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
