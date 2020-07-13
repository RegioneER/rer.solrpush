import React, { useState } from 'react';
import axios from 'axios';
import { string } from 'prop-types';
import SearchParametersContainer from '../SearchParametersContainer';
import SearchResultsContainer from '../SearchResultsContainer';
import FacetsContainer from '../FacetsContainer';

const SearchDebugContainer = ({ authenticator }) => {
  const [params, setParams] = useState({
    SearchableText: '',
    facets: false,
    // sort_on: '',
  });
  const [results, setResults] = useState({});
  // const [searching, setSearching] = useState(false);

  const portalUrl = document.body
    ? document.body.getAttribute('data-portal-url') || ''
    : '';

  const doSearch = parameters => {
    console.log('in doSearch: ', parameters);
    axios(`${portalUrl}/@solr-search`, {
      headers: {
        'content-type': 'application/json',
        Accept: 'application/json',
      },
      params: { _authenticator: authenticator, ...parameters },
    }).then(res => {
      setResults(res.data);
    });
  };

  const updateParameter = parameter => {
    const newParameters = { ...params, ...parameter };
    setParams(newParameters);
    doSearch(newParameters);
  };

  console.log(params);
  console.log(results);
  return (
    <div className="search-wrapper">
      <SearchParametersContainer
        params={params}
        onUpdateParams={updateParameter}
      />
      <div className="results" style={{ display: 'flex' }}>
        <FacetsContainer facets={results.facets} />
        <SearchResultsContainer results={results} />
      </div>
    </div>
  );
};

SearchDebugContainer.propTypes = {
  authenticator: string,
};

export default SearchDebugContainer;
