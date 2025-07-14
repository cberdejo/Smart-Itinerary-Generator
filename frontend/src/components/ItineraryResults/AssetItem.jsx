import { useState } from 'react';
import { Info } from 'lucide-react';

/**
 * A component that renders an asset item with a title, optional subtitle, and detailed information.
 * The component displays a colored dot and an info icon. Clicking the button toggles the visibility
 * of the detailed information.
 *
 * @param {Object} props - The properties object.
 * @param {string} props.title - The main title of the asset item.
 * @param {string} [props.subtitle] - An optional subtitle for additional context.
 * @param {ReactNode} props.details - Additional details displayed when the item is expanded.
 * @param {string} [props.dotColor='blue'] - The color of the dot and info icon, default is 'blue'.
 */

export default function AssetItem({ title, subtitle, details, dotColor = 'blue' }) {
  const [open, setOpen] = useState(false);

  return (
    <li className="flex flex-col gap-2">
      <button
        className="flex items-start gap-2 group text-left"
        onClick={() => setOpen(!open)}
      >
        <div
          className={`w-2 h-2 rounded-full mt-2 shrink-0 bg-${dotColor}-500`}
        />
        <span className="font-medium text-gray-800">{title}</span>
        {subtitle && (
          <span className="text-sm text-gray-600 ml-2">{subtitle}</span>
        )}
        <Info
          className={`w-4 h-4 text-${dotColor}-600 opacity-80 group-hover:opacity-100 transition-opacity ml-1 mt-0.5 shrink-0`}
          aria-label="Mostrar información"
        />
      </button>

      {open && (
        <div className="ml-4 pl-4 border-l-2 border-dashed text-sm text-gray-700 space-y-1 border-current/40">
          {details}
        </div>
      )}
    </li>
  );
}
