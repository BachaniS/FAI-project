"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import axios from 'axios';

// Update interface to match the JSON structure
interface Place {
  name: string;
  address: string;
  capacity: string;
  features: string[];
  website: string;
  state: string;
  estimated_cost: string;
  event_types: string[];
}

export default function HomePage() {
  const router = useRouter();
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [showVenues, setShowVenues] = useState(false);

  useEffect(() => {
    const fetchRandomPlaces = async () => {
      try {
        const { data } = await axios.get(
          "http://localhost:8000/generate-random-places",
          {
            params: {
              event_type: "party"
            }
          }
        );
        // The response structure from your backend returns data.places
        setPlaces(data.places);
      } catch (error) {
        console.error('Failed to fetch random places:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRandomPlaces();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-7xl mx-auto"> {/* Increased max-width for better display of cards */}
        <div className="space-y-8">
          <section className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-8 shadow-lg backdrop-blur-sm border border-gray-100 dark:border-gray-700">
            <h2 className="text-3xl font-semibold mb-6 text-blue-600 dark:text-blue-400">
              Your Journey to Finding the Perfect Venue
            </h2>
            <p className="text-gray-700 dark:text-gray-300 mb-6 text-lg leading-relaxed">
              SchedulEase provides a seamless experience for booking venues for
              your events. Discover options, resources, and guidance to enhance
              your event planning.
            </p>
            <div className="flex gap-4">
              <button
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-all duration-300 transform hover:scale-105 shadow-md"
                onClick={() => router.push("/chat")}
              >
                Use AI to find a perfect place for you
              </button>
              <button
                onClick={() => setShowVenues(true)}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-all duration-300 transform hover:scale-105 shadow-md"
              >
                Not sure yet? Let AI help you find some suggestions...
              </button>
            </div>
          </section>

          {/* <section className="grid md:grid-cols-2 gap-8">
            <div
              className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 backdrop-blur-sm border border-gray-100 dark:border-gray-700 cursor-pointer"
              onClick={() => router.push("/venue-resource")}
            >
              <h3 className="text-2xl font-semibold mb-4 text-blue-600 dark:text-blue-400 cursor-pointer">
                Venue Resources
              </h3>
              <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                Access expert-curated content on venue selection, event planning, and logistics.
              </p>
            </div>

            <div className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 backdrop-blur-sm border border-gray-100 dark:border-gray-700 cursor-pointer"
              onClick={() => router.push("/event-pathway")}
            >
              <h3 className="text-2xl font-semibold mb-4 text-blue-600 dark:text-blue-400">
                Event Pathways
              </h3>
              <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                Discover personalized options for hosting events and guided planning resources.
              </p>
            </div>
          </section> */}

          {/* Modify the Random Places Section to only show when showVenues is true */}
          {showVenues && (
            <section className="mt-12">
              <h2 className="text-3xl font-semibold mb-8 text-blue-600 dark:text-blue-400">
                Discover Amazing Venues
              </h2>
              
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {places.map((place, index) => (
                    <div
                      key={index}
                      className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 backdrop-blur-sm border border-gray-100 dark:border-gray-700 transform hover:-translate-y-2 hover:scale-[1.02]"
                    >
                      <h3 className="text-xl font-semibold mb-3 text-blue-600 dark:text-blue-400">
                        {place.name}
                      </h3>
                      <div className="space-y-2 text-gray-700 dark:text-gray-300">
                        <p className="text-sm">📍 {place.address}</p>
                        <p className="text-sm">�� {place.state}</p>
                        <p className="text-sm">👥 Capacity: {place.capacity}</p>
                        <p className="text-sm">💰 {place.estimated_cost}</p>
                        
                        <div className="mt-4">
                          <p className="text-sm font-semibold mb-2">Features:</p>
                          <div className="flex flex-wrap gap-2">
                            {place.features.map((feature, idx) => (
                              <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full"
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div className="mt-4">
                          <p className="text-sm font-semibold mb-2">Event Types:</p>
                          <div className="flex flex-wrap gap-2">
                            {place.event_types.map((type, idx) => (
                              <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full"
                              >
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>

                        <a
                          href={place.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-4 inline-block text-blue-600 dark:text-blue-400 hover:underline text-sm"
                        >
                          Visit Website →
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
