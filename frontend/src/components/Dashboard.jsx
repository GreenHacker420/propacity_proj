import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { motion } from 'framer-motion';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042'];

const Dashboard = ({ data }) => {
  const [selectedFilters, setSelectedFilters] = useState(['Praises', 'Problems', 'Suggestions', 'Questions']);
  const [timeRange, setTimeRange] = useState('all');
  
  const FilterButton = ({ label, active, onClick }) => {
    const getButtonStyle = () => {
      switch (label) {
        case 'Praises':
          return active ? 'bg-green-600 text-white' : 'bg-green-100 text-green-800';
        case 'Problems':
          return active ? 'bg-orange-500 text-white' : 'bg-orange-100 text-orange-800';
        case 'Suggestions':
          return active ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800';
        case 'Questions':
          return active ? 'bg-purple-600 text-white' : 'bg-purple-100 text-purple-800';
        default:
          return active ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-800';
      }
    };

    return (
      <button
        onClick={onClick}
        className={`px-4 py-2 rounded-full font-medium transition-all duration-200 ${getButtonStyle()}`}
      >
        <span className="flex items-center">
          {active && <span className="mr-2">✓</span>}
          {label}
        </span>
      </button>
    );
  };

  const SentimentGauge = ({ score }) => {
    const rotation = (score / 10) * 180 - 90; // Convert score to degrees

    return (
      <div className="relative w-48 h-24 mx-auto">
        {/* Gauge background */}
        <div className="absolute w-full h-full rounded-t-full overflow-hidden">
          <div className="absolute w-full h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 opacity-20"></div>
        </div>
        
        {/* Gauge needle */}
        <div 
          className="absolute left-1/2 bottom-0 w-1 h-20 bg-gray-800 origin-bottom transform -translate-x-1/2"
          style={{ transform: `rotate(${rotation}deg)` }}
        ></div>
        
        {/* Score display */}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-2xl font-bold">
          {score.toFixed(2)}
        </div>
        
        {/* Labels */}
        <div className="absolute bottom-[-30px] left-0 text-sm text-gray-600">poor</div>
        <div className="absolute bottom-[-30px] right-0 text-sm text-gray-600">excellent</div>
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-3">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <button className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
        <div className="flex items-center space-x-4">
          <button className="text-purple-600 font-medium hover:text-purple-700">
            + Add widget
          </button>
          <button className="text-purple-600 font-medium hover:text-purple-700">
            ⚙ Edit layout
          </button>
          <button className="text-gray-400 hover:text-gray-600">
            ⋮
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-3">
          {['Praises', 'Problems', 'Suggestions', 'Questions'].map(filter => (
            <FilterButton
              key={filter}
              label={filter}
              active={selectedFilters.includes(filter)}
              onClick={() => {
                if (selectedFilters.includes(filter)) {
                  setSelectedFilters(selectedFilters.filter(f => f !== filter));
                } else {
                  setSelectedFilters([...selectedFilters, filter]);
                }
              }}
            />
          ))}
          <button className="text-purple-600 hover:text-purple-700 font-medium">
            Reset
          </button>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All time</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
          <button className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Sentiment Score */}
        <div className="col-span-4 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">Sentiment score</h2>
            <button className="text-gray-400 hover:text-gray-600">⋮</button>
          </div>
          <SentimentGauge score={3.18} />
        </div>

        {/* NPS Score by City */}
        <div className="col-span-4 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">NPS Score by City</h2>
            <div className="flex space-x-2">
              <button className="text-gray-400 hover:text-gray-600">⤢</button>
              <button className="text-gray-400 hover:text-gray-600">⋮</button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left">
                  <th className="pb-3 text-gray-600">City</th>
                  <th className="pb-3 text-gray-600">Rating Average</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="py-2">Vancouver</td>
                  <td className="py-2">4.82</td>
                </tr>
                <tr>
                  <td className="py-2">Toronto</td>
                  <td className="py-2">1.55</td>
                </tr>
                <tr>
                  <td className="py-2">Seattle</td>
                  <td className="py-2">3.33</td>
                </tr>
                <tr>
                  <td className="py-2">San Francisco</td>
                  <td className="py-2">3.21</td>
                </tr>
              </tbody>
            </table>
            <button className="text-purple-600 hover:text-purple-700 text-sm mt-4">
              Expand to view more
            </button>
          </div>
        </div>

        {/* Top Comments */}
        <div className="col-span-4 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">Top comments</h2>
            <div className="flex space-x-2">
              <button className="text-gray-400 hover:text-gray-600">⤢</button>
              <button className="text-gray-400 hover:text-gray-600">⋮</button>
            </div>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-5 gap-2">
              <div></div>
              <div className="text-sm text-gray-600">Good</div>
              <div className="text-sm text-gray-600">Amazing</div>
              <div className="text-sm text-gray-600">Shocking</div>
              <div className="text-sm text-gray-600">Worst</div>
            </div>
            <div className="grid grid-cols-5 gap-2">
              <div className="text-sm text-gray-600">App</div>
              <div className="bg-purple-700 text-white text-center py-1">92</div>
              <div className="bg-purple-600 text-white text-center py-1">83</div>
              <div className="bg-purple-400 text-white text-center py-1">44</div>
              <div className="bg-purple-300 text-white text-center py-1">36</div>
            </div>
            <div className="grid grid-cols-5 gap-2">
              <div className="text-sm text-gray-600">Customer Service</div>
              <div className="bg-purple-300 text-white text-center py-1">11</div>
              <div className="bg-purple-400 text-white text-center py-1">16</div>
              <div className="bg-purple-700 text-white text-center py-1">68</div>
              <div className="bg-purple-600 text-white text-center py-1">56</div>
            </div>
          </div>
        </div>

        {/* Volume Chart */}
        <div className="col-span-6 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">Volume</h2>
            <div className="flex space-x-2">
              <button className="text-gray-400 hover:text-gray-600">⤢</button>
              <button className="text-gray-400 hover:text-gray-600">⋮</button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Jan', value: 1000 },
              { name: 'Feb', value: 900 },
              { name: 'Mar', value: 880 },
              { name: 'Apr', value: 850 },
              { name: 'May', value: 820 }
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#ffa726" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Topics */}
        <div className="col-span-6 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">Topics</h2>
            <div className="flex space-x-2">
              <button className="text-gray-400 hover:text-gray-600">⤢</button>
              <button className="text-gray-400 hover:text-gray-600">⋮</button>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center">
              <div className="w-24 text-sm text-gray-600">app</div>
              <div className="flex-1 h-6 bg-gradient-to-r from-purple-900 via-green-600 to-orange-400 rounded"></div>
            </div>
            <div className="flex items-center">
              <div className="w-24 text-sm text-gray-600">customer service</div>
              <div className="flex-1 h-6 bg-gradient-to-r from-green-600 to-orange-400 rounded" style={{ width: '60%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 