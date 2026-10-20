import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import RiderFlightDeck from './RiderFlightDeck'

// Attach L to window so plugins like leaflet.heat can find it
window.L = L

// Fix Leaflet icon issue
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// City Centers
const CITY_COORDS = {
  "Pune, India": [18.5204, 73.8567],
  "Mumbai, India": [19.0760, 72.8777],
  "Delhi, India": [28.6139, 77.2090],
  "Bangalore, India": [12.9716, 77.5946]
}

// Premium Status Colors (Accessible Navigation Palette)
const STATUS_COLORS = {
  idle: '#34c759',        // Apple Green
  picking: '#ff9500',     // Warm Amber (Restaurant Pickup path)
  delivering: '#0a84ff',  // Electric Blue (Customer Delivery path)
  returning: '#30d158',   // Emerald Green
  restaurant: '#ff9500',  // Apple Orange
  customer: '#af52de',    // Apple Purple
}

// Distinct shades of orange/amber so each driver's path & bike is clearly recognizable
const DRIVER_ORANGE_PALETTE = [
  '#ff4500', // Fiery Red-Orange
  '#ff6d00', // Bright Blaze Orange
  '#ff8500', // Vibrant Sunset Orange
  '#ffa200', // Amber Gold Orange
  '#ff5400', // Electric Coral Orange
  '#f77f00', // Rich Sunburst Orange
  '#ffb703', // Warm Marigold Orange
  '#fb5607', // Neon Persimmon Orange
  '#e85d04', // Deep Blood Orange
  '#faa307', // Radiant Apricot Orange
  '#f48c06', // Tangerine Glow
  '#dc2f02', // Spiced Rust Orange
]

function getDriverOrangeShade(driverId, index = 0) {
  const numMatch = String(driverId).match(/\d+/)
  const idx = numMatch ? parseInt(numMatch[0], 10) : (typeof index === 'number' ? index : 0)
  return DRIVER_ORANGE_PALETTE[Math.abs(idx) % DRIVER_ORANGE_PALETTE.length]
}

// Custom driver icon creator (Miniature Delivery Motorbike with Driver-Specific Orange Shades)
function createDriverIcon(status, customColor) {
  const color = customColor || (status === 'idle' ? '#34c759' : '#ff9500')
  const glowId = `bike-glow-${status}-${String(color).replace(/[^a-zA-Z0-9]/g, '')}`
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 34 34">
      <defs>
        <filter id="${glowId}" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="2.5" flood-color="${color}" flood-opacity="0.85"/>
        </filter>
      </defs>
      <!-- Circular badge background -->
      <circle cx="17" cy="17" r="14" fill="#0d1117" stroke="${color}" stroke-width="2.3" filter="url(#${glowId})"/>
      
      <!-- Miniature Delivery Motorbike & Box -->
      <g fill="${color}">
        <!-- Rear wheel -->
        <circle cx="9.5" cy="21" r="3.2" fill="none" stroke="${color}" stroke-width="1.8"/>
        <!-- Front wheel -->
        <circle cx="23.5" cy="21" r="3.2" fill="none" stroke="${color}" stroke-width="1.8"/>
        <!-- Chassis / Body frame -->
        <path d="M9.5 21 L14 16 L19.5 16 L23.5 21" fill="none" stroke="${color}" stroke-width="1.8" stroke-linecap="round"/>
        <path d="M15 16 L18 10 L21.5 10" fill="none" stroke="${color}" stroke-width="1.8" stroke-linecap="round"/>
        <!-- Delivery Box on back -->
        <rect x="7" y="11.5" width="6" height="5" rx="1.2" fill="${color}" stroke="#ffffff" stroke-width="0.7"/>
        <!-- Rider helmet -->
        <circle cx="16.5" cy="8.5" r="2.2" fill="${color}"/>
      </g>
      
      <!-- Glowing motion ripple if picking/delivering -->
      ${status !== 'idle' ? `
        <circle cx="17" cy="17" r="15" fill="none" stroke="${color}" stroke-width="1.8" opacity="0.6">
          <animate attributeName="r" from="14" to="22" dur="1.2s" repeatCount="indefinite" />
          <animate attributeName="opacity" from="0.7" to="0" dur="1.2s" repeatCount="indefinite" />
        </circle>
      ` : ''}
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: 'custom-driver-pin',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17],
  })
}

