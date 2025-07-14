import { useState, useEffect } from 'react';

import VillageForm from '../components/VillageForm/VillageForm';
import ItineraryResults from '../components/ItineraryResults/ItineraryResults';
import { generateItinerary } from '../services/itineraryService';
import { toast } from 'react-toastify';

export default function Home() {

  const [state, setState] = useState('form'); // 'form' | 'results' 
  const [results, setResults] = useState(null);
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);

  // load results from localStorage
  useEffect(() => {
    const storedResults = localStorage.getItem('itineraryResults');
    const storedLocation = localStorage.getItem('location');
    const storedState = localStorage.getItem('viewState');

    if (storedResults && storedState === 'results') {
      setResults(JSON.parse(storedResults));
      setLocation(JSON.parse(storedLocation));
      setState('results');
    }
  }, []);

  // save results to localStorage
  useEffect(() => {
    if (state === 'results') {
      localStorage.setItem('itineraryResults', JSON.stringify(results));
      localStorage.setItem('location', JSON.stringify(location));
      localStorage.setItem('viewState', 'results');
    } else {
      localStorage.removeItem('itineraryResults');
      localStorage.removeItem('location');
      localStorage.setItem('viewState', 'form');
    }
  }, [state, results, location]);
  /**
   * Handles form submission, calls generateItinerary service, and updates local state accordingly.
   * If an error occurs, displays an error toast and resets the state to 'form'.
   * @param {Object} formData - Form data object containing trip preferences and optional location.
   */
  const handleSubmit = async (formData) => {
    setLoading(true);
    setLocation(formData.location);
    try {
      const itineraryData = await generateItinerary(formData);
      setResults(itineraryData);
      setLoading(false);
      setState('results');
    } catch (err) {
      toast.error(err.message || 'Ha ocurrido un error inesperado.');
      setLoading(false);
      setState('form');
    }
  };

  /**
   * Resets the state to 'form', clears local results and location state, and removes
   * all items from localStorage.
   */
  const handleReset = () => {
    setState('form');
    setResults(null);
    setLocation(null);
    localStorage.clear();
  };


  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-10" >
      <div className="">
        {state === 'form' && (
          <VillageForm
            onSubmit={handleSubmit}
            loading={loading}
          />
        )}

        {state === 'results' && (
          <ItineraryResults
            results={results}
            location={location}
            onReset={handleReset}
          />
        )}

      </div>
    </div>
  );

}