import { useEffect, useMemo, useRef, useState } from 'react';

const EMPTY_COLLECTION = { type: 'FeatureCollection', features: [] };
const types = ['building', 'road', 'parcel'];

function collection(payload) {
  if (payload?.type === 'FeatureCollection') return payload;
  if (Array.isArray(payload?.features)) return { type: 'FeatureCollection', features: payload.features };
  if (Array.isArray(payload)) return { type: 'FeatureCollection', features: payload };
  return EMPTY_COLLECTION;
}

function projectBounds(bounds) {
  if (!Array.isArray(bounds) || bounds.length !== 4) return null;
  const numbers = bounds.map(Number);
  return numbers.every(Number.isFinite) ? [[numbers[0], numbers[1]], [numbers[2], numbers[3]]] : null;
}

export default function ProjectMap({ project, featureData, layers }) {
  const node = useRef(null);
  const map = useRef(null);
  const [error, setError] = useState('');
  const featureCollection = useMemo(() => collection(featureData), [featureData]);
  const latitude = Number(project?.latitude);
  const longitude = Number(project?.longitude);
  const bounds = useMemo(() => projectBounds(project?.bounding_box ?? project?.bbox), [project?.bounding_box, project?.bbox]);
  const hasLocation = bounds || (Number.isFinite(latitude) && Number.isFinite(longitude));
  const currentData = useRef(featureCollection);
  const currentLayers = useRef(layers);
  currentData.current = featureCollection;
  currentLayers.current = layers;

  useEffect(() => {
    if (!node.current || !hasLocation || map.current) return undefined;
    let disposed = false;
    Promise.all([import('maplibre-gl'), import('maplibre-gl/dist/maplibre-gl.css')]).then(([{ default: maplibregl }]) => {
      if (disposed) return;
      const instance = new maplibregl.Map({
        container: node.current,
        style: import.meta.env.VITE_MAP_STYLE_URL || 'https://demotiles.maplibre.org/style.json',
        center: bounds ? [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2] : [longitude, latitude],
        zoom: bounds ? 12 : 15,
      });
      instance.addControl(new maplibregl.NavigationControl(), 'top-right');
      instance.on('load', () => {
        if (bounds) instance.fitBounds(bounds, { padding: 48, maxZoom: 17 });
        instance.addSource('project-features', { type: 'geojson', data: EMPTY_COLLECTION });
        instance.addLayer({ id: 'buildings', type: 'fill', source: 'project-features', filter: ['==', ['get', 'feature_type'], 'building'], paint: { 'fill-color': '#d35c3c', 'fill-opacity': 0.65, 'fill-outline-color': '#8f3323' } });
        instance.addLayer({ id: 'roads', type: 'line', source: 'project-features', filter: ['==', ['get', 'feature_type'], 'road'], paint: { 'line-color': '#2b6cb0', 'line-width': 4 } });
        instance.addLayer({ id: 'parcels', type: 'fill', source: 'project-features', filter: ['==', ['get', 'feature_type'], 'parcel'], paint: { 'fill-color': '#d69e2e', 'fill-opacity': 0.28, 'fill-outline-color': '#9c6b12' } });
        instance.getSource('project-features').setData(currentData.current);
        types.forEach(type => instance.setLayoutProperty(`${type}s`, 'visibility', currentLayers.current[type] ? 'visible' : 'none'));
      });
      instance.on('error', () => setError('The map base layer could not be loaded. Check the map provider configuration.'));
      map.current = instance;
    }).catch(() => setError('The map viewer could not be loaded.'));
    return () => { disposed = true; map.current?.remove(); map.current = null; };
  }, [hasLocation, latitude, longitude, bounds]);

  useEffect(() => {
    const instance = map.current;
    if (!instance?.isStyleLoaded()) return;
    instance.getSource('project-features')?.setData(featureCollection);
    types.forEach(type => instance.setLayoutProperty(`${type}s`, 'visibility', layers[type] ? 'visible' : 'none'));
  }, [featureCollection, layers]);

  if (!hasLocation) return <div className="map-empty" role="status"><h3>No project location yet</h3><p>Add a saved project location to view its mapped features.</p></div>;
  return <div className="map-wrap"><div className="maplibre-map" ref={node} aria-label="Project GIS map" />{error && <p className="map-error" role="alert">{error}</p>}{featureCollection.features.length === 0 && <p className="map-empty-overlay">No GIS features are available for this project.</p>}</div>;
}
