import { useState, useEffect } from 'react';

import VillageForm from '../components/VillageForm/VillageForm';
import ItineraryResults from '../components/ItineraryResults/ItineraryResults';
import { generateItinerary, getBootstrapStatus } from '../services/itineraryService';
import { toast } from 'react-toastify';

export default function Home() {

  const [state, setState] = useState('form'); // 'form' | 'results' 
  const [results, setResults] = useState(null);
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bootstrapReady, setBootstrapReady] = useState(false);
  const [bootstrapLoading, setBootstrapLoading] = useState(true);
  const [bootstrapMessage, setBootstrapMessage] = useState('Comprobando estado de inicialización...');

  const checkBootstrapStatus = async () => {
    try {
      const status = await getBootstrapStatus();
      setBootstrapReady(Boolean(status?.ready));
      setBootstrapMessage(status?.message || 'Esperando finalización del pipeline...');
      return Boolean(status?.ready);
    } catch {
      setBootstrapReady(false);
      setBootstrapMessage('No se pudo verificar el estado del pipeline. Reintentando...');
      return false;
    } finally {
      setBootstrapLoading(false);
    }
  };

  useEffect(() => {
    let pollTimer;
    let isMounted = true;

    const bootstrap = async () => {
      const isReady = await checkBootstrapStatus();
      if (isMounted && !isReady) {
        pollTimer = setInterval(async () => {
          const nowReady = await checkBootstrapStatus();
          if (nowReady && pollTimer) {
            clearInterval(pollTimer);
          }
        }, 10000);
      }
    };

    bootstrap();

    return () => {
      isMounted = false;
      if (pollTimer) clearInterval(pollTimer);
    };
  }, []);

  useEffect(() => {
    if (!bootstrapReady) return;

    const storedResults = localStorage.getItem('itineraryResults');
    const storedLocation = localStorage.getItem('location');
    const storedState = localStorage.getItem('viewState');

    if (storedResults && storedState === 'results') {
      setResults(JSON.parse(storedResults));
      setLocation(JSON.parse(storedLocation));
      setState('results');
    }
  }, [bootstrapReady]);

  // save results to localStorage
  useEffect(() => {
    if (!bootstrapReady) return;

    if (state === 'results') {
      localStorage.setItem('itineraryResults', JSON.stringify(results));
      localStorage.setItem('location', JSON.stringify(location));
      localStorage.setItem('viewState', 'results');
    } else {
      localStorage.removeItem('itineraryResults');
      localStorage.removeItem('location');
      localStorage.setItem('viewState', 'form');
    }
  }, [state, results, location, bootstrapReady]);
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
        {!bootstrapReady && (
          <section className="bg-white rounded-xl shadow-md p-6 md:p-8 fade-in max-w-2xl">
            <h1 className="text-2xl md:text-3xl font-bold text-indigo-800 mb-3">
              Inicializando datos del itinerario
            </h1>
            <p className="text-gray-600 mb-4">
              El formulario se habilitará cuando el job de Prefect termine de cargar los datos iniciales.
            </p>
            <p className="text-sm text-gray-500 mb-4">{bootstrapMessage}</p>
            {bootstrapLoading && (
              <p className="text-sm text-indigo-700">Comprobando estado...</p>
            )}
            <button
              type="button"
              onClick={checkBootstrapStatus}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
            >
              Reintentar ahora
            </button>
          </section>
        )}

        {bootstrapReady && state === 'form' && (
          <VillageForm
            onSubmit={handleSubmit}
            loading={loading}
          />
        )}

        {bootstrapReady && state === 'results' && (
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