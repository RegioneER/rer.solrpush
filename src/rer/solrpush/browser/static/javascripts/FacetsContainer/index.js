import React from 'react';
import { object } from 'prop-types';

const FacetsContainer = ({ facets }) => {
  if (!facets) {
    return '';
  }
  return (
    <div
      className="facets-container"
      style={{ flex: '30%', marginRight: '1em' }}
    >
      <h3>Facets</h3>
      {Object.keys(facets).map((id, i) => {
        const facet_values = facets[id];
        return (
          <div
            key={i}
            className="facet"
            style={{
              backgroundColor: '#eee',
              padding: '5px 20px',
              margin: '10px 0',
            }}
          >
            <strong>{id}</strong>
            {facet_values.map((val, idx) => {
              const key = Object.keys(val)[0];
              return (
                <div key={`${id}-${idx}`}>
                  {key} [{val[key]}]
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

FacetsContainer.propTypes = {
  facets: object,
};

export default FacetsContainer;
