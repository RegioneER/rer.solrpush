import React from 'react';
import { object } from 'prop-types';

const SearchResultsContainer = ({ results }) => {
  if (results === undefined) {
    return '';
  }
  if (!results.items) {
    return '';
  }

  return (
    <div className="search-results-wrapper" style={{ flex: '70%' }}>
      <h2>Results: {results.items_total || 0}</h2>
      <div className="results">
        {results.items.map((res, i) => (
          <div
            key={i}
            className="result-wrapper"
            style={{
              backgroundColor: '#eee',
              padding: '5px 20px',
              margin: '10px 0',
            }}
          >
            <h4>{res.title}</h4>
            <div>
              <strong>Portal type: </strong>
              {res['@type']}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

SearchResultsContainer.propTypes = {
  results: object,
};

export default SearchResultsContainer;
