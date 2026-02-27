import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';

import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--dark', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get Started
          </Link>
          <Link
            className="button button--primary button--lg"
            to="/docs/architecture"
            style={{marginLeft: '1rem'}}>
            Architecture
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="AIDEN Labs - ENSP Logger System"
      description="AI-Powered Network Error Detection for Huawei eNSP">
      <HomepageHeader />
      <main>
        <div className="container" style={{padding: '3rem 0'}}>
          <div className="row">
            <div className="col col--4">
              <div className="text--center">
                <Heading as="h3">Real-Time Monitoring</Heading>
                <p>Event-driven file watching with millisecond response time</p>
              </div>
            </div>
            <div className="col col--4">
              <div className="text--center">
                <Heading as="h3">AI-Powered Analysis</Heading>
                <p>Self-hosted LLM for root cause analysis and solutions</p>
              </div>
            </div>
            <div className="col col--4">
              <div className="text--center">
                <Heading as="h3">Pattern Detection</Heading>
                <p>Automatically detects critical errors and warnings</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}
