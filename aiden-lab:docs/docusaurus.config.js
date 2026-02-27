// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'AIDEN Labs',
  tagline: 'ENSP Logger System - AI-Powered Network Error Detection',
  favicon: 'img/favicon.svg',

  future: {
    v4: true,
  },

  url: 'https://aiden-lab-docs.example.com',
  baseUrl: '/',

  organizationName: 'aiden-lab',
  projectName: 'aiden-lab-docs',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          editUrl: undefined,
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/social-card.svg',
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'AIDEN Labs',
        logo: {
          alt: 'AIDEN Labs Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentation',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'Getting Started',
                to: '/docs/intro',
              },
              {
                label: 'Architecture',
                to: '/docs/architecture',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} AIDEN Labs.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'json', 'yaml'],
      },
      announcementBar: {
        id: 'aiden_brand',
        content: 'AIDEN Labs - AI-Powered Network Error Detection',
        backgroundColor: 'rgba(36, 171, 148, 0.1)',
        textColor: '#24ab94',
        isCloseable: false,
      },
    }),
};

export default config;
