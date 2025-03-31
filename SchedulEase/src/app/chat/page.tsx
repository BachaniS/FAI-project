"use client";

import { useState, useEffect } from "react";
import { Send } from "lucide-react";
import axios from "axios";
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";

interface TrafficTimes {
  travel_time_text: string;
  travel_time_seconds: number;
}

interface LocationTraffic {
  times: {
    [hour: string]: TrafficTimes;
  };
}

interface TrafficData {
  traffic_data: {
    [location: string]: LocationTraffic;
  };
  average_times: {
    [location: string]: {
      average_commute_time: number;
    };
  };
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  trafficData?: TrafficData;
}

interface Venue {
  name: string;
  address: string;
  capacity: string;
  features: string[];
  source: string;
  weather?: {
    temperature?: string;
    conditions?: string;
  };
  safety?: {
    crimeRate?: string;
    emergencyServices?: string[];
  };
  accessibility?: {
    wheelchair?: boolean;
    parking?: string;
    publicTransport?: string[];
  };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(crypto.randomUUID());
  const [venues, setVenues] = useState<Venue[]>([]);
  const { toast } = useToast();
  const router = useRouter();
  const [loadingText, setLoadingText] = useState("Checking traffic...");

  const handleInitialMessage = async () => {
    try {
      const { data } = await axios.post(
        "http://localhost:8000/api/ai_message",
        {
          message: "start",
          conversation_id: conversationId
        }
      );
      
      const aiMessage: Message = {
        role: "assistant",
        content: data.message,
        timestamp: new Date(),
      };
      setMessages([aiMessage]);
    } catch (error) {
      console.error("Failed to start conversation:", error);
    }
  };

  useEffect(() => {
    handleInitialMessage();
  }, []);

  useEffect(() => {
    if (isLoading) {
      const texts = [
        "Checking traffic...",
        "Analyzing accessibility...",
        "Evaluating safety...",
        "Checking weather conditions..."
      ];
      let index = 0;

      const interval = setInterval(() => {
        index = (index + 1) % texts.length;
        setLoadingText(texts[index]);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const { data } = await axios.post(
        "http://localhost:8000/api/ai_message",
        {
          message: input.trim(),
          conversation_id: conversationId
        }
      );

      if (data.type === "venues") {
        setVenues(data.venues);
        router.push('/venue-details?' + new URLSearchParams({
          venues: JSON.stringify(data.venues),
          weather: JSON.stringify(data.weather),
          safety: JSON.stringify(data.safety),
          accessibility: JSON.stringify(data.accessibility)
        }));
      }

      const aiMessage: Message = {
        role: "assistant",
        content: data.message,
        timestamp: new Date(),
        trafficData: data.traffic_data ? {
          traffic_data: data.traffic_data,
          average_times: data.average_times
        } : undefined
      };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (error) {
      console.error("Failed to send message:", error);
      toast({
        description: "Failed to send message. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 p-4 shadow-sm">
        <div className="max-w-3xl mx-auto flex items-center justify-center">
          <h1 className="text-xl font-semibold text-gray-800 dark:text-white">
            Event Planning Assistant
          </h1>
        </div>
      </div>

      {/* Chat container */}
      <div className="flex-1 overflow-hidden">
        <div className="max-w-3xl h-full mx-auto flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <div key={index}>
                <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`
                      max-w-[80%] px-4 py-2 rounded-2xl shadow-sm
                      ${
                        message.role === "user"
                          ? "bg-blue-600 text-white rounded-br-none"
                          : "bg-white dark:bg-gray-800 rounded-bl-none border dark:border-gray-700"
                      }
                    `}
                  >
                    <div className={`text-sm ${
                      message.role === "user" ? "text-white" : "text-gray-800 dark:text-gray-200"
                    }`}>
                      {message.content}
                    </div>
                  </div>
                </div>
                
                {message.trafficData && (
                  <div className="mt-4 space-y-4">
                    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                      <h3 className="font-semibold text-lg mb-2">Traffic Information</h3>
                      
                      {Object.entries(message.trafficData.traffic_data).map(([location, data]) => (
                        <div key={location} className="mb-4">
                          <h4 className="font-medium text-md">{location}</h4>
                          <div className="grid grid-cols-3 gap-2 mt-2">
                            {Object.entries(data.times).map(([time, timeData]) => (
                              <div key={time} className="text-sm">
                                {time}: {timeData.travel_time_text}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                      
                      <div className="mt-4">
                        <h4 className="font-medium text-md mb-2">Average Commute Times</h4>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(message.trafficData.average_times).map(([location, data]) => (
                            <div key={location} className="text-sm">
                              {location}: {Math.round(data.average_commute_time / 60)} mins
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Venue Recommendations */}
            {venues.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                {venues.map((venue, index) => (
                  <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <h3 className="font-semibold text-lg">{venue.name}</h3>
                    <p className="text-gray-600 dark:text-gray-400">{venue.address}</p>
                    <p className="text-sm">{venue.capacity}</p>
                    <div className="mt-2">
                      <p className="text-sm font-semibold">Features:</p>
                      <ul className="text-sm list-disc list-inside">
                        {venue.features.map((feature, idx) => (
                          <li key={idx}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                    {venue.weather && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold">Weather:</p>
                        <p className="text-sm">{venue.weather.temperature}, {venue.weather.conditions}</p>
                      </div>
                    )}
                    {venue.accessibility && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold">Accessibility:</p>
                        <p className="text-sm">
                          {venue.accessibility.wheelchair ? '✓ Wheelchair Accessible' : '✗ Not Wheelchair Accessible'}
                        </p>
                      </div>
                    )}
                    <a 
                      href={venue.source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 text-sm hover:underline mt-2 inline-block"
                    >
                      More Info
                    </a>
                  </div>
                ))}
              </div>
            )}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 px-4 py-2 rounded-2xl rounded-bl-none border dark:border-gray-700">
                  <span className="text-gray-400 dark:text-gray-500 animate-fade-in-out">
                    {loadingText}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Input form */}
          <div className="p-4 bg-white dark:bg-gray-800 border-t dark:border-gray-700">
            <form
              onSubmit={handleSubmit}
              className="max-w-3xl mx-auto flex items-center gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 p-3 bg-gray-100 dark:bg-gray-900 border dark:border-gray-700 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
}