// Custom restaurant icon (Miniature Storefront Building)
function createRestaurantIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
      <defs>
        <filter id="rest-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#ff9500" flood-opacity="0.8"/>
        </filter>
      </defs>
      <circle cx="14" cy="14" r="12" fill="#18130e" stroke="#ff9500" stroke-width="2" filter="url(#rest-shadow)"/>
      <g fill="#ff9500">
        <!-- Roof Awning -->
        <path d="M6 10 L14 5 L22 10 Z"/>
        <!-- Building Frame -->
        <rect x="7.5" y="11" width="13" height="9" rx="1" fill="none" stroke="#ff9500" stroke-width="1.4"/>
        <!-- Door -->
        <rect x="12" y="13.5" width="4" height="6.5" rx="0.5" fill="#ff9500"/>
        <!-- Windows -->
        <rect x="9" y="12.5" width="2" height="2.5" fill="#ff9500"/>
        <rect x="17" y="12.5" width="2" height="2.5" fill="#ff9500"/>
      </g>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: 'custom-restaurant-pin',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  })
}

// Custom customer icon (Miniature Person Avatar)
function createCustomerIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 26 26">
      <defs>
        <filter id="cust-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#af52de" flood-opacity="0.8"/>
        </filter>
      </defs>
      <circle cx="13" cy="13" r="11" fill="#160f1c" stroke="#af52de" stroke-width="2" filter="url(#cust-shadow)"/>
      <g fill="#af52de">
        <!-- Head -->
        <circle cx="13" cy="8.5" r="3.2"/>
        <!-- Hair detail -->
        <path d="M10.2 8 C10.2 5.8 15.8 5.8 15.8 8 Z" fill="#ffffff" opacity="0.35"/>
        <!-- Shoulders / Torso -->
        <path d="M7.5 19 C7.5 14.5 10 13 13 13 C16 13 18.5 14.5 18.5 19 Z"/>
      </g>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: 'custom-customer-pin',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -13],
  })
}

// Custom Roadblock Icon (White Barrier Hazard Pin)
function createRoadblockIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 30 30">
      <defs>
        <filter id="block-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="3" flood-color="#ffffff" flood-opacity="0.95"/>
        </filter>
      </defs>
      <!-- Base circle badge -->
      <circle cx="15" cy="15" r="13" fill="#0c0d12" stroke="#ffffff" stroke-width="2.5" filter="url(#block-glow)"/>
      <!-- Barrier Board -->
      <rect x="6" y="11.5" width="18" height="7" rx="1.5" fill="#ffffff"/>
      <!-- Hazard stripes in black -->
      <path d="M8 11.5 L11 18.5 M13 11.5 L16 18.5 M18 11.5 L21 18.5" stroke="#0c0d12" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: 'custom-roadblock-pin',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  })
}

// Custom Delivery Destination Icon (Crisp Red Small Dot with animated pulse indicating drop-off location)
function createDeliveryDestinationIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 30 30">
      <defs>
        <filter id="red-dot-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="#ff3b30" flood-opacity="0.95"/>
        </filter>
      </defs>
      <!-- Expanding ripple pulse -->
      <circle cx="15" cy="15" r="7" fill="none" stroke="#ff3b30" stroke-width="2" opacity="0.8">
        <animate attributeName="r" values="5;13;5" dur="1.6s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.95;0.1;0.95" dur="1.6s" repeatCount="indefinite" />
      </circle>
      <!-- Small crisp solid red dot with white border -->
      <circle cx="15" cy="15" r="5" fill="#ff3b30" stroke="#ffffff" stroke-width="1.8" filter="url(#red-dot-glow)"/>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: 'custom-delivery-dot',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  })
}

// Heatmap layer component
function HeatmapLayer({ points, visible }) {
  const map = useMap()
  const heatLayerRef = useRef(null)

  useEffect(() => {
    if (visible && points.length > 0) {
      import('leaflet.heat').then(() => {
        if (heatLayerRef.current) {
          map.removeLayer(heatLayerRef.current)
        }
        heatLayerRef.current = L.heatLayer(points, {
          radius: 25,
          blur: 15,
          maxZoom: 17,
          gradient: { 0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1: 'red' }
        }).addTo(map)
      }).catch(err => console.warn("Failed to load heatmap", err))
    } else if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current)
      heatLayerRef.current = null
    }

    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current)
      }
    }
  }, [map, points, visible])

  return null
}

// Animated map view controller
function MapUpdater({ city }) {
  const map = useMap()
  useEffect(() => {
    const coords = CITY_COORDS[city]
    if (coords) {
      map.setView(coords, 12, { animate: true })
    }
  }, [city, map])
  return null
}

