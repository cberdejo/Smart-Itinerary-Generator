import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { toast } from 'react-toastify';
import { useState } from 'react';
import { Loader2, Download } from 'lucide-react';
import polyline from '@mapbox/polyline';
import leafletImage from 'leaflet-image';


/**
 * Component responsible for generating a PDF report from itinerary results.
 *
 * This component processes the itinerary data and map reference to create
 * a visually appealing PDF document. It includes town descriptions,
 * history, real estate and intangible assets, and images. The PDF is
 * created using jsPDF and html2canvas, featuring justified text and
 * dynamic map snapshots.
 *
 * @param {Object} results - Itinerary results object containing trip and town information.
 * @param {Object} mapRef - React ref pointing to the map element for capturing map images.
 */

export default function GenerateReport({ results, mapRef }) {
    const [isGenerating, setIsGenerating] = useState(false);

    async function captureMap(map) {
        return await new Promise((resolve, reject) =>
            leafletImage(map, (err, canvas) => (err ? reject(err) : resolve(canvas)))
        );
    }

    const cleanText = (text) => text.replace(/\s*\n\s*/g, ' ').replace(/\s{2,}/g, ' ').trim();

    /**
     * Generates a PDF report based on the given itinerary results.
     *
     * @param {Object} results - Itinerary results object
     * @param {Object} mapRef - Reference to the map container
     */
    const generatePDF = async () => {
        if (!mapRef.current) return;

        setIsGenerating(true);
        const map = mapRef.current;

        try {
            const routeLatLngs = [];
            results.trip.legs.forEach(leg => {
                if (leg.shape) {
                    const latlngs = polyline.decode(leg.shape, 6).map(([lat, lon]) => [lat, lon]);
                    routeLatLngs.push(...latlngs);
                }
            });

            const originalCenter = map.getCenter();
            const originalZoom = map.getZoom();

            if (routeLatLngs.length > 0) {
                const routeBounds = L.latLngBounds(routeLatLngs);
                map.fitBounds(routeBounds, { padding: [20, 20] });

                await new Promise(resolve => {
                    let moveEnd = false;
                    let zoomEnd = false;

                    const check = () => moveEnd && zoomEnd && resolve();

                    const moveHandler = () => {
                        moveEnd = true;
                        map.off('moveend', moveHandler);
                        check();
                    };

                    const zoomHandler = () => {
                        zoomEnd = true;
                        map.off('zoomend', zoomHandler);
                        check();
                    };

                    map.on('moveend', moveHandler);
                    map.on('zoomend', zoomHandler);

                    setTimeout(() => {
                        map.off('moveend', moveHandler);
                        map.off('zoomend', zoomHandler);
                        resolve();
                    }, 2000);
                });
            }
            const polylineLayer = L.polyline(routeLatLngs, {
                color: '#2563eb',
                weight: 4,
                opacity: 0.8,
                renderer: L.canvas() 
            }).addTo(map);


            await new Promise(resolve => setTimeout(resolve, 300));

            const canvas = await new Promise((resolve, reject) =>
                leafletImage(map, (err, c) => err ? reject(err) : resolve(c))
            );

            map.removeLayer(polylineLayer);
            map.setView(originalCenter, originalZoom);

            // Create pdf
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();

            pdf.setFontSize(20);
            pdf.text('Itinerario', pageWidth / 2, 20, { align: 'center' });
            pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 10, 30, pageWidth - 20, 100);

            let y = 140;
            const addSpace = (amount) => {
                if (y + amount > pageHeight - 20) {
                    pdf.addPage();
                    y = 20;
                }
            };

            const cleanText = (text) => text.replace(/\s*\n\s*/g, ' ').replace(/\s{2,}/g, ' ').trim();

            for (const town of results.towns) {
                addSpace(12);
                pdf.setFontSize(16);
                pdf.text(town.municipality_name, 10, y);
                y += 10;

                if (town.description) {
                    const lines = pdf.splitTextToSize(cleanText(town.description), pageWidth - 20);
                    addSpace(lines.length * 5);
                    pdf.setFontSize(10);
                    lines.forEach(line => {
                        pdf.text(line, 10, y);
                        y += 5;
                    });
                    y += 3;
                }

                if (town.history) {
                    const lines = pdf.splitTextToSize(cleanText(town.history), pageWidth - 20);
                    addSpace(lines.length * 5 + 6);
                    pdf.setFontSize(12);
                    pdf.text('Historia:', 10, y);
                    y += 6;
                    pdf.setFontSize(10);
                    lines.forEach(line => {
                        pdf.text(line, 10, y);
                        y += 5;
                    });
                    y += 3;
                }

                if (town.real_estate_assets?.length) {
                    pdf.setFontSize(12);
                    addSpace(6);
                    pdf.text('Monumentos y Patrimonio:', 10, y);
                    y += 6;
                    pdf.setFontSize(10);
                    for (const asset of town.real_estate_assets) {
                        const text = `• ${asset.name} (${asset.typologies?.map(t => t.den_tipologia).join(', ') || ''})`;
                        const lines = pdf.splitTextToSize(text, pageWidth - 20);
                        addSpace(lines.length * 4);
                        pdf.text(lines, 15, y);
                        y += lines.length * 4;
                    }
                    y += 5;
                }

                if (town.intangible_assets?.length) {
                    pdf.setFontSize(12);
                    addSpace(6);
                    pdf.text('Festividades y Tradiciones:', 10, y);
                    y += 6;
                    pdf.setFontSize(10);
                    for (const asset of town.intangible_assets) {
                        const text = `• ${asset.name} (${asset.typology || ''})`;
                        const lines = pdf.splitTextToSize(text, pageWidth - 20);
                        addSpace(lines.length * 4);
                        pdf.text(lines, 15, y);
                        y += lines.length * 4;
                    }
                    y += 5;
                }

                if (Array.isArray(town.images) && town.images.length > 0) {
                    pdf.setFontSize(12);
                    addSpace(6);
                    pdf.text('Imágenes:', 10, y);
                    y += 6;

                    const imgWidth = (pageWidth - 40) / 3;
                    const imgHeight = 40;
                    const padding = 5;

                    for (let i = 0; i < town.images.length; i++) {
                        const imageData = town.images[i];
                        if (!imageData.url) continue;

                        const image = new Image();
                        image.crossOrigin = 'anonymous';
                        image.src = imageData.url;

                        try {
                            await new Promise((res, rej) => {
                                image.onload = () => res();
                                image.onerror = () => rej();
                            });

                            const col = i % 3;
                            const x = 10 + col * (imgWidth + 10);

                            if (col === 0) {
                                addSpace(imgHeight + padding);
                                y += padding;
                            }

                            pdf.addImage(image, 'JPEG', x, y, imgWidth, imgHeight);

                            if (col === 2 || i === town.images.length - 1) {
                                y += imgHeight;
                            }

                        } catch (e) {
                            console.warn(`No se pudo cargar la imagen para ${town.municipality_name}`);
                        }
                    }
                    y += 5;
                }

                y += 5;
                addSpace(5);
                pdf.setDrawColor(200);
                pdf.line(10, y, pageWidth - 10, y);
                y += 10;
            }

            pdf.save('itinerary-report.pdf');
            toast.success('PDF generado correctamente');

        } catch (err) {
            toast.error('Error al generar el PDF');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div>
            <button
                className='flex items-center gap-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5'
                onClick={generatePDF}
                disabled={isGenerating}
            >
                {isGenerating ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Cargando...
                    </>
                ) : (
                    <>
                        <Download className="w-4 h-4" />
                        Descargar
                    </>
                )}
            </button>
        </div>
    )
}