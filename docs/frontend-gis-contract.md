# Frontend GIS API contract

The frontend deliberately does not persist, publish, or derive GIS feature state.
It expects the GIS service to expose the following endpoints:

- `GET /api/projects/{project_id}/features` returns a GeoJSON `FeatureCollection`
  (or an object with a `features` array). Each feature has `properties.feature_type`
  of `building`, `road`, or `parcel`, plus its server-owned review/publication state.
- `GET /api/projects/{project_id}/features?published=true` returns only features
  that are accepted and published. This is the endpoint used by the public map.
- `PATCH /api/features/{feature_id}/review` accepts `{ decision, notes, geometry? }`
  and returns the updated feature. `geometry` is optional and sent only when an
  editor is added and the backend supports geometry updates.

Projects may provide `latitude` and `longitude`, or `bounding_box`/`bbox` as
`[minLongitude, minLatitude, maxLongitude, maxLatitude]`. The map uses the bounds
when available and otherwise centers on the coordinates. A parcel feature is
displayed as an indicative mapping layer and is never labelled a legal boundary.
