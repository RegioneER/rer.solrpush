import React from 'react';
import { DebounceInput } from 'react-debounce-input';
import { object, func } from 'prop-types';

const SearchParametersContainer = ({ params, onUpdateParams }) => {
  return (
    <div className="filters">
      <div className="SearchableText">
        <DebounceInput
          minLength={2}
          debounceTimeout={300}
          onChange={event =>
            onUpdateParams({ SearchableText: event.target.value })
          }
        />
        <label>
          Faccette
          <input
            name="facets"
            type="checkbox"
            checked={params.facets}
            onChange={event => {
              onUpdateParams({ facets: event.target.checked });
            }}
          />
        </label>
      </div>
    </div>
  );
};

SearchParametersContainer.propTypes = {
  params: object,
  onUpdateParams: func,
};

export default SearchParametersContainer;
