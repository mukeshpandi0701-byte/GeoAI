const MAP_WIDTH = 720;
const MAP_HEIGHT = 430;
const MAP_PADDING = 38;

function positions(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Point') return [geometry.coordinates];
  if (geometry.type === 'LineString') return geometry.coordinates;
  if (geometry.type === 'MultiLineString' || geometry.type === 'Polygon') return geometry.coordinates.flat();
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flat(2);
  return [];
}

function projection(features) {
  const coordinates = features.flatMap(feature => positions(feature.geometry));
  if (!coordinates.length) return () => [MAP_WIDTH / 2, MAP_HEIGHT / 2];
  const longitudes = coordinates.map(([longitude]) => longitude);
  const latitudes = coordinates.map(([, latitude]) => latitude);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const longitudeRange = Math.max(maxLongitude - minLongitude, 0.0001);
  const latitudeRange = Math.max(maxLatitude - minLatitude, 0.0001);
  return ([longitude, latitude]) => [
    MAP_PADDING + ((longitude - minLongitude) / longitudeRange) * (MAP_WIDTH - MAP_PADDING * 2),
    MAP_HEIGHT - MAP_PADDING - ((latitude - minLatitude) / latitudeRange) * (MAP_HEIGHT - MAP_PADDING * 2),
  ];
}

function linePath(coordinates, point) {
  return coordinates.map((coordinate, index) => {
    const [x, y] = point(coordinate);
    return `${index ? 'L' : 'M'}${x} ${y}`;
  }).join(' ');
}

function polygonPath(rings, point) {
  return rings.map(ring => `${linePath(ring, point)} Z`).join(' ');
}

function geometryPath(geometry, point) {
  if (geometry.type === 'LineString') return linePath(geometry.coordinates, point);
  if (geometry.type === 'MultiLineString') return geometry.coordinates.map(line => linePath(line, point)).join(' ');
  if (geometry.type === 'Polygon') return polygonPath(geometry.coordinates, point);
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.map(polygon => polygonPath(polygon, point)).join(' ');
  return null;
}

export default function MapCanvas({ layers, features = [], loading = false, error = '', projectName, onFeatureSelect }) {
  const point = projection(features);
  const visibleFeatures = features.filter(feature => layers[`${feature.properties?.feature_type}s`]);
  return <div className="map" role="img" aria-label="Map of persisted AI-mapped physical features">
    <div className="map-toolbar"><button aria-label="Zoom in">+</button><button aria-label="Zoom out">−</button><button aria-label="Center map">⌾</button></div>
    <div className="north"><b>N</b><span>↑</span></div><div className="scale"><i />50 m</div>
    <svg viewBox="0 0 720 430" preserveAspectRatio="none">
      {layers.imagery && <><rect width="720" height="430" className="terrain" /><path className="contour" d="M-20 85 Q155 30 315 90T740 62M-15 292 Q110 242 280 303T735 263M82 -10Q128 98 50 212T73 440M640 -15Q581 112 651 212T618 450" /></>}
      {visibleFeatures.map(feature => {
        const featureType = feature.properties?.feature_type;
        const path = geometryPath(feature.geometry, point);
        const selectFeature = () => onFeatureSelect?.(feature);
        if (feature.geometry?.type === 'Point') {
          const [cx, cy] = point(feature.geometry.coordinates);
          return <circle key={feature.id} className={`gis-feature gis-${featureType} gis-${feature.review_status}`} cx={cx} cy={cy} r="7" role="button" tabIndex="0" aria-label={`Select ${featureType} ${feature.id}`} onClick={selectFeature} onKeyDown={event => event.key === 'Enter' && selectFeature()} />;
        }
        return path && <path key={feature.id} d={path} className={`gis-feature gis-${featureType} gis-${feature.review_status}`} role="button" tabIndex="0" aria-label={`Select ${featureType} ${feature.id}`} onClick={selectFeature} onKeyDown={event => event.key === 'Enter' && selectFeature()} />;
      })}
    </svg><span className="map-label"><i />{projectName || 'No project selected'} <small>Persisted GIS features</small></span>
    {loading && <div className="map-state" role="status">Loading mapped features…</div>}
    {!loading && error && <div className="map-state error" role="alert">{error}</div>}
    {!loading && !error && projectName && !features.length && <div className="map-state">No processed features are available for this project.</div>}
  </div>;
}
