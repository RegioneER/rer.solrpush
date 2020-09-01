import React from 'react';
import ReactDOM from 'react-dom';
import ProgressBarContainer from './ProgressBarContainer';
import SearchDebugContainer from './SearchDebugContainer';

const maintenanceRootElement = document.getElementById('solr-maintenance');
const searchDebugRootElement = document.getElementById('search-debug');

if (maintenanceRootElement) {
  const authenticator = maintenanceRootElement.getAttribute(
    'data-authenticator',
  );
  const action = maintenanceRootElement.getAttribute('data-action');
  ReactDOM.render(
    <ProgressBarContainer authenticator={authenticator} action={action} />,
    maintenanceRootElement,
  );
} else if (searchDebugRootElement) {
  const authenticator = searchDebugRootElement.getAttribute(
    'data-authenticator',
  );
  ReactDOM.render(
    <SearchDebugContainer authenticator={authenticator} />,
    searchDebugRootElement,
  );
}
