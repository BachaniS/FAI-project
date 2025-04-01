"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import toast from "react-hot-toast";
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

interface Venue {
  name: string;
  address: string;
  capacity: string;
  features: string[];
  source: string;
  accessibility_score: number;
  weather_data: {
    Temperature: number;
    Humidity: number;
    WindSpeed: number;
    PrecipitationProbability: number;
  };
  safety_data: {
    Hostility: string;
  };
  date: string;
  event_type: string;
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function SavedVenuesPage() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSavedVenues = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/saved-venues');
        const venuesData = response.data.venues || response.data;
        setVenues(Array.isArray(venuesData) ? venuesData : []);
      } catch (error) {
        console.error('Error fetching venues:', error);
        setVenues([]);
        toast.error('Failed to fetch saved venues');
      } finally {
        setLoading(false);
      }
    };

    fetchSavedVenues();
  }, []);

  const generateBostonTrafficData = (venueName: string) => {
    const hours = Array.from({ length: 15 }, (_, i) => `${i + 9}:00`);
    const nameSeed = venueName.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    const data = hours.map((_, index) => {
      const baseValue = (nameSeed + index) % 20;
      let timePattern = 0;
      
      if (index >= 7 && index <= 9) timePattern = 30;
      else if (index >= 11 && index <= 14) timePattern = 40;
      else if (index >= 16 && index <= 19) timePattern = 35;
      else if (index >= 22 || index <= 2) timePattern = nameSeed % 2 === 0 ? 25 : 5;
      else timePattern = 15;

      const randomNoise = Math.random() * 10;
      const weatherFactor = Math.sin(nameSeed + index) * 5;

      return Math.floor(Math.max(20, Math.min(90, baseValue + timePattern + randomNoise + weatherFactor)));
    });

    return { hours, data };
  };

  const generateVenueInsights = (venueName: string) => {
    const trafficData = generateBostonTrafficData(venueName).data;
    const peakHours = trafficData.reduce((peaks, value, index) => {
      if (value > 70) peaks.push(`${index}:00`);
      return peaks;
    }, [] as string[]);

    const avgTraffic = Math.round(trafficData.reduce((sum, val) => sum + val, 0) / trafficData.length);
    const maxTraffic = Math.max(...trafficData);
    const quietHours = trafficData.filter((v) => v < 30).length;

    const resourceSavings = {
      energy: Math.round(quietHours * 2.5 * 10),
      staff: Math.round(quietHours * 1.5),
      water: Math.round(quietHours * 50),
      emissions: Math.round(quietHours * 1.8),
    };

    return { peakHours, avgTraffic, maxTraffic, quietHours, resourceSavings };
  };

  const generateWeatherData = (weatherData: Venue["weather_data"]) => {
    if (!weatherData) return null;

    const hours = Array.from({ length: 15 }, (_, i) => `${i + 9}:00`);
    const baseTemp = weatherData.Temperature;
    const baseHumidity = weatherData.Humidity;

    const temperatureData = hours.map((_, i) => {
      const timeOfDay = Math.sin((i / hours.length) * Math.PI) * 3;
      return baseTemp + timeOfDay + (Math.random() * 2 - 1);
    });

    const humidityData = hours.map((_, i) => {
      const timeOfDay = -Math.sin((i / hours.length) * Math.PI) * 5;
      return Math.min(100, Math.max(0, baseHumidity + timeOfDay + (Math.random() * 4 - 2)));
    });

    return { hours, temperatureData, humidityData };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-xl text-gray-600 dark:text-gray-300">Loading saved venues...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">
            Saved Venues
          </h1>
          <Link
            href="/chat"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Chat
          </Link>
        </div>

        {venues.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-300 text-lg">No saved venues found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-8">
            {venues.map((venue, index) => (
              <div 
                key={`${venue.name}-${venue.address}-${index}`} 
                className="bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-0.5 rounded-xl shadow-lg relative"
              >
                <div className="h-full w-full bg-white dark:bg-gray-800 rounded-xl p-8 backdrop-blur-sm bg-opacity-95 dark:bg-opacity-95">
                  <div className="flex flex-col md:flex-row gap-8">
                    <div className="md:w-1/3 flex flex-col h-full">
                      <h3 className="font-bold text-2xl mb-4 bg-gradient-to-r from-purple-600 to-pink-600 inline-block text-transparent bg-clip-text">
                        {venue.name}
                      </h3>
                      
                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg transform transition-all duration-300 hover:scale-105 hover:shadow-xl">
                        <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
                          {venue.address}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Capacity: {venue.capacity}
                        </p>
                      </div>

                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg transform transition-all duration-300 hover:scale-105 hover:shadow-xl">
                        <p className="text-sm font-semibold mb-2">Event Type:</p>
                        <p className="text-gray-600 dark:text-gray-400">{venue.event_type}</p>
                      </div>

                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <p className="text-sm font-semibold mb-2">Features:</p>
                        <ul className="text-sm space-y-1">
                          {venue.features?.map((feature, idx) => (
                            <li key={idx} className="text-gray-600 dark:text-gray-400">
                              • {feature}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg mt-4">
                        <div className="mb-3">
                          <span className="font-semibold">Accessibility Score: </span>
                          <span className={venue.accessibility_score >= 80 ? "text-green-500" : "text-red-500"}>
                            {venue.accessibility_score}%
                          </span>
                        </div>

                        {venue.weather_data && (
                          <div>
                            <p className="font-semibold mb-2">Weather Conditions:</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>Temperature: {venue.weather_data.Temperature}°C</div>
                              <div>Humidity: {venue.weather_data.Humidity}%</div>
                              <div>Wind: {venue.weather_data.WindSpeed} km/h</div>
                              <div>Rain: {venue.weather_data.PrecipitationProbability}%</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="md:w-1/3 space-y-4">
                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <h3 className="font-semibold text-lg mb-4">Daily Traffic Pattern</h3>
                        <div className="h-[200px]">
                          <Line
                            data={{
                              labels: generateBostonTrafficData(venue.name).hours,
                              datasets: [{
                                label: "Visitors",
                                data: generateBostonTrafficData(venue.name).data,
                                borderColor: "rgb(99, 102, 241)",
                                backgroundColor: "rgba(99, 102, 241, 0.1)",
                                tension: 0.4,
                                fill: true,
                              }],
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                legend: { display: false },
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  min: 0,
                                  max: 100,
                                },
                              },
                            }}
                          />
                        </div>
                      </div>

                      {venue.weather_data && (
                        <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <h3 className="font-semibold text-lg mb-4">Weather Forecast</h3>
                          <div className="h-[200px]">
                            <Line
                              data={{
                                labels: generateWeatherData(venue.weather_data)?.hours,
                                datasets: [
                                  {
                                    label: "Temperature (°C)",
                                    data: generateWeatherData(venue.weather_data)?.temperatureData,
                                    borderColor: "rgb(239, 68, 68)",
                                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                                    yAxisID: "y1",
                                  },
                                  {
                                    label: "Humidity (%)",
                                    data: generateWeatherData(venue.weather_data)?.humidityData,
                                    borderColor: "rgb(59, 130, 246)",
                                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                                    yAxisID: "y2",
                                  },
                                ],
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                  y1: {
                                    type: "linear",
                                    position: "left",
                                  },
                                  y2: {
                                    type: "linear",
                                    position: "right",
                                  },
                                },
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="md:w-1/3 space-y-4">
                      {(() => {
                        const insights = generateVenueInsights(venue.name);
                        return (
                          <>
                            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                              <h4 className="text-lg font-semibold mb-4">Traffic Analysis</h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="p-3 bg-white dark:bg-gray-800 rounded-lg text-center">
                                  <p className="text-sm text-gray-600 dark:text-gray-400">Avg Traffic</p>
                                  <p className="text-xl font-bold text-indigo-600">{insights.avgTraffic}</p>
                                </div>
                                <div className="p-3 bg-white dark:bg-gray-800 rounded-lg text-center">
                                  <p className="text-sm text-gray-600 dark:text-gray-400">Peak Capacity</p>
                                  <p className="text-xl font-bold text-indigo-600">{insights.maxTraffic}</p>
                                </div>
                              </div>
                            </div>

                            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                              <h5 className="font-semibold mb-3">Resource Optimization</h5>
                              <div className="space-y-2">
                                {Object.entries(insights.resourceSavings).map(([key, value]) => (
                                  <div key={key} className="flex justify-between items-center p-2 bg-white dark:bg-gray-800 rounded">
                                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{key}</span>
                                    <span className="font-medium text-green-600">
                                      {value} {key === "energy" ? "kWh" : key === "staff" ? "hrs" : key === "water" ? "gal" : "kg"}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
