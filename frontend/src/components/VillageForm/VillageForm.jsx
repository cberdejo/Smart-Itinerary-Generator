import React, { useState, useRef, useEffect } from 'react';
import { Home, Landmark, Utensils, MapPin } from "lucide-react";
import LocationPicker from './LocationPicker';

/**
 * VillageForm component renders a form for users to specify their preferences for generating a travel itinerary.
 * It includes input fields for village type, environment, cultural and historical interests, travel interests,
 * and location. The component also includes a location picker and a travel time selector.
 *
 * Props:
 * @param {Function} onSubmit - Callback function to handle form submission.
 * @param {Boolean} loading - Indicates if the form is in a loading state.
 *
 * State:
 * @param {Object} form - Stores form data including village type, environment, monuments, historical periods,
 * cultural influences, travel interests, traditions, beach preference, location, and travel time limit.
 *
 * Methods:
 * - handleChange: Updates form state based on input field changes.
 * - handleRadio: Updates the beach preference in the form state.
 * - handleSubmit: Prevents default form submission, checks loading state, and calls the onSubmit callback with form data.
 *
 * Effects:
 * - Adjusts textarea height automatically based on content.
 *
 * UI Components:
 * - LocationPicker: Allows users to select a geographic location.
 * - Textarea: Custom textarea component for form inputs.
 */

