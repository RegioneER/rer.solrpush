import React from 'react';
import { Line } from 'rc-progress';
import { number, string, bool } from 'prop-types';

const ProgressBar = ({ tot, counter, message, error }) => {
  if (error) {
    return <div className="status-message">{message || 'Generic Error.'}</div>;
  }
  const progress = tot === 0 ? 0 : Math.floor((counter * 100) / tot);
  return (
    <React.Fragment>
      {message ? <div>{message}</div> : ''}
      <div className="status-bar">
        <Line
          percent={progress}
          strokeWidth="2"
          strokeLinecap="butt"
          strokeColor={progress === 100 ? '#008000' : '#007bb1'}
        />
        {}
        {tot > 0 ? (
          <div>
            {counter}/{tot} ({progress}%)
          </div>
        ) : (
          ''
        )}
      </div>
    </React.Fragment>
  );
};

ProgressBar.propTypes = {
  tot: number,
  counter: number,
  message: string,
  error: bool,
};

export default ProgressBar;
