/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    'getting-started',
    {
      type: 'category',
      label: '功能模块',
      items: [
        'modules/data-download',
        'modules/feature-calculation',
        'modules/model-training',
        'modules/model-interpretation',
        'modules/model-analysis',
        'modules/backtest-construction',
      ],
    },
  ],
};

module.exports = sidebars;