// Smooth auto-follow map controller for selected rider
function FollowController({ targetCoords, isFollowing }) {
  const map = useMap()
  useEffect(() => {
    if (isFollowing && targetCoords) {
      map.panTo(targetCoords, { animate: true, duration: 0.6 })
    }
  }, [map, targetCoords, isFollowing])
  return null
}

function MapView({ drivers, orders, isRunning, showHeatmap, debugRouteData, city, closedRoads = [], speed = 1 }) {
  const mapCenter = CITY_COORDS[city] || CITY_COORDS["Pune, India"]
  const [selectedDriverId, setSelectedDriverId] = useState(null)
  const [isFollowing, setIsFollowing] = useState(false)

  const selectedDriver = useMemo(() => {
    return drivers.find(d => d.driver_id === selectedDriverId) || null
  }, [drivers, selectedDriverId])
  
  // Create driver icons memo
  const driverIcons = useMemo(() => {
    const icons = {}
    Object.keys(STATUS_COLORS).forEach(status => {
      icons[status] = createDriverIcon(status)
    })
    return icons
  }, [])

  // Memoize restaurant, customer, and roadblock custom icons
  const restaurantIcon = useMemo(() => createRestaurantIcon(), [])
  const customerIcon = useMemo(() => createCustomerIcon(), [])
  const roadblockIcon = useMemo(() => createRoadblockIcon(), [])
  const deliveryDestinationIcon = useMemo(() => createDeliveryDestinationIcon(), [])

  // Active delivery destination points (Small Red Dots) for in-transit riders
  // Once the rider reaches a drop-off point, the order is delivered and this dot disappears
  const activeDeliveryDots = useMemo(() => {
    const dots = []
    const seen = new Set()

    drivers.forEach(d => {
      if (d.status === 'idle') return

      // 1. Explicit delivery_stops from backend
      if (Array.isArray(d.delivery_stops) && d.delivery_stops.length > 0) {
        d.delivery_stops.forEach(s => {
          if (s.lat && s.lng) {
            const key = `${Number(s.lat).toFixed(5)},${Number(s.lng).toFixed(5)}`
            if (!seen.has(key)) {
              seen.add(key)
              dots.push({
                driverId: d.driver_id,
                driverName: d.name,
                orderId: s.order_id,
                lat: s.lat,
                lng: s.lng,
              })
            }
          }
        })
      }
      // 2. Active non-delivered orders in current_orders
      else if (Array.isArray(d.current_orders) && d.current_orders.length > 0) {
        d.current_orders.forEach(o => {
          if (o.status !== 'delivered' && o.customer_lat && o.customer_lng) {
            const key = `${Number(o.customer_lat).toFixed(5)},${Number(o.customer_lng).toFixed(5)}`
            if (!seen.has(key)) {
              seen.add(key)
              dots.push({
                driverId: d.driver_id,
                driverName: d.name,
                orderId: o.order_id,
                lat: o.customer_lat,
                lng: o.customer_lng,
              })
            }
          }
        })
      }
      // 3. Fallback to end of route_coords for delivering drivers
      else if (d.status === 'delivering' && Array.isArray(d.route_coords) && d.route_coords.length > 0) {
        const dest = d.route_coords[d.route_coords.length - 1]
        if (dest && dest[0] && dest[1]) {
          const key = `${Number(dest[0]).toFixed(5)},${Number(dest[1]).toFixed(5)}`
          if (!seen.has(key)) {
            seen.add(key)
            dots.push({
              driverId: d.driver_id,
              driverName: d.name,
              orderId: null,
              lat: dest[0],
              lng: dest[1],
            })
          }
        }
      }
    })

    return dots
  }, [drivers])

  // Forward route polylines starting precisely at current rider coordinates with individual orange shades
  const routes = useMemo(() => {
    return drivers
      .filter(d => d.status !== 'idle' && d.route_coords && d.route_coords.length > 0)
      .map((d, idx) => {
        const coords = d.route_coords.map(c => [c[0], c[1]])
        // Ensure path connects directly to rider's current bike position
        if (coords.length > 0 && (Math.abs(coords[0][0] - d.lat) > 0.00005 || Math.abs(coords[0][1] - d.lng) > 0.00005)) {
          coords.unshift([d.lat, d.lng])
        }
        const orangeColor = getDriverOrangeShade(d.driver_id, idx)
        return {
          id: d.driver_id,
          coords: coords,
          status: d.status,
          color: orangeColor,
        }
      })
  }, [drivers])

  // Heatmap data: all restaurant and customer locations
  const heatmapPoints = useMemo(() => {
    const points = []
    orders.forEach(o => {
      if (o.status !== 'delivered') {
        points.push([o.restaurant_lat, o.restaurant_lng, 0.5])
        points.push([o.customer_lat, o.customer_lng, 0.3])
      }
    })
    return points
  }, [orders])

  return (
    <div 
      className="map-container" 
      style={{ 
        height: '100%', 
        width: '100%', 
        position: 'absolute', 
        top: 0, 
        left: 0,
        '--move-duration': `${(0.8 / Math.max(0.2, speed || 1)).toFixed(2)}s`
      }}
    >
      <MapContainer
        center={mapCenter}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
        preferCanvas={true}
      >
        {/* Standard OSM with CSS Dark Mode Inversion (Supports deep zoom up to 19) */}
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="dark-osm-tiles"
          maxZoom={19}
        />

        <MapUpdater city={city} />
        <FollowController 
          targetCoords={selectedDriver ? [selectedDriver.lat, selectedDriver.lng] : null} 
          isFollowing={isFollowing} 
        />
        <HeatmapLayer points={heatmapPoints} visible={showHeatmap} />

        {/* Delivery routes (Each Driver has a Unique Vibrant Shade of Orange!) */}
        {routes.map(route => {
          const color = route.color || STATUS_COLORS[route.status] || '#ff8500';
          return (
            <div key={`route-group-${route.id}`}>
              {/* Outer Ambient Glow with Driver-Specific Orange */}
              <Polyline
                positions={route.coords}
                pathOptions={{
                  color: color,
                  weight: 9,
                  opacity: 0.35,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
              {/* Vivid Neon Delivery Path */}
              <Polyline
                positions={route.coords}
                pathOptions={{
                  color: color,
                  weight: 4,
                  opacity: 0.95,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
              {/* Center Core Highlight for Apple-Maps Polish */}
              <Polyline
                positions={route.coords}
                pathOptions={{
                  color: '#ffffff',
                  weight: 1.2,
                  opacity: 0.8,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
            </div>
          )
        })}

        {/* Visual Search Cloud — Dijkstra 360-degree radial exploration cloud */}
        {debugRouteData?.dijkstra?.explored_coords && debugRouteData.dijkstra.explored_coords.map((c, i) => (
          <CircleMarker 
            key={`dijkstra-node-${i}`}
            center={[c[0], c[1]]} 
            radius={2}
            pathOptions={{ color: '#34c759', fillColor: '#34c759', fillOpacity: 0.5, weight: 0 }} 
          />
        ))}

        {/* Visual Search Cloud — A* focused directional search cone */}
        {debugRouteData?.astar?.explored_coords && debugRouteData.astar.explored_coords.map((c, i) => (
          <CircleMarker 
            key={`astar-node-${i}`}
            center={[c[0], c[1]]} 
            radius={2.5}
            pathOptions={{ color: '#00f2fe', fillColor: '#00f2fe', fillOpacity: 0.85, weight: 0 }} 
          />
        ))}

        {/* Restaurant markers (Storefront Building Pin) */}
        {orders.map(order => (
          <Marker
            key={`rest-${order.order_id}`}
            position={[order.restaurant_lat, order.restaurant_lng]}
            icon={restaurantIcon}
          >
            <Popup>
              <div className="driver-popup">
                <h4>🏬 {order.restaurant_name || "Restaurant"}</h4>
                <p>Zone: {order.restaurant_zone}</p>
                <p>Status: {order.status}</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Red Small Dot indicating that the rider has to finish delivery at this point */}
        {/* Once the rider reaches this point, delivery completes and the red dot disappears, leading to next delivery */}
        {activeDeliveryDots.map(dot => (
          <Marker
            key={`delivery-dot-${dot.driverId}-${dot.orderId || `${dot.lat}-${dot.lng}`}`}
            position={[dot.lat, dot.lng]}
            icon={deliveryDestinationIcon}
          >
            <Popup>
              <div className="driver-popup">
                <h4 style={{ color: '#ff3b30' }}>🔴 Delivery Drop-off Point</h4>
                <p><strong>Rider:</strong> {dot.driverName || dot.driverId}</p>
                {dot.orderId && <p><strong>Order:</strong> {dot.orderId}</p>}
                <div style={{ marginTop: '5px', fontSize: '11px', color: '#ff9500' }}>
                  ⏳ En route. Once rider arrives here, the delivery is complete and this red dot disappears.
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Customer markers (Person Pin for unassigned/pending pool) */}
        {orders.map(order => {
          // If this order's destination is already an active delivery target marked with the Red Dot, don't duplicate
          const hasActiveRedDot = activeDeliveryDots.some(
            d => d.orderId === order.order_id || 
            (Math.abs(d.lat - order.customer_lat) < 0.0001 && Math.abs(d.lng - order.customer_lng) < 0.0001)
          )
          if (hasActiveRedDot) return null

          return (
            <Marker
              key={`cust-${order.order_id}`}
              position={[order.customer_lat, order.customer_lng]}
              icon={customerIcon}
            >
              <Popup>
                <div className="driver-popup">
                  <h4>👤 Customer</h4>
                  <p>Order: {order.order_id}</p>
                  <p>Status: {order.status}</p>
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* Driver markers (Miniature Motorbike with individual orange shades) */}
        {drivers.map((driver, idx) => {
          const driverOrange = getDriverOrangeShade(driver.driver_id, idx)
          const icon = driver.status === 'idle'
            ? createDriverIcon('idle', '#34c759')
            : createDriverIcon(driver.status, driverOrange)

          return (
            <Marker
              key={driver.driver_id}
              position={[driver.lat, driver.lng]}
              icon={icon}
              eventHandlers={{
                click: () => {
                  setSelectedDriverId(driver.driver_id)
                }
              }}
            >
              <Popup>
                <div className="driver-popup">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h4>🏍️ {driver.driver_id}</h4>
                    <span 
                      style={{ 
                        width: '12px', 
                        height: '12px', 
                        borderRadius: '50%', 
                        background: driverOrange, 
                        display: 'inline-block',
                        boxShadow: `0 0 8px ${driverOrange}`
                      }}
                      title="Driver's individual route color"
                    ></span>
                  </div>
                  <span className={`status-tag ${driver.status}`} style={{ borderColor: driverOrange, color: driverOrange }}>
                    {driver.status.toUpperCase()}
                  </span>
                  <p>Deliveries: {driver.deliveries || 0}</p>
                  {driver.active_batch && <p>Batch: {driver.active_batch}</p>}
                  <div style={{ marginTop: '6px', fontSize: '11px', color: '#58a6ff' }}>
                    ℹ️ Click bike anytime to view Flight Deck HUD
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* Closed Roads Blockages in Prominent WHITE Color */}
        {closedRoads.map((closure, idx) => (
          <div key={`closed-road-${idx}`}>
            {/* Outer White Hazard Glow */}
            <Polyline
              positions={closure.coords}
              pathOptions={{
                color: '#ffffff',
                weight: 12,
                opacity: 0.5,
                lineCap: 'round',
              }}
            />
            {/* Bright Solid White Hazard Line */}
            <Polyline
              positions={closure.coords}
              pathOptions={{
                color: '#ffffff',
                weight: 5,
                opacity: 0.95,
                dashArray: '8, 8',
                lineCap: 'round',
              }}
            />
            {/* Roadblock Icon Marker in Center */}
            <Marker
              position={[
                (closure.coords[0][0] + closure.coords[1][0]) / 2,
                (closure.coords[0][1] + closure.coords[1][1]) / 2
              ]}
              icon={roadblockIcon}
            >
              <Popup>
                <div className="driver-popup">
                  <h4>🚧 ROAD CLOSED</h4>
                  <p>Status: Impassable (1,000,000s)</p>
                  <p>Dynamic A* re-routing around blockage!</p>
                </div>
              </Popup>
            </Marker>
          </div>
        ))}
      </MapContainer>

      {/* Map overlay legend (Premium) */}
      {!showHeatmap && (
        <div className="map-legend">
          <div className="map-legend-title">System Status</div>
          <div className="legend-grid">
            <div className="legend-item">
              <span className="legend-emoji">🏬</span> Restaurant
            </div>
            <div className="legend-item">
              <span className="legend-emoji">👤</span> Customer
            </div>
            <div className="legend-item">
              <span className="legend-emoji">🚧</span> Blocked
            </div>
            <div className="legend-item">
              <span className="status-dot" style={{ background: STATUS_COLORS.idle, boxShadow: `0 0 10px ${STATUS_COLORS.idle}` }}></span> 🏍️ Idle
            </div>
            <div className="legend-item">
              <span className="status-dot" style={{ background: '#ff7b00', boxShadow: '0 0 10px #ff7b00' }}></span> 🏍️ Active (Shades of Orange)
            </div>
          </div>
        </div>
      )}

      {/* Rider Flight Deck HUD */}
      {selectedDriver && (
        <RiderFlightDeck
          driver={selectedDriver}
          isFollowing={isFollowing}
          onToggleFollow={() => setIsFollowing(prev => !prev)}
          onClose={() => {
            setSelectedDriverId(null)
            setIsFollowing(false)
          }}
        />
      )}
    </div>
  )
}

export default MapView


