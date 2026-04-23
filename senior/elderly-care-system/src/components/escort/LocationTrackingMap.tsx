// @ts-nocheck
import { useState, useEffect, useCallback } from 'react';
import { GoogleMap, Marker, DirectionsRenderer, InfoWindow, useJsApiLoader } from '@react-google-maps/api';
import { supabase } from '../../lib/supabase';

interface LocationPoint {
  id: string;
  order_id: string;
  worker_id: string;
  latitude: number;
  longitude: number;
  address: string;
  recorded_at: string;
}

interface LocationTrackingMapProps {
  orderId: string;
  elderlyLocation?: { lat: number; lng: number; address: string };
  hospitalLocation?: { lat: number; lng: number; address: string };
  showRoute?: boolean;
  autoUpdate?: boolean;
  height?: string;
}

const GOOGLE_MAPS_API_KEY = 'AIzaSyCO0kKndUNlmQi3B5mxy4dblg_8WYcuKuk';

const mapContainerStyle = {
  width: '100%',
  height: '500px'
};

const defaultCenter = {
  lat: 30.5928, // 武汉市中心
  lng: 114.3055
};

export default function LocationTrackingMap({
  orderId,
  elderlyLocation,
  hospitalLocation,
  showRoute = true,
  autoUpdate = true,
  height = '500px'
}: LocationTrackingMapProps) {
  const [workerLocation, setWorkerLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [workerAddress, setWorkerAddress] = useState<string>('');
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [selectedMarker, setSelectedMarker] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    language: 'zh-CN',
    region: 'CN'
  });

  // 获取陪诊师最新位置
  const fetchWorkerLocation = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('location_tracking')
        .select('*')
        .eq('order_id', orderId)
        .order('recorded_at', { ascending: false })
        .limit(1)
        .single();

      if (error) {
        console.error('获取位置失败:', error);
        return;
      }

      if (data) {
        setWorkerLocation({
          lat: data.latitude,
          lng: data.longitude
        });
        setWorkerAddress(data.address || '');
        setLastUpdate(new Date(data.recorded_at));
      }
    } catch (error) {
      console.error('获取陪诊师位置失败:', error);
    }
  }, [orderId]);

  // 计算路线
  const calculateRoute = useCallback(() => {
    if (!isLoaded || !workerLocation || !hospitalLocation) return;

    const directionsService = new google.maps.DirectionsService();

    directionsService.route(
      {
        origin: workerLocation,
        destination: hospitalLocation,
        travelMode: google.maps.TravelMode.DRIVING,
        region: 'CN'
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result) {
          setDirections(result);
        } else {
          console.error('路线规划失败:', status);
        }
      }
    );
  }, [isLoaded, workerLocation, hospitalLocation]);

  // 初始加载和定时更新
  useEffect(() => {
    fetchWorkerLocation();

    if (autoUpdate) {
      const interval = setInterval(() => {
        fetchWorkerLocation();
      }, 30000); // 每30秒更新一次

      return () => clearInterval(interval);
    }
  }, [fetchWorkerLocation, autoUpdate]);

  // 位置变化时重新计算路线
  useEffect(() => {
    if (showRoute && workerLocation && hospitalLocation) {
      calculateRoute();
    }
  }, [showRoute, workerLocation, hospitalLocation, calculateRoute]);

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">地图加载失败，请检查网络连接</p>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center" style={{ height }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载地图中...</p>
        </div>
      </div>
    );
  }

  const center = workerLocation || elderlyLocation || defaultCenter;

  return (
    <div className="space-y-4">
      {/* 位置信息栏 */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          {elderlyLocation && (
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <div>
                <div className="font-medium text-gray-700">老人位置</div>
                <div className="text-gray-600">{elderlyLocation.address}</div>
              </div>
            </div>
          )}
          
          {workerLocation && (
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <div>
                <div className="font-medium text-gray-700">陪诊师位置</div>
                <div className="text-gray-600">{workerAddress}</div>
                {lastUpdate && (
                  <div className="text-xs text-gray-500 mt-1">
                    更新于 {lastUpdate.toLocaleTimeString('zh-CN')}
                  </div>
                )}
              </div>
            </div>
          )}

          {hospitalLocation && (
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
              <div>
                <div className="font-medium text-gray-700">医院位置</div>
                <div className="text-gray-600">{hospitalLocation.address}</div>
              </div>
            </div>
          )}
        </div>

        {directions && (
          <div className="mt-3 pt-3 border-t border-indigo-200">
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <span className="font-medium text-gray-700">
                  距离: {directions.routes[0]?.legs[0]?.distance?.text}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-gray-700">
                  预计时间: {directions.routes[0]?.legs[0]?.duration?.text}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 地图容器 */}
      <div className="rounded-lg overflow-hidden shadow-lg border border-gray-200">
        <GoogleMap
          mapContainerStyle={{ ...mapContainerStyle, height }}
          center={center}
          zoom={13}
          options={{
            zoomControl: true,
            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: true,
          }}
        >
          {/* 老人位置标记 */}
          {elderlyLocation && (
            <Marker
              position={elderlyLocation}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
                    <path fill="#3B82F6" d="M16 0C7.2 0 0 7.2 0 16c0 8.8 16 24 16 24s16-15.2 16-24C32 7.2 24.8 0 16 0z"/>
                    <circle fill="white" cx="16" cy="16" r="8"/>
                  </svg>
                `),
                scaledSize: new google.maps.Size(32, 40)
              }}
              onClick={() => setSelectedMarker('elderly')}
            >
              {selectedMarker === 'elderly' && (
                <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                  <div className="p-2">
                    <h3 className="font-semibold text-blue-700">老人位置</h3>
                    <p className="text-sm text-gray-600">{elderlyLocation.address}</p>
                  </div>
                </InfoWindow>
              )}
            </Marker>
          )}

          {/* 陪诊师位置标记 */}
          {workerLocation && (
            <Marker
              position={workerLocation}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
                    <path fill="#10B981" d="M16 0C7.2 0 0 7.2 0 16c0 8.8 16 24 16 24s16-15.2 16-24C32 7.2 24.8 0 16 0z"/>
                    <circle fill="white" cx="16" cy="16" r="8"/>
                  </svg>
                `),
                scaledSize: new google.maps.Size(32, 40)
              }}
              onClick={() => setSelectedMarker('worker')}
            >
              {selectedMarker === 'worker' && (
                <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                  <div className="p-2">
                    <h3 className="font-semibold text-green-700">陪诊师位置</h3>
                    <p className="text-sm text-gray-600">{workerAddress}</p>
                    {lastUpdate && (
                      <p className="text-xs text-gray-500 mt-1">
                        {lastUpdate.toLocaleString('zh-CN')}
                      </p>
                    )}
                  </div>
                </InfoWindow>
              )}
            </Marker>
          )}

          {/* 医院位置标记 */}
          {hospitalLocation && (
            <Marker
              position={hospitalLocation}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
                    <path fill="#EF4444" d="M16 0C7.2 0 0 7.2 0 16c0 8.8 16 24 16 24s16-15.2 16-24C32 7.2 24.8 0 16 0z"/>
                    <path fill="white" d="M12 10h8v4h4v8h-4v4h-8v-4H8v-8h4v-4z"/>
                  </svg>
                `),
                scaledSize: new google.maps.Size(32, 40)
              }}
              onClick={() => setSelectedMarker('hospital')}
            >
              {selectedMarker === 'hospital' && (
                <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                  <div className="p-2">
                    <h3 className="font-semibold text-red-700">医院位置</h3>
                    <p className="text-sm text-gray-600">{hospitalLocation.address}</p>
                  </div>
                </InfoWindow>
              )}
            </Marker>
          )}

          {/* 路线显示 */}
          {directions && showRoute && (
            <DirectionsRenderer
              directions={directions}
              options={{
                suppressMarkers: true,
                polylineOptions: {
                  strokeColor: '#6366F1',
                  strokeWeight: 5,
                  strokeOpacity: 0.7
                }
              }}
            />
          )}
        </GoogleMap>
      </div>

      {/* 刷新按钮 */}
      {!autoUpdate && (
        <div className="flex justify-end">
          <button
            onClick={fetchWorkerLocation}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            刷新位置
          </button>
        </div>
      )}
    </div>
  );
}
