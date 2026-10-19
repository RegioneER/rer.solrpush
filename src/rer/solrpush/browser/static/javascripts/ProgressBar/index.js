import React from 'react';
import { Line } from 'rc-progress';
import { number, string, bool, array } from 'prop-types';

const ProgressBar = ({
  tot,
  counter,
  message,
  error,
  indexed,
  failed,
  skipped,
  unindexed,
  commit_error,
  errors,
}) => {
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
      {indexed !== undefined ? (
        <div className="status-summary">
          <div>Submitted: {indexed}</div>
          <div>Failed: {failed}</div>
          <div>Skipped: {skipped}</div>
          <div>Removed: {unindexed}</div>
          {commit_error ? <div>Final commit failed: {commit_error}</div> : ''}
          {errors && errors.length ? (
            <details>
              <summary>Failed items ({errors.length})</summary>
              <ul>
                {errors.map((error) => (
                  <li key={`${error.UID}-${error.phase}`}>
                    {error.UID} - {error.path} ({error.phase}): {error.message}
                  </li>
                ))}
              </ul>
            </details>
          ) : (
            ''
          )}
        </div>
      ) : (
        ''
      )}
    </React.Fragment>
  );
};

ProgressBar.propTypes = {
  tot: number,
  counter: number,
  message: string,
  error: bool,
  indexed: number,
  failed: number,
  skipped: number,
  unindexed: number,
  commit_error: string,
  errors: array,
};

export default ProgressBar;
