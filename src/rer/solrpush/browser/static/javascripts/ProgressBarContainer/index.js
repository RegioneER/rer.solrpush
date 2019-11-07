import React, { useState } from 'react';
import axios from 'axios';
import { Line } from 'rc-progress';
import { string } from 'prop-types';
import Spinner from 'react-svg-spinner';

const ProgressBarContainer = ({ authenticator }) => {
  const defaultData = {
    in_progress: true,
    tot: 0,
    counter: 0,
  };
  const [intervalId, setIntervalId] = useState();
  const [reindexStart, setReindexStart] = useState(false);
  const [data, setData] = useState(defaultData);

  const portalUrl = document.body
    ? document.body.getAttribute('data-portal-url') || ''
    : '';

  const doReindex = () => {
    setData(defaultData);
    setReindexStart(true);
    axios(`${portalUrl}/do-reindex`, {
      params: { _authenticator: authenticator },
    });
    const intervalId = setInterval(function() {
      axios(`${portalUrl}/reindex-progress`).then(result =>
        setData(result.data),
      );
    }, 5000);
    setIntervalId(intervalId);
  };

  if (reindexStart && !data.in_progress) {
    setReindexStart(false);
    clearInterval(intervalId);
  }
  const progress =
    data.tot === 0 ? 0 : Math.floor((data.counter * 100) / data.tot);
  return (
    <div className="progress-wrapper">
      <button onClick={doReindex} disabled={reindexStart}>
        START {reindexStart ? <Spinner /> : ''}
      </button>
      <div>
        <Line
          percent={progress}
          strokeWidth="2"
          strokeLinecap="butt"
          strokeColor={progress === 100 ? '#008000' : '#007bb1'}
        />
        {data.tot > 0 ? (
          <div>
            {data.counter}/{data.tot} ({progress}%)
          </div>
        ) : (
          ''
        )}
      </div>
    </div>
  );
};

ProgressBarContainer.propTypes = {
  authenticator: string,
};

export default ProgressBarContainer;
