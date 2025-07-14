import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Component to render a section of the itinerary results, with a toggle to expand or collapse the content.
 * The section includes a title, an icon, and a list of items.
 * The list of items is render as a list of children, and the component takes care of slicing the children to
 * the number of items to preview, and to render a button to show all the items if the number of items is greater
 * than the number of items to preview.
 *
 * @param {React.ReactNode | React.ReactNode[]} children - The children to render in the section.
 * @param {string} title - The title of the section.
 * @param {JSX.Element} icon - The icon to render in the title.
 * @param {string} bgFrom - The background color from, use in the gradient.
 * @param {string} bgTo - The background color to, use in the gradient.
 * @param {string} bgClass - The classes to add to the section container.
 * @param {number} maxPreview - The number of items to preview, default is 5.
 */

export default function AssetSection({ children, title, icon, bgFrom, bgTo,bgClass = '' , maxPreview = 5 }) {
  const [showAll, setShowAll] = useState(false);
  const items = Array.isArray(children) ? children : [children];

  return (
    <div className={`rounded-xl p-5 ${bgClass}`}>
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-800 flex items-center gap-2">
          {icon}
          {title}
        </h4>

        {items.length > maxPreview && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 text-sm font-medium transition-colors text-gray-700 hover:text-gray-900"
          >
            {showAll ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Mostrar menos
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Ver todos ({items.length})
              </>
            )}
          </button>
        )}
      </div>

      <ul className="space-y-2">
        {(showAll ? items : items.slice(0, maxPreview)).length > 0
          ? showAll
            ? items
            : items.slice(0, maxPreview)
          : (
            <p className="text-gray-500 italic">
              No hay elementos registrados
            </p>
          )}
      </ul>
    </div>
  );
}
