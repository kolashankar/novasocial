import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  FlatList,
  Modal,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';

interface LocationData {
  id: string;
  name: string;
  displayName: string;
  address?: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  category?: string;
  distance?: number;
}

interface LocationPickerProps {
  visible: boolean;
  onClose: () => void;
  onLocationSelected: (location: LocationData) => void;
  selectedLocation?: LocationData | null;
}

export const LocationPicker: React.FC<LocationPickerProps> = ({
  visible,
  onClose,
  onLocationSelected,
  selectedLocation
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationData[]>([]);
  const [currentLocation, setCurrentLocation] = useState<{lat: number, lng: number} | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingLocation, setLoadingLocation] = useState(false);

  useEffect(() => {
    if (visible) {
      getCurrentLocation();
    }
  }, [visible]);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchLocations(searchQuery);
    } else if (currentLocation) {
      getNearbyLocations();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, currentLocation]);

  const getCurrentLocation = async () => {
    setLoadingLocation(true);
    try {
      // Request permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          'Permission Required',
          'Please enable location permissions to find nearby places.',
          [{ text: 'OK' }]
        );
        return;
      }

      // Get current location
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      setCurrentLocation({
        lat: location.coords.latitude,
        lng: location.coords.longitude
      });
    } catch (error) {
      console.error('Error getting location:', error);
      Alert.alert('Location Error', 'Unable to get your current location');
    } finally {
      setLoadingLocation(false);
    }
  };

  const searchLocations = async (query: string) => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/search/tags?q=${encodeURIComponent(query)}&type=locations&limit=15`);
      const data = await response.json();
      
      // Add distance if we have current location
      const locations = data.locations || [];
      if (currentLocation) {
        locations.forEach((loc: LocationData) => {
          if (loc.coordinates) {
            loc.distance = calculateDistance(
              currentLocation.lat,
              currentLocation.lng,
              loc.coordinates.lat,
              loc.coordinates.lng
            );
          }
        });
        // Sort by distance
        locations.sort((a: LocationData, b: LocationData) => (a.distance || 0) - (b.distance || 0));
      }
      
      setSearchResults(locations);
    } catch (error) {
      console.error('Error searching locations:', error);
      Alert.alert('Error', 'Failed to search locations');
    } finally {
      setLoading(false);
    }
  };

  const getNearbyLocations = async () => {
    if (!currentLocation) return;
    
    setLoading(true);
    try {
      // Mock nearby locations based on current location
      // In a real app, this would call a places API like Google Places
      const response = await fetch(`/api/search/tags?q=&type=locations&limit=10`);
      const data = await response.json();
      
      const locations = data.locations || [];
      locations.forEach((loc: LocationData) => {
        if (loc.coordinates) {
          loc.distance = calculateDistance(
            currentLocation.lat,
            currentLocation.lng,
            loc.coordinates.lat,
            loc.coordinates.lng
          );
        }
      });
      
      // Sort by distance
      locations.sort((a: LocationData, b: LocationData) => (a.distance || 0) - (b.distance || 0));
      setSearchResults(locations);
    } catch (error) {
      console.error('Error fetching nearby locations:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const formatDistance = (distance?: number): string => {
    if (!distance) return '';
    if (distance < 1) {
      return `${Math.round(distance * 1000)}m away`;
    }
    return `${distance.toFixed(1)}km away`;
  };

  const getCategoryIcon = (category?: string): string => {
    switch (category) {
      case 'restaurant': return 'restaurant-outline';
      case 'park': return 'leaf-outline';
      case 'landmark': return 'location-outline';
      case 'mall': return 'storefront-outline';
      case 'hotel': return 'bed-outline';
      default: return 'location-outline';
    }
  };

  const handleLocationSelect = (location: LocationData) => {
    onLocationSelected(location);
    onClose();
  };

  const handleRemoveLocation = () => {
    onLocationSelected(null as any);
    onClose();
  };

  const renderLocationItem = ({ item }: { item: LocationData }) => (
    <TouchableOpacity
      style={styles.locationItem}
      onPress={() => handleLocationSelect(item)}
    >
      <View style={styles.locationIcon}>
        <Ionicons 
          name={getCategoryIcon(item.category) as any} 
          size={24} 
          color="#667eea" 
        />
      </View>
      <View style={styles.locationInfo}>
        <Text style={styles.locationName}>{item.name}</Text>
        <Text style={styles.locationAddress}>{item.address}</Text>
        {item.distance && (
          <Text style={styles.locationDistance}>{formatDistance(item.distance)}</Text>
        )}
      </View>
      <Ionicons name="chevron-forward" size={20} color="#94a3b8" />
    </TouchableOpacity>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose}>
            <Ionicons name="close" size={24} color="#1e293b" />
          </TouchableOpacity>
          <Text style={styles.title}>Add Location</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Current Location Button */}
        <TouchableOpacity 
          style={styles.currentLocationButton}
          onPress={getCurrentLocation}
          disabled={loadingLocation}
        >
          <View style={styles.currentLocationContent}>
            <View style={styles.currentLocationIcon}>
              {loadingLocation ? (
                <ActivityIndicator size="small" color="#667eea" />
              ) : (
                <Ionicons name="navigate" size={20} color="#667eea" />
              )}
            </View>
            <View style={styles.currentLocationInfo}>
              <Text style={styles.currentLocationText}>
                {loadingLocation ? 'Getting your location...' : 'Use Current Location'}
              </Text>
              <Text style={styles.currentLocationSubtext}>
                Find places around you
              </Text>
            </View>
          </View>
        </TouchableOpacity>

        {/* Search Input */}
        <View style={styles.searchContainer}>
          <View style={styles.searchInputContainer}>
            <Ionicons name="search" size={20} color="#94a3b8" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search for a place..."
              placeholderTextColor="#94a3b8"
              value={searchQuery}
              onChangeText={setSearchQuery}
              autoCapitalize="words"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={20} color="#94a3b8" />
              </TouchableOpacity>
            )}
          </div>
        </View>

        {/* Selected Location */}
        {selectedLocation && (
          <View style={styles.selectedLocationContainer}>
            <View style={styles.selectedLocationHeader}>
              <Text style={styles.selectedLocationTitle}>Current Selection</Text>
              <TouchableOpacity onPress={handleRemoveLocation}>
                <Text style={styles.removeLocationText}>Remove</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.selectedLocationItem}>
              <View style={styles.locationIcon}>
                <Ionicons 
                  name={getCategoryIcon(selectedLocation.category) as any} 
                  size={24} 
                  color="#10b981" 
                />
              </View>
              <View style={styles.locationInfo}>
                <Text style={[styles.locationName, { color: '#10b981' }]}>
                  {selectedLocation.name}
                </Text>
                <Text style={styles.locationAddress}>{selectedLocation.address}</Text>
              </View>
              <Ionicons name="checkmark-circle" size={24} color="#10b981" />
            </View>
          </View>
        )}

        {/* Search Results */}
        <View style={styles.resultsContainer}>
          <Text style={styles.resultsTitle}>
            {searchQuery ? `Search Results` : 'Nearby Places'}
          </Text>
          
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#667eea" />
              <Text style={styles.loadingText}>Searching...</Text>
            </View>
          ) : (
            <FlatList
              data={searchResults}
              keyExtractor={(item) => item.id}
              renderItem={renderLocationItem}
              showsVerticalScrollIndicator={false}
              style={styles.resultsList}
              ListEmptyComponent={() => (
                <View style={styles.emptyState}>
                  <Ionicons name="location-outline" size={48} color="#94a3b8" />
                  <Text style={styles.emptyText}>
                    {searchQuery.length < 2 
                      ? currentLocation 
                        ? 'Nearby places will appear here'
                        : 'Enable location to see nearby places'
                      : 'No places found'
                    }
                  </Text>
                  {!currentLocation && searchQuery.length < 2 && (
                    <TouchableOpacity 
                      style={styles.enableLocationButton}
                      onPress={getCurrentLocation}
                    >
                      <Text style={styles.enableLocationText}>Enable Location</Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            />
          )}
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  currentLocationButton: {
    margin: 16,
    marginBottom: 0,
  },
  currentLocationContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  currentLocationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  currentLocationInfo: {
    flex: 1,
  },
  currentLocationText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 2,
  },
  currentLocationSubtext: {
    fontSize: 14,
    color: '#64748b',
  },
  searchContainer: {
    padding: 16,
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 25,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1e293b',
  },
  selectedLocationContainer: {
    margin: 16,
    marginTop: 0,
    padding: 16,
    backgroundColor: '#f0fdf4',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#dcfce7',
  },
  selectedLocationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  selectedLocationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#166534',
  },
  removeLocationText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#dc2626',
  },
  selectedLocationItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultsContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
  },
  resultsList: {
    flex: 1,
  },
  locationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  locationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f1f5f9',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  locationInfo: {
    flex: 1,
  },
  locationName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 2,
  },
  locationAddress: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 2,
  },
  locationDistance: {
    fontSize: 12,
    color: '#94a3b8',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#94a3b8',
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  enableLocationButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#667eea',
    borderRadius: 20,
  },
  enableLocationText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
});