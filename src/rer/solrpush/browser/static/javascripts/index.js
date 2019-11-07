import React from 'react';
import ReactDOM from 'react-dom';
import ProgressBarContainer from './ProgressBarContainer';

const rootElement = document.getElementById('reindex-solr');

const authenticator = rootElement.getAttribute('data-authenticator');

ReactDOM.render(
  <ProgressBarContainer authenticator={authenticator} />,
  rootElement,
);
