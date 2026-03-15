const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Generates an itinerary based on form data.
 *
 * @param {Object} formData Form data
 * @returns {Promise<Object>} Itinerary data
 * @throws {Error} If there's an error generating the itinerary
 */
export const generateItinerary = async (formData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/itinerary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    const result = await response.json(); 

    if (!response.ok || result.code !== 200) {
      const message = result.message || 'Error generando el itinerario';
      throw new Error(message);
    }

    return result.data; 
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

/**
 * Fetch bootstrap readiness for initial pipeline data.
 *
 * @returns {Promise<{ready: boolean, message: string, counts?: {towns: number, embedded_towns: number}}>}
 */
export const getBootstrapStatus = async () => {
  const response = await fetch(`${API_BASE_URL}/bootstrap-status`);
  const result = await response.json();

  if (!response.ok) {
    throw new Error(result?.message || 'No se pudo comprobar el estado de inicialización');
  }

  return result;
};
