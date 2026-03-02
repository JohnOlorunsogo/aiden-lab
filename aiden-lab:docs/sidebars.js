// @ts-check

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.

 @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      collapsible: true,
      items: [
        {
          type: 'doc',
          id: 'intro',
          label: 'Overview',
        },
      ],
    },
    {
      type: 'category',
      label: 'Processing Pipeline',
      collapsible: true,
      items: [
        {
          type: 'doc',
          id: 'capturing-traffic',
          label: 'Step 1',
        },
        {
          type: 'doc',
          id: 'log-files',
          label: 'Step 2',
        },
        {
          type: 'doc',
          id: 'file-watcher',
          label: 'Step 3',
        },
        {
          type: 'doc',
          id: 'error-detection',
          label: 'Step 4',
        },
        {
          type: 'doc',
          id: 'ai-analysis',
          label: 'Step 5',
        },
        {
          type: 'doc',
          id: 'database',
          label: 'Step 6',
        },
        {
          type: 'doc',
          id: 'dashboard',
          label: 'Step 7',
        },
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      collapsible: true,
      items: [
        {
          type: 'doc',
          id: 'architecture',
          label: 'System Architecture',
        },
        {
          type: 'doc',
          id: 'tools-and-dependencies',
          label: 'Tools and Dependencies',
        },
      ],
    },
    {
      type: 'category',
      label: 'Operations',
      collapsible: true,
      items: [
        {
          type: 'doc',
          id: 'startup',
          label: 'Startup Sequence',
        },
      ],
    },
  ],
};

export default sidebars;
