import React, { useState } from 'react';
import axios from 'axios';
import { string } from 'prop-types';
import Spinner from 'react-svg-spinner';
import ProgressBar from '../ProgressBar';

const ProgressBarContainer = ({ authenticator, action }) => {
  const defaultData = {
    in_progress: true,
    tot: 0,
    counter: 0,
    message: '',
    error: false,
  };
  const [intervalId, setIntervalId] = useState();
  const [reindexStart, setReindexStart] = useState(false);
  const [data, setData] = useState(defaultData);

  const portalUrl = document.body
    ? document.body.getAttribute('data-portal-url') || ''
    : '';

  const doCancel = () => {
    window.location.href = `${portalUrl}/@@solrpush-settings`;
  };

  const doReindex = () => {
    setData(defaultData);
    setReindexStart(true);
    axios(`${portalUrl}/${action}`, {
      params: { _authenticator: authenticator },
    });
    const intervalId = setInterval(function () {
      axios(`${portalUrl}/reindex-progress`).then((result) =>
        setData(result.data),
      );
    }, 5000);
    setIntervalId(intervalId);
  };

  const { in_progress } = data;
  if (reindexStart && !in_progress) {
    setReindexStart(false);
    clearInterval(intervalId);
  }
  return (
    <div className="maintenance-wrapper">
      <div className="formControls">
        <button onClick={doReindex} disabled={reindexStart}>
          Start {reindexStart ? <Spinner /> : ''}
        </button>{' '}
        <button onClick={doCancel} disabled={reindexStart}>
          Cancel
        </button>
      </div>
      <ProgressBar {...data} />
    </div>
  );
};

ProgressBarContainer.propTypes = {
  authenticator: string,
  action: string,
};

export default ProgressBarContainer;