export default function VillageForm({ onSubmit, loading }) {
  // ---------- form state ----------
  const [form, setForm] = useState({
    villageType: '',
    environment: '',
    monuments: '',
    historicalPeriods: '',
    culturalInfluences: '',
    travelInterests: '',
    traditions: '',
    beach: 'indiference',
    location: null, // {lat, lng, label}
    travelTimeLimit: 60,
  });

  // ---------- helpers ----------
  const isFormEmpty = (obj) => {
    return Object.entries(obj).every(([key, val]) => {
      if (key === 'location' || key === 'beach') return true;
      return !val;
    });
  };
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRadio = (e) => {
    setForm((prev) => ({ ...prev, beach: e.target.value }));
  };

  const [mapOpen, setMapOpen] = useState(false);

  // ---------- autogrow  textareas ----------
  const autosizeRefs = useRef([]);

  useEffect(() => {
    autosizeRefs.current.forEach((el) => {
      if (el) {
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
      }
    });
  }, [form]);

  // ---------- send ----------
  const handleSubmit = (e) => {
    e.preventDefault();
    if (loading) return;
    onSubmit(form);
  };

  // ---------- render ----------
  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow-md p-6 md:p-8 fade-in"
    >
      {/* Header */}
      <header className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-indigo-800 mb-2">
          Generador de Itinerarios Inteligente
        </h1>
        <p className="text-gray-600">
          ¿Eres de Andalucía? ¿Vienes de vísita pronto? No te preocupes, completa este formulario para descubrir
          lugares que te encantarán.
        </p>

      </header>

      {/* ---------- Town type ---------- */}
      <Section icon={Home} title="Tipo de Pueblo">
        <Textarea
          label="¿Qué tipo de pueblo deseas ver?"
          name="villageType"
          placeholder="Ejemplo: rural, tranquilo, con arquitectura tradicional andaluza"
          value={form.villageType}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[0] = el)}
          disabled={loading}
        />

        <Textarea
          label="¿Qué tipo de ambiente buscas?"
          name="environment"
          placeholder="Ejemplo: rural, tranquilo, con arquitectura tradicional andaluza"
          value={form.environment}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[1] = el)}
          disabled={loading}
        />
      </Section>

      <Divider />

      {/* ---------- Culture ---------- */}
      <Section icon={Landmark} title="Interés Cultural e Histórico">
        <Textarea
          label="¿Qué tipo de monumentos te interesan?"
          name="monuments"
          placeholder="Ejemplo: castillos medievales, iglesias románicas, etc."
          value={form.monuments}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[2] = el)}
          disabled={loading}
        />

        <Textarea
          label="¿Qué épocas históricas te interesan?"
          name="historicalPeriods"
          placeholder="Ejemplo: Edad Media, época romana, etc."
          value={form.historicalPeriods}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[3] = el)}
          disabled={loading}
        />

        <Textarea
          label="¿Te interesan pueblos con cultura indígena, morisca, romana…?"
          name="culturalInfluences"
          placeholder="Ejemplo: cultura morisca, influencia romana, etc."
          value={form.culturalInfluences}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[4] = el)}
          disabled={loading}
        />
      </Section>

      <Divider />

      {/* ---------- Traditions ---------- */}
      <Section icon={Utensils} title="Experiencias y Tradiciones">
        <Textarea
          label="¿Qué te interesa más en un viaje?"
          name="travelInterests"
          placeholder="Ejemplo: aprender sobre historia, probar comida típica, conocer fiestas"
          value={form.travelInterests}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[5] = el)}
          disabled={loading}
        />

        <Textarea
          label="¿Qué tipo de tradiciones o festividades te gustaría experimentar en tu próximo destino?"
          name="traditions"
          placeholder="Ejemplo: ferias medievales, fiestas patronales, etc."
          value={form.traditions}
          onChange={handleChange}
          ref={(el) => (autosizeRefs.current[6] = el)}
          disabled={loading}
        />
      </Section>

      <Divider />

      {/* ---------- Nature & Location ---------- */}
      <Section icon={MapPin} title="Naturaleza y Ubicación">
        {/* playa */}
        <div className="mb-6">
          <label className="block text-gray-700 mb-2">¿Buscas playa?</label>
          <div className="flex space-x-4">
            <label className="inline-flex items-center">
              <input
                type="radio"
                name="beach"
                value="yes"
                onChange={handleRadio}
                checked={form.beach === 'yes'}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                disabled={loading}
              />
              <span className="ml-2 text-gray-700">Sí</span>
            </label>
            <label className="inline-flex items-center">
              <input
                type="radio"
                name="beach"
                value="no"
                onChange={handleRadio}
                checked={form.beach === 'no'}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500"
                disabled={loading}
              />
              <span className="ml-2 text-gray-700">No</span>

            </label>

            <label className="inline-flex items-center">
              <input
                type="radio"
                name="beach"
                value="indiferente"
                onChange={handleRadio}
                checked={form.beach === 'indiferente'}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                disabled={loading}
              />
              <span className="ml-2 text-gray-700">Indiferente</span>
            </label>
          </div>
        </div>

        {/* Location */}

        <div className="mb-4">
          <label className="block text-gray-700 mb-2">
            ¿Quieres que nuestras recomendaciones estén cerca de alguna ubicación?
          </label>
          <button
            type="button"
            onClick={() => mapOpen ? setMapOpen(false) : setMapOpen(true)}
            disabled={loading}
            className={`bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 mb-2 rounded-lg ${loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-indigo-200'
              }`}
          >
            <i className="fas fa-map-marker-alt mr-2" />
            {mapOpen ? 'Cerrar Mapa' : 'Seleccionar ubicación en el mapa'}
          </button>

          {/* Location picker */}
          {mapOpen && (
            <LocationPicker
              defaultPos={[37.3074, -4.5780]}           // Andalusia center
              onConfirm={(loc) => {

                setForm((prev) => ({ ...prev, location: loc }));
                setMapOpen(false);   // close model

              }}
            />
          )}

          {form.location && !mapOpen && (
            <div className="mt-2 text-sm text-gray-500">
              <i className="fas fa-check-circle text-green-500 mr-1" />
              Ubicación seleccionada: {form.location.label}
              <button 
                type="button"
                onClick={() => {
                  setForm((prev) => ({ ...prev, location: null }));
                }}
                className=" ml-2 bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 mb-2 rounded-lg"
              >
                Eliminar ubicación
              </button>

               {/* Travel Time Selector */}
            <div className="mt-4">
              <label htmlFor="travelTimeLimit" className="block text-gray-700 mb-2">
                ¿Hasta cuánto tiempo estás dispuesto/a a conducir desde el punto seleccionado?
              </label>
              <select
                id="travelTimeLimit"
                name="travelTimeLimit"
                value={form.travelTimeLimit}
                onChange={handleChange}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value={30}>30 minutos</option>
                <option value={60}>1 hora</option>
                <option value={90}>1 hora y 30 minutos</option>
                <option value={120}>2 horas</option>
              </select>
            </div>
            </div>

           

          )}

     
        </div>
      </Section>

      {/* ---------- Submit ---------- */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading || isFormEmpty(form)}
          className={`bg-indigo-600 text-white px-6 py-2 rounded-lg transition flex items-center justify-center ${loading || isFormEmpty(form) ? 'opacity-20 cursor-not-allowed' : 'hover:bg-indigo-700'
            }`}
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-5 w-5 mr-2 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
              Cargando...
            </>
          ) : (
            <>
              <i className="fas fa-search mr-2" />
              Buscar pueblos
            </>
          )}
        </button>
      </div>
    </form>
  );
}

// ---------- reusables sub-componentes ----------


function Section({ icon: Icon, title, children }) {
  return (
    <section className="mb-8 fade-in">
      <div className="flex items-center mb-4">
        <div className="bg-indigo-100 p-2 rounded-full mr-3">
          <Icon className="w-5 h-5 text-indigo-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
      </div>
      {children}
    </section>
  );
}


function Divider() {
  return <div className="border-t-2 border-dashed border-gray-200 my-8" />;
}

const Textarea = React.forwardRef(
  ({ label, name, placeholder, value, onChange, disabled }, ref) => (
    <div className="mb-4">
      <label htmlFor={name} className="block text-gray-700 mb-2">
        {label}
      </label>
      <textarea
        id={name}
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        ref={ref}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 textarea-autosize resize-none overflow-hidden"
      />
    </div>
  )
);
