import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import styles from './index.module.css';

function FloatingElement({ className, delay = 0 }) {
  return (
    <div 
      className={clsx(styles.floatingElement, className)}
      style={{ animationDelay: `${delay}s` }}
    />
  );
}

function HeroBackground() {
  return (
    <div className={styles.heroBackground}>
      <div className={styles.gradientOrb1} />
      <div className={styles.gradientOrb2} />
      <div className={styles.gradientOrb3} />
      <div className={styles.meshGradient} />
      <FloatingElement className={styles.float1} delay={0} />
      <FloatingElement className={styles.float2} delay={2} />
      <FloatingElement className={styles.float3} delay={4} />
    </div>
  );
}

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={styles.heroBanner}>
      <HeroBackground />
      <div className={clsx('container', styles.heroContainer)}>
        <div className={styles.heroContent}>
          <div className={styles.heroBadge}>
            <span className={styles.badgePulse} />
            <span>AI-Powered Network Intelligence</span>
          </div>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <div className={styles.buttons}>
            <Link
              className={clsx(styles.button, styles.buttonPrimary)}
              to="/docs/intro">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              Get Started
            </Link>
            <Link
              className={clsx(styles.button, styles.buttonSecondary)}
              to="/docs/architecture">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
              View Docs
            </Link>
          </div>
        </div>
        <div className={styles.heroVisual}>
          <div className={styles.codePreview}>
            <div className={styles.codeHeader}>
              <div className={styles.codeDot} />
              <div className={styles.codeDot} />
              <div className={styles.codeDot} />
              <span className={styles.codeTitle}>network-analysis.log</span>
            </div>
            <pre className={styles.codeContent}>
              <code>
{`[2024-03-02 14:23:15] INFO: Monitoring started
[2024-03-02 14:23:18] WARN: High latency detected
[2024-03-02 14:23:20] ERROR: Connection timeout
[2024-03-02 14:23:21] AI: Analyzing root cause...
[2024-03-02 14:23:22] AI: Pattern identified
[2024-03-02 14:23:23] AI: Solution generated`}
              </code>
            </pre>
          </div>
        </div>
      </div>
    </header>
  );
}

function StatsSection() {
  const stats = [
    { value: '< 100ms', label: 'Response Time' },
    { value: '99.9%', label: 'Uptime' },
    { value: '24/7', label: 'Monitoring' },
    { value: 'AI', label: 'Powered Analysis' },
  ];

  return (
    <section className={styles.statsSection}>
      <div className="container">
        <div className={styles.statsGrid}>
          {stats.map((stat, idx) => (
            <div key={idx} className={styles.statCard}>
              <div className={styles.statValue}>{stat.value}</div>
              <div className={styles.statLabel}>{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className={styles.ctaSection}>
      <div className={styles.ctaBackground}>
        <div className={styles.ctaGlow1} />
        <div className={styles.ctaGlow2} />
      </div>
      <div className={clsx('container', styles.ctaContainer)}>
        <div className={styles.ctaContent}>
          <h2 className={styles.ctaTitle}>Ready to enhance your network monitoring?</h2>
          <p className={styles.ctaDescription}>
            Get started with AIDEN Labs today and transform how you detect and resolve network errors
          </p>
          <div className={styles.ctaButtons}>
            <Link
              className={clsx(styles.button, styles.buttonPrimary, styles.buttonLarge)}
              to="/docs/intro">
              Start Building
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - ENSP Logger System`}
      description="AI-Powered Network Error Detection for Huawei eNSP">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <StatsSection />
        <CTASection />
      </main>
    </Layout>
  );
}
