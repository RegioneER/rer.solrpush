import React from 'react';
import ReactDOM from 'react-dom';
import ProgressBarContainer from './ProgressBarContainer';

const rootElement = document.getElementById('solr-maintenance');

const authenticator = rootElement.getAttribute('data-authenticator');
const action = rootElement.getAttribute('data-action');

ReactDOM.render(
  <ProgressBarContainer authenticator={authenticator} action={action} />,
  rootElement,
);
